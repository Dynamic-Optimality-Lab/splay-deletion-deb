"""Critical geometry: zero-slack corridors, SCCs, FORCED_DELTA, B06 diagnostic.

Zero-reduced edges (w.r.t. exact U): r(e) = L(e) - (U[t]-U[s]) >= 0.
FPATH  = edges with U[t]+L(e) == 0 (complete rule: exactly the edges on some
         nonempty zero-slack diagonal-rooted path).
FCYCLE = zero edges inside nontrivial zero-SCCs (self-loop or size>1).
FGAP   = frozen rule: G[s]==0 and G[t]==0 and U[t]-U[s]==L(e).
VBELLMAN/UBELLMAN recorded separately. FORCED_DELTA = FPATH u FCYCLE u FGAP,
each with exact Delta_H_scaled = L(e) and proof provenance.
Below-optimum diagnostic (B06, frozen rule): b- = (p+q)/2q reduced if p>q,
1/2 if p=q=1; exact NEGATIVE_PATH vs NEGATIVE_CYCLE preserved separately.
"""

import hashlib
import json
import math
import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.reference import pair_graph as pg  # noqa: E402
from python.reference import solve_small as sv  # noqa: E402

KEEP, DELETE = pg.KEEP, pg.DELETE


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def mode_name(mode):
    """Frozen mode code to artifact string."""
    return "KEEP" if mode == KEEP else "DELETE"


def mode_of(name):
    """Artifact mode string to frozen mode code."""
    return KEEP if name == "KEEP" else DELETE


def slack(edge_a, edge_y, p, q):
    """Integer-scaled slack of one edge."""
    return p * edge_a - q * edge_y


def build_zero_graph(csr, U, V, p, q):
    """Zero-reduced adjacency (forward + reverse) and edge class sets.

    Returns dict with: fwd (per-state list of (j, e)), radj reverse,
    fpath (set of edge keys), z_edges (all zero-reduced edge keys).
    Edge key = (source_index, mode, key).
    FPATH rule (complete): U[t]+L(e)-V[s] == 0 — exactly the edges lying on
    some nonempty zero-slack diagonal-rooted path (both directions by
    telescoping + sandwich with attained optima).
    """
    # console.log equivalent [WP3-CR-01]: zero-reduced graph begin.
    console_log("WP3-CR-01", "zero graph R=%d" % csr.size)
    fwd = [[] for _ in range(csr.size)]
    radj = [[] for _ in range(csr.size)]
    fpath = set()
    z_edges = set()
    for i in range(csr.size):
        for e in range(csr.off[i], csr.off[i + 1]):
            j = csr.tgt[e]
            w = p * int(csr.am[e]) - q * int(csr.ym[e])
            if w == U[j] - U[i]:
                key = (i, int(csr.mom[e]), int(csr.keym[e]))
                fwd[i].append((j, e))
                radj[j].append(i)
                z_edges.add(key)
                if U[i] + w - V[j] == 0:
                    fpath.add(key)
    # console.log equivalent [WP3-CR-02]: zero graph sealed.
    console_log("WP3-CR-02", "zero edges=%d fpath=%d" % (len(z_edges), len(fpath)))
    return {"fwd": fwd, "radj": radj, "fpath": fpath, "z_edges": z_edges}


def zero_sccs(csr, zero):
    """SCCs of the zero-reduced subgraph (iterative Kosaraju)."""
    s = csr.size
    fwd, radj = zero["fwd"], zero["radj"]
    visited = bytearray(s)
    order = []
    for root in range(s):
        if visited[root]:
            continue
        stack = [(root, 0)]
        while stack:
            v, ci = stack.pop()
            if ci == 0:
                if visited[v]:
                    continue
                visited[v] = 1
            nbrs = fwd[v]
            if ci < len(nbrs):
                stack.append((v, ci + 1))
                w = nbrs[ci][0]
                if not visited[w]:
                    stack.append((w, 0))
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
            for w in radj[v]:
                if comp[w] == -1:
                    comp[w] = len(sccs)
                    stack.append(w)
        sccs.append(members)
    return sccs, comp


def canonical_cycle(csr, zero, members, comp_id, comp, p, q, U):
    """One canonical simple zero cycle inside an SCC (lexicographically first)."""
    inset = set(members)
    if len(members) == 1:
        v = members[0]
        loops = [(e, int(csr.mom[e]), int(csr.keym[e]))
                 for (j, e) in zero["fwd"][v] if j == v]
        if not loops:
            return None
        e = min(loops, key=lambda t: (t[1], t[2]))[0]
        cyc = [(csr.pids[v], int(csr.mom[e]), int(csr.keym[e]), csr.pids[v])]
        sa, sy = sv.edge_sums(csr, cyc)
        assert p * sa - q * sy == 0
        return {"edges": cyc, "sum_a": sa, "sum_y": sy}
    start = min(members)
    prev = {start: None}
    queue = deque([start])
    found = None
    while queue and found is None:
        v = queue.popleft()
        for (j, e) in sorted(zero["fwd"][v], key=lambda t: (int(csr.mom[t[1]]), int(csr.keym[t[1]]))):
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
    cyc = [edge_tuple_of(csr, v, e, start)]
    cur = v
    while cur != start:
        pv, pe = prev[cur]
        cyc.append(edge_tuple_of(csr, pv, pe, cur))
        cur = pv
    cyc.reverse()
    sa, sy = sv.edge_sums(csr, cyc)
    assert p * sa - q * sy == 0
    return {"edges": cyc, "sum_a": sa, "sum_y": sy}


def edge_tuple_of(csr, u, e, v):
    """Edge as (source_pid, mode, key, target_pid)."""
    return (csr.pids[u], int(csr.mom[e]), int(csr.keym[e]), csr.pids[v])


def below_optimum(p, q):
    """Frozen b- rule: (p+q)/2q reduced if p>q, else 1/2 (diagnostic only)."""
    if p > q:
        return reduce_pair(p + q, 2 * q)
    return (1, 2)


def reduce_pair(p, q):
    """Reduced positive pair."""
    g = math.gcd(p, q)
    return p // g, q // g


def _dump_zst(path, obj):
    import zstandard as zstd
    blob = (json.dumps(obj, sort_keys=True) + "\n").encode("utf-8")
    logical = hashlib.sha256(blob).hexdigest()
    with open(path, "wb") as f:
        f.write(zstd.ZstdCompressor(level=19).compress(blob))
    return logical


def tight_backward_to_other_diagonal(csr, tight, f):
    """Nonempty tight path from a different diagonal to f, or None.

    Total is U[f]-U[d2] == 0 for forced diagonals: a valid representative
    for zero paths ending at f. DFS completeness: any U-optimal path to f
    from another diagonal is tight throughout.
    """
    tc = csr.tree_count
    pred = {f: None}
    stack = [f]
    while stack:
        v = stack.pop()
        for (t, e) in tight[v]:
            if t not in pred:
                pred[t] = (v, e)
                stack.append(t)
    cands = []
    for d, _ in pred.items():
        if d == f:
            continue
        da, db = divmod(csr.pids[d], tc)
        if da == db:
            cands.append(d)
    if not cands:
        return None
    d = min(cands, key=lambda x: csr.pids[x])
    chain = []
    cur = d
    while cur != f:
        nxt, e = pred[cur]
        chain.append(edge_tuple_of(csr, cur, e, nxt))
        cur = nxt
    return chain


def build_critical(n, tables, reach, p, q, U, V, outdir):
    """Extract corridors, SCCs, FORCED_DELTA, trajectories, B06 diagnostic."""
    os.makedirs(outdir, exist_ok=True)
    csr = sv.build_csr(tables, reach)
    c = reach.tree_count
    G = [U[i] - V[i] for i in range(csr.size)]
    zero = build_zero_graph(csr, U, V, p, q)
    # console.log equivalent [WP3-CR-03]: corridors via prefix/suffix.
    console_log("WP3-CR-03", "corridor construction begin")
    tight = sv.tight_pred_lists(csr, U, p, q)
    vtight = sv.vtight_out_lists(csr, V, p, q)
    paths = {}
    for f in range(csr.size):
        if G[f] != 0:
            continue
        f_pid = csr.pids[f]
        chain = None
        if not csr.diag[f]:
            pre = sv.dfs_prefix(csr, tight, f)
            suf = sv.dfs_suffix(csr, vtight, V, f)
            if pre is not None and suf is not None:
                chain = pre + suf
        else:
            for e in range(csr.off[f], csr.off[f + 1]):
                j = csr.tgt[e]
                if U[f] + p * int(csr.am[e]) - q * int(csr.ym[e]) - V[j] != 0:
                    continue
                suf = sv.dfs_suffix(csr, vtight, V, j)
                if suf is None:
                    continue
                chain = [sv.edge_tuple(csr, f, e, j)] + suf
                break
            if chain is None:
                chain = tight_backward_to_other_diagonal(csr, tight, f)
        if chain is None or not chain:
            continue
        sa, sy = sv.edge_sums(csr, chain)
        a0, b0 = divmod(chain[0][0], c)
        if a0 != b0 or sa <= 0 or p * sa - q * sy != 0:
            raise AssertionError("corridor failed verification")
        paths[str(f_pid)] = {
            "edges": [{"key": e[2], "mode": mode_name(e[1]),
                       "forced_after": G[csr.reach.index_of[e[3]]] == 0,
                       "forced_before": G[csr.reach.index_of[e[0]]] == 0,
                       "source": e[0], "target": e[3]} for e in chain],
            "length": len(chain), "sum_a": sa, "sum_y": sy}
    with open(os.path.join(outdir, "paths.json"), "w", encoding="utf-8") as f:
        json.dump(paths, f, sort_keys=True)
        f.write("\n")
    with open(os.path.join(outdir, "canonical_paths.json"), "w", encoding="utf-8") as f:
        json.dump(paths, f, sort_keys=True, indent=2)
        f.write("\n")
    # console.log equivalent [WP3-CR-04]: SCC decomposition begin.
    console_log("WP3-CR-04", "SCC decomposition begin")
    sccs, comp = zero_sccs(csr, zero)
    crit = []
    for cid, members in enumerate(sccs):
        if len(members) > 1 or any(j == members[0] for (j, _) in zero["fwd"][members[0]]):
            cyc = canonical_cycle(csr, zero, members, cid, comp, p, q, U)
            if cyc is None:
                continue
            start_pid = cyc["edges"][0][0]
            crit.append({"canonical_cycle": {
                "edges": [{"key": e[2], "mode": mode_name(e[1]),
                           "source": e[0], "target": e[3]} for e in cyc["edges"]],
                "sum_a": cyc["sum_a"], "sum_y": cyc["sum_y"]},
                "member_count": len(members),
                "members": sorted(csr.pids[v] for v in members),
                "prefix": [{"key": e[2], "mode": mode_name(e[1]),
                            "source": e[0], "target": e[3]}
                           for e in sv.diagonal_prefix(csr, start_pid)],
                "scc_id": cid})
    with open(os.path.join(outdir, "sccs.json"), "w", encoding="utf-8") as f:
        json.dump(crit, f, sort_keys=True)
        f.write("\n")
    with open(os.path.join(outdir, "canonical_cycles.json"), "w", encoding="utf-8") as f:
        json.dump([{"edges": c["canonical_cycle"]["edges"], "scc_id": c["scc_id"],
                    "sum_a": c["canonical_cycle"]["sum_a"],
                    "sum_y": c["canonical_cycle"]["sum_y"]} for c in crit],
                  f, sort_keys=True, indent=2)
        f.write("\n")
    # console.log equivalent [WP3-CR-05]: FORCED_DELTA union begin.
    console_log("WP3-CR-05", "forced-delta union begin")
    fcycle = set()
    for entry in crit:
        members = set(entry["members"])
        for s_pid in members:
            si = csr.reach.index_of[s_pid]
            for (j, e) in zero["fwd"][si]:
                if csr.pids[j] in members:
                    fcycle.add((si, int(csr.mom[e]), int(csr.keym[e])))
    rows = []
    for i in range(csr.size):
        for e in range(csr.off[i], csr.off[i + 1]):
            j = csr.tgt[e]
            mode, key = int(csr.mom[e]), int(csr.keym[e])
            w = p * int(csr.am[e]) - q * int(csr.ym[e])
            on_path = (i, mode, key) in zero["fpath"]
            on_cycle = (i, mode, key) in fcycle
            fgap = G[i] == 0 and G[j] == 0 and U[j] - U[i] == w
            v_tight = V[j] - V[i] == w
            u_tight = U[j] - U[i] == w
            prov = []
            if on_path:
                prov.append("FPATH")
            if on_cycle:
                prov.append("FCYCLE")
            if fgap:
                prov.append("FGAP")
            if v_tight:
                prov.append("VBELLMAN")
            if u_tight:
                prov.append("UBELLMAN")
            forced = on_path or on_cycle or fgap
            rows.append({"a": int(csr.am[e]), "forced_delta": forced,
                         "forced_delta_scaled": str(w) if forced else None,
                         "key": key, "mode": mode_name(mode),
                         "on_zero_cycle": on_cycle, "on_zero_path": on_path,
                         "provenance": prov, "scaled_slack": str(w),
                         "source_pair_id": csr.pids[i], "target_pair_id": csr.pids[j],
                         "U_bellman_tight": u_tight, "V_bellman_tight": v_tight,
                         "y": int(csr.ym[e])})
    h_fd = _dump_zst(os.path.join(outdir, "forced_delta_edges.json.zst"),
                     [r for r in rows if r["forced_delta"]])
    h_z = _dump_zst(os.path.join(outdir, "zero_reduced.json.zst"),
                    [{"key": k[2], "mode": mode_name(k[1]),
                      "source_index": k[0]} for k in sorted(zero["z_edges"])])
    write_trajectories(n, tables, reach, outdir, paths, crit, csr, U, V, G, p, q)
    below = run_below_optimum(n, tables, reach, csr, p, q, outdir)
    summary = {"b": {"p": str(p), "q": str(q)},
               "below_optimum": below["label"],
               "critical_scc_count": len(crit),
               "forced_delta_count": sum(1 for r in rows if r["forced_delta"]),
               "forced_delta_share": {"DELETE": sum(1 for r in rows if r["forced_delta"] and r["mode"] == "DELETE"),
                                      "KEEP": sum(1 for r in rows if r["forced_delta"] and r["mode"] == "KEEP")},
               "logical_forced_delta_sha256": h_fd, "logical_zero_sha256": h_z,
               "n": n, "transient_corridor_count": len(paths)}
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, sort_keys=True, indent=2)
        f.write("\n")
    # console.log equivalent [WP3-CR-06]: critical artifacts written.
    console_log("WP3-CR-06", "n=%d sccs=%d forced_delta=%d" % (n, len(crit), summary["forced_delta_count"]))
    return summary


def write_trajectories(n, tables, reach, outdir, paths, crit, csr, U, V, G, p, q):
    """Human-readable canonical trajectories (paths then cycles).

    Every step records: A/B shapes before and after, a/y costs, scaled
    slack, forced H values before/after (U=V point values where forced),
    criticality provenance is carried by the parent section; structural
    deltas are a WP-4 feature-join placeholder by design.
    """
    # console.log equivalent [WP3-CR-07]: trajectories begin.
    console_log("WP3-CR-07", "trajectories begin")
    c = reach.tree_count
    idx = reach.index_of

    def step_line(e):
        s_pid, mode, key, t_pid = e["source"], e["mode"], e["key"], e["target"]
        tgt, a, y = pg.pair_successor(tables, s_pid, mode_of(mode), key)
        assert tgt == t_pid
        a_id, b_id = divmod(s_pid, c)
        a2, b2 = divmod(t_pid, c)
        return ("- %s key=%d A=%s B=%s a=%d y=%d slack=%d "
                "U/V before=(%s/%s) after=(%s/%s) forced %s->%s | structural deltas: WP-4" % (
                    mode, key, tables.shapes[a_id], tables.shapes[b_id], a, y,
                    p * a - q * y, U[idx[s_pid]], V[idx[s_pid]],
                    U[idx[t_pid]], V[idx[t_pid]],
                    G[idx[s_pid]] == 0, G[idx[t_pid]] == 0))

    lines = ["# Critical trajectories n=%d b=%d/%d" % (n, p, q), ""]
    for pid, rec in sorted(paths.items(), key=lambda kv: int(kv[0])):
        lines.append("## Path to pair %s (length %d, a=%d y=%d, zero-slack)" % (
            pid, rec["length"], rec["sum_a"], rec["sum_y"]))
        for e in rec["edges"]:
            lines.append(step_line(e))
        lines.append("")
    for entry in crit:
        cyc = entry["canonical_cycle"]
        lines.append("## Cycle in SCC %d (members %d, a=%d y=%d, zero-slack)" % (
            entry["scc_id"], entry["member_count"], cyc["sum_a"], cyc["sum_y"]))
        for e in cyc["edges"]:
            lines.append(step_line(e))
        lines.append("")
    with open(os.path.join(outdir, "trajectories.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    # console.log equivalent [WP3-CR-08]: trajectories written.
    console_log("WP3-CR-08", "trajectories paths=%d cycles=%d" % (len(paths), len(crit)))


def run_below_optimum(n, tables, reach, csr, p, q, outdir):
    """Frozen b- diagnostic: exact NEGATIVE_PATH vs NEGATIVE_CYCLE."""
    # console.log equivalent [WP3-CR-09]: below-optimum diagnostic begin.
    console_log("WP3-CR-09", "below-optimum diagnostic begin")
    pb, qb = below_optimum(p, q)
    verdict, wit, _ = sv.check_validity(csr, pb, qb)
    if verdict == "VALID":
        raise AssertionError("b- unexpectedly valid")
    label = "NEGATIVE_PATH" if wit["kind"] == "transient" else "NEGATIVE_CYCLE"
    obj = {"b_minus": {"p": str(pb), "q": str(qb)}, "certified_b": {"p": str(p), "q": str(q)},
           "kind": wit["kind"], "label": label, "n": n,
           "sum_a": wit["sum_a"], "sum_y": wit["sum_y"],
           "witness": [{"key": e[2], "mode": mode_name(e[1]),
                        "source": e[0], "target": e[3]} for e in wit["edges"]]}
    with open(os.path.join(outdir, "below_optimum.json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True, indent=2)
        f.write("\n")
    # console.log equivalent [WP3-CR-10]: diagnostic preserved.
    console_log("WP3-CR-10", "below-optimum %s a=%d y=%d" % (label, wit["sum_a"], wit["sum_y"]))
    return obj
