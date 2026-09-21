"""Exact b_n* solver: Dinkelbach parametric search over integer-scaled slacks.

Hot paths use a compact CSR graph (flat C arrays) with SLF-ordered
queue-based Bellman-Ford; every extracted witness is re-verified by
recomputation before use (fail-closed). The sealed optimum gets U^Z,
transient/cyclic zero-slack witnesses (Kosaraju SCCs on the zero-reduced
subgraph), and a two-sided certificate. LP/HiGHS discovery is proposal-only
and never seals (threat T6). Discovery always climbs from b=1/1: an LP float
is agreement evidence only, never a search start (a float above the optimum
would break the climbing invariant).
"""

import argparse
import hashlib
import json
import math
import os
import sys
from array import array
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.reference import enumerate as enum  # noqa: E402
from python.reference import pair_graph as pg  # noqa: E402

KEEP, DELETE = pg.KEEP, pg.DELETE
MAX_ITER = 10000


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def reduce_fraction(p, q):
    """Reduced (p, q) with p, q > 0."""
    g = math.gcd(p, q)
    return p // g, q // g


class Graph(object):
    """Reachable pair graph with on-demand edges (used for LP + mapping)."""

    def __init__(self, tables, reach):
        self.tables = tables
        self.reach = reach
        self.n = reach.n
        self.size = len(reach.pair_ids)
        self.pids = reach.pair_ids
        self.idx = reach.index_of

    def out_edges(self, i, p, q):
        """Yield (j, mode, key, a, y, L) for reachable_index i."""
        pid = self.pids[i]
        for mode in (KEEP, DELETE):
            for key in range(1, self.n + 1):
                tgt, a, y = pg.pair_successor(self.tables, pid, mode, key)
                yield self.idx[tgt], mode, key, a, y, p * a - q * y


class Csr(object):
    """Compact CSR pair graph: flat arrays, L computed on the fly as p*a-q*y.

    diag[i] is 1 iff state i is a diagonal state. reach/tables kept for
    witness verification (edge legality recomputed from tables, never trusted
    from arrays alone at seal time).
    """

    def __init__(self):
        self.size = 0
        self.nkeys = 0
        self.tree_count = 0
        self.pids = []
        self.diag = bytearray()
        self.off = array("i", [0])
        self.tgt = array("i")
        self.am = array("b")
        self.ym = array("b")
        self.mom = array("b")
        self.keym = array("b")
        self.roff = array("i", [0])
        self.rsrc = array("i")
        self.rfwd = array("i")
        self.reach = None
        self.tables = None


def build_csr(tables, reach):
    """Materialize the full reachable edge set once per size. Returns Csr.

    Bulk-build discipline: gc disabled during mass int allocation, C-level
    array appends, local bindings. (An earlier version using plain Python
    lists thrashed the cyclic GC at n=7 scale: >3 GB and no progress.)
    """
    import gc
    # console.log equivalent [WP2-SOL-00]: CSR materialization begin.
    console_log("WP2-SOL-00", "CSR build R=%d" % len(reach.pair_ids))
    csr = Csr()
    csr.tables = tables
    csr.reach = reach
    csr.nkeys = reach.n
    csr.tree_count = reach.tree_count
    csr.pids = list(reach.pair_ids)
    csr.size = len(csr.pids)
    csr.diag = bytearray(csr.size)
    tc = reach.tree_count
    for i, pid in enumerate(csr.pids):
        if divmod(pid, tc)[0] == divmod(pid, tc)[1]:
            csr.diag[i] = 1
    succ = pg.pair_successor
    idx = reach.index_of
    nk = reach.n
    gc.disable()
    try:
        tgt = array("i")
        am = array("b")
        ym = array("b")
        mom = array("b")
        keym = array("b")
        off = array("i", [0])
        append_t, append_a, append_y = tgt.append, am.append, ym.append
        append_m, append_k = mom.append, keym.append
        for pid in csr.pids:
            for mode in (0, 1):
                for key in range(1, nk + 1):
                    t, a, y = succ(tables, pid, mode, key)
                    append_t(idx[t])
                    append_a(a)
                    append_y(y)
                    append_m(mode)
                    append_k(key)
            off.append(len(tgt))
        nstates = csr.size
        nedges = len(tgt)
        rcount = [0] * nstates
        for v in tgt:
            rcount[v] += 1
        roff = array("i", [0])
        acc = 0
        for c in rcount:
            acc += c
            roff.append(acc)
        rsrc = array("i", [0]) * nedges
        rfwd = array("i", [0]) * nedges
        fill = list(roff[:-1])
        for u in range(nstates):
            ou, ou1 = off[u], off[u + 1]
            for e in range(ou, ou1):
                v = tgt[e]
                pos = fill[v]
                rsrc[pos] = u
                rfwd[pos] = e
                fill[v] = pos + 1
    finally:
        gc.enable()
    csr.off = off
    csr.tgt = tgt
    csr.am = am
    csr.ym = ym
    csr.mom = mom
    csr.keym = keym
    csr.roff = roff
    csr.rsrc = rsrc
    csr.rfwd = rfwd
    # console.log equivalent [WP2-SOL-00]: CSR ready (second emission).
    console_log("WP2-SOL-00", "CSR ready edges=%d" % len(tgt))
    return csr


def check_validity(csr, p, q, max_visits=None):
    """Exact validity at b=p/q via SLF-ordered queue Bellman-Ford.

    Returns (verdict, witness, dist) with verdict in VALID/INVALID/UNDECIDED.
    max_visits bounds edge relaxations for far-below-optimum probes: on
    exhaustion the function returns INVALID only with a recomputation-verified
    negative witness, else UNDECIDED (caller reruns unbounded). Unbounded runs
    never return UNDECIDED: drained queue + no negative dist ⟺ valid.
    """
    s = csr.size
    off, tgt, am, ym = csr.off, csr.tgt, csr.am, csr.ym
    dist = [None] * s
    par = [None] * s
    inq = bytearray(s)
    cnt = [0] * s
    dq = deque()
    for i in range(s):
        if csr.diag[i]:
            dist[i] = 0
            dq.append(i)
            inq[i] = 1
    overflow = None
    visits = 0
    append = dq.append
    appendleft = dq.appendleft
    budgeted = max_visits is not None
    while dq:
        u = dq.popleft()
        inq[u] = 0
        du = dist[u]
        ou, ou1 = off[u], off[u + 1]
        for e in range(ou, ou1):
            visits += 1
            v = tgt[e]
            nd = du + p * am[e] - q * ym[e]
            dv = dist[v]
            if dv is None or nd < dv:
                dist[v] = nd
                par[v] = (u, e)
                cnt[v] += 1
                if cnt[v] > s:
                    overflow = v
                    dq.clear()
                    break
                if not inq[v]:
                    front = dq[0] if dq else None
                    if front is not None and nd < dist[front]:
                        appendleft(v)
                    else:
                        append(v)
                    inq[v] = 1
            if budgeted and visits >= max_visits:
                dq.clear()
                break
    if overflow is not None:
        try:
            return "INVALID", extract_cycle(csr, par, overflow, p, q), dist
        except AssertionError:
            if budgeted:
                return "UNDECIDED", None, dist
            raise
    for v in range(s):
        if dist[v] is not None and dist[v] < 0:
            try:
                return "INVALID", extract_negative_path(csr, par, v, p, q), dist
            except AssertionError:
                if budgeted:
                    break
                raise
    for u in range(s):
        if dist[u] is None:
            continue
        du = dist[u]
        for e in range(off[u], off[u + 1]):
            v = tgt[e]
            dv = dist[v]
            if dv is None or du + p * am[e] - q * ym[e] < dv:
                try:
                    return "INVALID", extract_cycle(csr, par, u, p, q), dist
                except AssertionError:
                    if budgeted:
                        return "UNDECIDED", None, dist
                    raise
    if budgeted:
        return "UNDECIDED", None, dist
    return "VALID", None, dist


def edge_tuple(csr, u_idx, e_idx, v_idx):
    """Edge as (source_pid, mode, key, target_pid)."""
    return (csr.pids[u_idx], int(csr.mom[e_idx]), int(csr.keym[e_idx]), csr.pids[v_idx])


def edge_sums(csr, edges):
    """Recompute (sum_a, sum_y) for an edge list. Fail-closed."""
    sa = sy = 0
    for (s_pid, mode, key, t_pid) in edges:
        tgt, a, y = pg.pair_successor(csr.tables, s_pid, mode, key)
        if tgt != t_pid:
            raise AssertionError("witness edge not legal")
        sa += a
        sy += y
    return sa, sy


def extract_negative_path(csr, par, v, p, q):
    """Walk tight parents to a diagonal; verify negative total by recompute."""
    seen = set()
    chain = []
    cur = v
    steps = 0
    while steps <= csr.size:
        if csr.diag[cur]:
            break
        if cur in seen:
            return extract_cycle(csr, par, cur, p, q)
        seen.add(cur)
        pe = par[cur]
        if pe is None:
            raise AssertionError("dead parent chain")
        u, e = pe
        chain.append(edge_tuple(csr, u, e, cur))
        cur = u
        steps += 1
    chain.reverse()
    sa, sy = edge_sums(csr, chain)
    if not (sa > 0 and p * sa - q * sy < 0):
        raise AssertionError("transient extraction failed verification")
    a0, b0 = divmod(chain[0][0], csr.tree_count)
    if a0 != b0:
        raise AssertionError("transient witness not diagonal-rooted")
    return {"kind": "transient", "edges": chain, "sum_a": sa, "sum_y": sy}


def extract_cycle(csr, par, v, p, q):
    """Walk size steps to a negative cycle; verify by recompute."""
    cur = v
    for _ in range(csr.size):
        pe = par[cur]
        if pe is None:
            raise AssertionError("dead parent chain in cycle extraction")
        cur = pe[0]
    start = cur
    cycle = []
    while True:
        pe = par[cur]
        if pe is None:
            raise AssertionError("open cycle")
        u, e = pe
        cycle.append(edge_tuple(csr, u, e, cur))
        cur = u
        if cur == start:
            break
        if len(cycle) > csr.size + 1:
            raise AssertionError("cycle walk did not close")
    cycle.reverse()
    sa, sy = edge_sums(csr, cycle)
    if not (sa > 0 and p * sa - q * sy < 0):
        raise AssertionError("cycle extraction failed verification")
    prefix = diagonal_prefix(csr, csr.pids[start])
    return {"kind": "cyclic", "edges": cycle, "sum_a": sa, "sum_y": sy,
            "prefix": prefix, "cycle_start": csr.pids[start]}


def diagonal_prefix(csr, pid):
    """BFS-parent chain from a diagonal to pid (reachability witnesses)."""
    parents = csr.reach.parents
    if pid not in parents:
        a_id, b_id = divmod(pid, csr.tree_count)
        if a_id == b_id:
            return []
        raise AssertionError("no reachability parent")
    chain = []
    cur = pid
    while cur in parents:
        par, mode, key = parents[cur]
        chain.append((par, mode, key, cur))
        cur = par
    chain.reverse()
    edge_sums(csr, chain)
    return chain


def dinkelbach(csr):
    """Exact parametric search from b=1/1. Returns (p, q, trail).

    Far-below-optimum probes run under a relaxation budget (sound climbing
    steps only: INVALID is returned solely with recomputation-verified
    witnesses); UNDECIDED probes rerun unbounded. Termination: strictly
    increasing reduced rationals over a finite ratio set.
    """
    # console.log equivalent [WP2-SOL-01]: discovery begin.
    console_log("WP2-SOL-01", "parametric discovery begin R=%d" % csr.size)
    budget = 4 * len(csr.tgt)
    p, q = 1, 1
    trail = []
    for _ in range(MAX_ITER):
        verdict, wit, _ = check_validity(csr, p, q, max_visits=budget)
        if verdict == "UNDECIDED":
            verdict, wit, _ = check_validity(csr, p, q)
            if verdict == "UNDECIDED":
                raise AssertionError("unbounded probe undecided")
        if verdict == "VALID":
            trail.append({"b": [p, q], "valid": True, "witness": None})
            break
        trail.append({"b": [p, q], "valid": False,
                      "witness": {"kind": wit["kind"], "sum_a": wit["sum_a"],
                                  "sum_y": wit["sum_y"]}})
        p, q = reduce_fraction(wit["sum_y"], wit["sum_a"])
    else:
        raise AssertionError("parametric search exhausted iterations")
    # console.log equivalent [WP2-SOL-02]: discovery sealed exactly.
    console_log("WP2-SOL-02", "discovered b=%d/%d probes=%d" % (p, q, len(trail)))
    return p, q, trail


def lp_proposal(graph):
    """Discovery-only sparse LP via HiGHS (float, never authoritative).

    min b s.t. phi >= 0, phi = 0 on diagonals,
    y(e) + phi[t] - phi[s] <= b * a(e). Returns float or None.
    """
    # console.log equivalent [WP2-SOL-03]: LP proposal begin.
    console_log("WP2-SOL-03", "HiGHS LP proposal begin")
    try:
        from scipy.optimize import linprog
        from scipy.sparse import coo_matrix
    except ImportError:
        console_log("WP2-SOL-03", "LP backend unavailable")
        return None
    n = graph.size
    col_b = n
    rows, cols, data, rhs = [], [], [], []
    r = 0
    for i, pid in enumerate(graph.pids):
        a_id, b_id = divmod(pid, graph.reach.tree_count)
        if a_id == b_id:
            rows.append(r)
            cols.append(i)
            data.append(1.0)
            rhs.append(0.0)
            r += 1
            rows.append(r)
            cols.append(i)
            data.append(-1.0)
            rhs.append(0.0)
            r += 1
    for i in range(n):
        s_pid = graph.pids[i]
        for mode in (KEEP, DELETE):
            for key in range(1, graph.n + 1):
                tgt, a, y = pg.pair_successor(graph.tables, s_pid, mode, key)
                j = graph.idx[tgt]
                rows += [r, r, r]
                cols += [j, i, col_b]
                data += [1.0, -1.0, -float(a)]
                rhs.append(-float(y))
                r += 1
    import numpy as np
    mat = coo_matrix((np.array(data), (np.array(rows), np.array(cols))),
                     shape=(r, n + 1)).tocsr()
    c = np.zeros(n + 1)
    c[col_b] = 1.0
    bounds = [(0.0, None)] * n + [(1.0, float(graph.n))]
    res = linprog(c, A_ub=mat, b_ub=np.array(rhs),
                  bounds=bounds, method="highs")
    if res.status != 0:
        console_log("WP2-SOL-03", "LP did not solve status=%d" % res.status)
        return None
    console_log("WP2-SOL-03", "LP proposal float=%r" % (res.x[col_b],))
    return float(res.x[col_b])


def tarjan_zero_cycles(csr, dist, p, q):
    """SCCs of the zero-reduced subgraph + one canonical simple cycle each.

    Iterative Kosaraju (two passes) over CSR + reverse CSR: exact and simple
    to verify. A zero self-loop also counts as a critical cycle.
    """
    s = csr.size
    off, tgt, am, ym = csr.off, csr.tgt, csr.am, csr.ym
    roff, rsrc, rfwd = csr.roff, csr.rsrc, csr.rfwd

    def is_zero(u, e):
        v = tgt[e]
        return p * am[e] - q * ym[e] == dist[v] - dist[u]

    visited = bytearray(s)
    order = []
    for root in range(s):
        if visited[root]:
            continue
        stack = [(root, off[root])]
        while stack:
            v, ei = stack.pop()
            if ei == off[v]:
                if visited[v]:
                    continue
                visited[v] = 1
            if ei < off[v + 1]:
                stack.append((v, ei + 1))
                e = ei
                if is_zero(v, e):
                    w = tgt[e]
                    if not visited[w]:
                        stack.append((w, off[w]))
            else:
                order.append(v)
    comp = [-1] * s
    sccs = []
    for root in reversed(order):
        if comp[root] != -1:
            continue
        members = []
        stack = [root]
        comp[root] = len(sccs)
        while stack:
            v = stack.pop()
            members.append(v)
            for re_ in range(roff[v], roff[v + 1]):
                w = rsrc[re_]
                if comp[w] == -1 and is_zero(w, rfwd[re_]):
                    comp[w] = len(sccs)
                    stack.append(w)
        sccs.append(members)
    cycles = []
    for members in sccs:
        inset = set(members)
        if len(members) == 1:
            v = members[0]
            loops = []
            for e in range(off[v], off[v + 1]):
                if tgt[e] == v and is_zero(v, e):
                    loops.append(e)
            if not loops:
                continue
            e = min(loops, key=lambda e: (int(csr.mom[e]), int(csr.keym[e])))
            pid = csr.pids[v]
            cyc = [(pid, int(csr.mom[e]), int(csr.keym[e]), pid)]
            sa, sy = edge_sums(csr, cyc)
            assert p * sa - q * sy == 0
            cycles.append({"scc_size": 1, "edges": cyc, "sum_a": sa, "sum_y": sy})
            continue
        start = min(members)
        prev = {start: None}
        queue = deque([start])
        found = None
        while queue and found is None:
            v = queue.popleft()
            for e in range(off[v], off[v + 1]):
                if not is_zero(v, e):
                    continue
                j = tgt[e]
                if j not in inset:
                    continue
                if j == start:
                    found = (v, e)
                    queue.clear()
                    break
                if j in prev:
                    continue
                prev[j] = (v, e)
                queue.append(j)
        if found is None:
            raise AssertionError("no zero return path inside SCC")
        v, e = found
        cyc = [edge_tuple(csr, v, e, start)]
        cur = v
        while cur != start:
            pv, pe = prev[cur]
            cyc.append(edge_tuple(csr, pv, pe, cur))
            cur = pv
        cyc.reverse()
        sa, sy = edge_sums(csr, cyc)
        assert p * sa - q * sy == 0
        cycles.append({"scc_size": len(members), "edges": cyc,
                       "sum_a": sa, "sum_y": sy})
    return cycles


def shortest_future(csr, p, q):
    """Exact V^Z via reverse propagation (no logging; callers log).

    D = min over paths-from-s (empty path allowed, so D <= 0); V = -D.
    Converges: at valid b no negative-slack cycle exists anywhere in R_n
    (all states are diagonal-reachable, so such a cycle would break
    validity). Returns (V, argmax) with argmax the last improving edge.
    """
    s = csr.size
    off, tgt, am, ym = csr.off, csr.tgt, csr.am, csr.ym
    roff, rsrc, rfwd = csr.roff, csr.rsrc, csr.rfwd
    dist = [0] * s
    argmax = [None] * s
    inq = bytearray(s)
    dq = deque()
    for i in range(s):
        dq.append(i)
        inq[i] = 1
    cap = 20 * len(tgt)
    visits = 0
    while dq:
        t = dq.popleft()
        inq[t] = 0
        dt = dist[t]
        for re in range(roff[t], roff[t + 1]):
            visits += 1
            if visits > cap:
                raise AssertionError("future propagation exceeded visit cap")
            u = rsrc[re]
            e = rfwd[re]
            nd = p * int(am[e]) - q * int(ym[e]) + dt
            if nd < dist[u]:
                dist[u] = nd
                argmax[u] = (t, e)
                if not inq[u]:
                    dq.append(u)
                    inq[u] = 1
    return [-d for d in dist], argmax


def tight_pred_lists(csr, U, p, q):
    """All tight incoming edges per state (U[t]+L(e) == U[s]), det. order."""
    lists = [[] for _ in range(csr.size)]
    for s in range(csr.size):
        for re in range(csr.roff[s], csr.roff[s + 1]):
            t = csr.rsrc[re]
            e = csr.rfwd[re]
            if U[t] + p * int(csr.am[e]) - q * int(csr.ym[e]) == U[s]:
                lists[s].append((t, e))
    return lists


def vtight_out_lists(csr, V, p, q):
    """All V-tight outgoing edges per state (-L(e)+V[t] == V[s])."""
    lists = [[] for _ in range(csr.size)]
    for i in range(csr.size):
        for e in range(csr.off[i], csr.off[i + 1]):
            j = csr.tgt[e]
            if -(p * int(csr.am[e]) - q * int(csr.ym[e])) + V[j] == V[i]:
                lists[i].append((j, e))
    return lists


def dfs_prefix(csr, tight_lists, target):
    """U-optimal diagonal-rooted path to target (tight edges, DFS).

    Exists: U[target] is attained by a simple diagonal path whose edges are
    all tight (telescoping: per-edge U[b]<=U[a]+L with equality forced by
    the optimal total); backward DFS completeness finds a route. Returns
    edge list (possibly empty when target is diagonal) or None.
    """
    tc = csr.tree_count
    a_id, b_id = divmod(csr.pids[target], tc)
    if a_id == b_id:
        return []
    succ = {}
    stack = [target]
    while stack:
        v = stack.pop()
        for (t, e) in tight_lists[v]:
            if t not in succ:
                succ[t] = (v, e)
                stack.append(t)
    for d, (nxt, e) in succ.items():
        da, db = divmod(csr.pids[d], tc)
        if da != db:
            continue
        chain = []
        cur = d
        while cur != target:
            nxt, e = succ[cur]
            chain.append(edge_tuple(csr, cur, e, nxt))
            cur = nxt
        edge_sums(csr, chain)
        return chain
    return None


def dfs_suffix(csr, vtight_lists, V, source):
    """V-optimal path from source to a V==0 state (V-tight edges, DFS).

    Exists: V[source] is attained by a simple path (no positive-regret
    cycle exists at valid b) whose edges are all V-tight (telescoping);
    DFS completeness finds a route. Total is exactly -V[source].
    Returns edge list (possibly empty) or None.
    """
    stack = [source]
    pred = {source: None}
    while stack:
        v = stack.pop()
        if V[v] == 0:
            chain = []
            cur = v
            while cur != source:
                pv, pe = pred[cur]
                chain.append(edge_tuple(csr, pv, pe, cur))
                cur = pv
            chain.reverse()
            sa, sy = edge_sums(csr, chain)
            return chain
        for (j, e) in vtight_lists[v]:
            if j not in pred:
                pred[j] = (v, e)
                stack.append(j)
    return None if V[source] != 0 else []


def find_transient(csr, dist, V, p, q):
    """Nonempty diagonal-rooted zero-slack path, or None (complete rule).

    Complete: an edge lies on some nonempty zero diagonal-rooted path iff
    U[t]+L(e)-V[s] == 0 (both directions by telescoping + sandwich, using
    attained U/V optima: no negative-slack cycle exists at valid b). For
    the first such edge in deterministic order, the path is the U-optimal
    prefix to t, e itself, and the V-optimal suffix from s; total is
    exactly U[t]+L(e)-V[s] == 0. Returns None iff no zero path exists.
    """
    U = dist
    tight = tight_pred_lists(csr, U, p, q)
    vtight = vtight_out_lists(csr, V, p, q)
    for i in range(csr.size):
        for e in range(csr.off[i], csr.off[i + 1]):
            j = csr.tgt[e]
            if U[i] + p * int(csr.am[e]) - q * int(csr.ym[e]) - V[j] != 0:
                continue
            pre = dfs_prefix(csr, tight, i)
            if pre is None:
                continue
            suf = dfs_suffix(csr, vtight, V, j)
            if suf is None:
                continue
            chain = pre + [edge_tuple(csr, i, e, j)] + suf
            if not chain:
                continue
            sa, sy = edge_sums(csr, chain)
            a0, b0 = divmod(chain[0][0], csr.tree_count)
            if a0 == b0 and sa > 0 and p * sa - q * sy == 0:
                return chain
    return None


def _dump_zst(path, obj):
    import zstandard as zstd
    blob = (json.dumps(obj, sort_keys=True) + "\n").encode("utf-8")
    logical = hashlib.sha256(blob).hexdigest()
    with open(path, "wb") as f:
        f.write(zstd.ZstdCompressor(level=19).compress(blob))
    return logical


def discover(n, tables, reach, cand_dir, use_lp=True):
    """Phase-05 discovery: exact parametric trail + LP agreement note.

    use_lp=False skips the proposal-only HiGHS run (documented per size;
    the exact candidate is unaffected — LP output can never seal).
    """
    os.makedirs(cand_dir, exist_ok=True)
    csr = build_csr(tables, reach)
    p, q, trail = dinkelbach(csr)
    lp_float = lp_proposal(Graph(tables, reach)) if use_lp else None
    if lp_float is not None and abs(lp_float - p / q) >= 1e-6:
        raise AssertionError("LP/exact discovery disagreement")
    agreement = None if lp_float is None else "AGREE"
    backend = "parametric-exact" if use_lp else "parametric-exact(lp-skipped-size-policy)"
    obj = {"authoritative": False, "backend_notes": backend,
           "discovery_float": lp_float, "lp_agreement": agreement, "n": n,
           "sealed_candidate": {"p": str(p), "q": str(q), "reduced": True},
           "trail": [{"b": {"p": str(b[0]), "q": str(b[1])}, "valid": t["valid"],
                      "witness": t["witness"]} for t in trail for b in [t["b"]]]}
    with open(os.path.join(cand_dir, "candidate_set.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True, indent=2)
        f.write("\n")
    # console.log equivalent [WP2-SOL-04]: discovery written.
    console_log("WP2-SOL-04", "n=%d candidate %d/%d trail=%d" % (n, p, q, len(trail)))
    return p, q


def certify(n, tables, reach, p, q, cert_dir):
    """Phase-06 certification: re-prove validity, U^Z, witnesses, seal."""
    # console.log equivalent [WP2-SOL-05]: certification begin.
    console_log("WP2-SOL-05", "certifying n=%d b=%d/%d" % (n, p, q))
    os.makedirs(cert_dir, exist_ok=True)
    csr = build_csr(tables, reach)
    verdict, wit, dist = check_validity(csr, p, q)
    if verdict != "VALID":
        raise AssertionError("candidate failed independent re-proof")
    if any(d is None or d < 0 for d in dist):
        raise AssertionError("U table violates nonnegativity")
    for i, pid in enumerate(csr.pids):
        a_id, b_id = divmod(pid, reach.tree_count)
        if a_id == b_id and dist[i] != 0:
            raise AssertionError("diagonal potential nonzero")
    for i in range(csr.size):
        for e in range(csr.off[i], csr.off[i + 1]):
            j = csr.tgt[e]
            if dist[j] - dist[i] > p * int(csr.am[e]) - q * int(csr.ym[e]):
                raise AssertionError("upper edge violation")
    pot = [{"P": str(dist[i]), "pair_id": csr.pids[i]} for i in range(csr.size)]
    h_pot = _dump_zst(os.path.join(cert_dir, "potential_upper.json.zst"), pot)
    Vw, _ = shortest_future(csr, p, q)
    tpath = find_transient(csr, dist, Vw, p, q)
    cycles = tarjan_zero_cycles(csr, dist, p, q)
    lowers = []
    if tpath is not None:
        sa, sy = edge_sums(csr, tpath)
        obj = {"initial_tree_id": tpath[0][0] // reach.tree_count,
               "edges": [{"key": e[2], "mode": "KEEP" if e[1] == KEEP else "DELETE",
                          "source": e[0], "target": e[3]} for e in tpath],
               "sum_a": sa, "sum_scaled_slack": 0, "sum_y": sy}
        with open(os.path.join(cert_dir, "witness_path.json"), "w", encoding="utf-8") as f:
            json.dump(obj, f, sort_keys=True, indent=2)
            f.write("\n")
        lowers.append({"file": "witness_path.json", "type": "zero_slack_path"})
    if cycles:
        c0 = cycles[0]
        obj = {"cycle": [{"key": e[2], "mode": "KEEP" if e[1] == KEEP else "DELETE",
                          "source": e[0], "target": e[3]} for e in c0["edges"]],
               "prefix": [{"key": e[2], "mode": "KEEP" if e[1] == KEEP else "DELETE",
                           "source": e[0], "target": e[3]} for e in diagonal_prefix(csr, c0["edges"][0][0])],
               "sum_a_cycle": c0["sum_a"], "sum_scaled_slack_cycle": 0,
               "sum_y_cycle": c0["sum_y"]}
        with open(os.path.join(cert_dir, "witness_cycle.json"), "w", encoding="utf-8") as f:
            json.dump(obj, f, sort_keys=True, indent=2)
            f.write("\n")
        lowers.append({"file": "witness_cycle.json", "type": "zero_slack_cycle"})
    if not lowers:
        raise AssertionError("no lower witness")
    has_t = tpath is not None
    has_c = bool(cycles)
    criticality = ("EXACT_BN_MIXED" if has_t and has_c
                   else "EXACT_BN_TRANSIENT" if has_t else "EXACT_BN_CYCLIC")
    g = math.gcd(p, q)
    cert = {"b": {"p": str(p), "q": str(q)}, "criticality": criticality,
            "independent_verifier": "PENDING",
            "lower_certificates": lowers, "n": n,
            "reachable_pair_count": csr.size,
            "reduced": g == 1,
            "sanity_lower_ok": p >= q, "sanity_upper_ok": p <= n * q,
            "upper_certificate": {"file": "potential_upper.json.zst",
                                  "sha256": h_pot, "type": "feasible_integer_potential"}}
    with open(os.path.join(cert_dir, "bn_certificate.json"), "w", encoding="utf-8") as f:
        json.dump(cert, f, sort_keys=True, indent=2)
        f.write("\n")
    with open(os.path.join(cert_dir, "canonical_cycles.json"), "w", encoding="utf-8") as f:
        json.dump([{"edges": [{"key": e[2], "mode": "KEEP" if e[1] == KEEP else "DELETE",
                               "source": e[0], "target": e[3]} for e in c["edges"]],
                    "scc_size": c["scc_size"], "sum_a": c["sum_a"], "sum_y": c["sum_y"]}
                   for c in cycles], f, sort_keys=True, indent=2)
        f.write("\n")
    # console.log equivalent [WP2-SOL-06]: certificate sealed (pending audit).
    console_log("WP2-SOL-06", "n=%d sealed %s witnesses=%d" % (n, criticality, len(lowers)))
    return criticality


def main(argv=None):
    """CLI: --discover or --certify for one n from built artifacts."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--mode", choices=["discover", "certify"], required=True)
    ap.add_argument("--tables", required=True)
    ap.add_argument("--reachability", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--candidate", default=None)
    args = ap.parse_args(argv)
    tables = load_tables(args.tables)
    reach = load_reach(args.reachability, tables.tree_count)
    if args.mode == "discover":
        discover(args.n, tables, reach, args.out)
    else:
        if args.candidate is None:
            raise AssertionError("--candidate is required for certify")
        with open(args.candidate, encoding="utf-8") as f:
            cand = json.load(f)
        p, q = int(cand["sealed_candidate"]["p"]), int(cand["sealed_candidate"]["q"])
        certify(args.n, tables, reach, p, q, args.out)
    return 0


def load_tables(path):
    """Reload single-tree tables from forward/inverse artifacts."""
    import zstandard as zstd
    with open(os.path.join(path, "forward.bin.zst"), "rb") as f:
        fwd = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    n = fwd["n"]
    c = max(r["tree"] for r in fwd["records"]) + 1
    after = [[0] * (n + 1) for _ in range(c)]
    cost = [[0] * (n + 1) for _ in range(c)]
    for r in fwd["records"]:
        after[r["tree"]][r["x"]] = r["after"]
        cost[r["tree"]][r["x"]] = r["cost"]
    shapes = enum.canonical_shapes(n)
    with open(os.path.join(path, "inverse.bin.zst"), "rb") as f:
        inv = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    pred = [None] + [inv["pred"][str(x)] for x in range(1, n + 1)]
    return pg.Tables(n, shapes, after, cost, pred)


def load_reach(path, tree_count):
    """Reload reachability from reachable.json.zst."""
    import zstandard as zstd
    with open(os.path.join(path, "reachable.json.zst"), "rb") as f:
        obj = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    pids = obj["pair_ids"]
    return pg.Reachability(obj["n"], tree_count, pids,
                           {p: i for i, p in enumerate(pids)},
                           {int(k): tuple(v) for k, v in obj["parents"].items()})


if __name__ == "__main__":
    sys.exit(main())
