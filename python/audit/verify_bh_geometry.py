"""Independent b_H=2 canonical-geometry verifier (imports python/audit only).

Rebuilds the reachable Pair-Access graph from scratch via the independent
Splay/tree implementation, loads artifacts/potentials/n{n}/hypothesis_bH/
(U/V/G.json.zst + forced_states.json + bH_geometry.v1.json companion), and
checks: companion schema + exact b=2/1 declaration, lengths, nonnegativity,
diagonal zeros, V<=U pointwise, G==U-V, forced==exact-zero-gap, every
reachable-edge Bellman inequality at b=2, tight-witness existence both
sides, AND full independent value recompute (own queue Bellman-Ford for U
from diagonals; own reverse-propagation longest-path for V from the empty
continuation) with exact equality against artifact values.

Refuses any b other than exactly 2/1. Exit 0 iff all pass. Step-logged.
"""

import argparse
import hashlib
import json
import os
import sys
from array import array
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.audit import graph  # noqa: E402

KEEP, DELETE = graph.KEEP, graph.DELETE


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def load_rows(path):
    """Load (rows, logical_sha256) from a .json.zst table artifact."""
    import zstandard as zstd
    with open(path, "rb") as handle:
        blob = zstd.ZstdDecompressor().decompress(handle.read())
    return json.loads(blob.decode("utf-8")), hashlib.sha256(blob).hexdigest()


def build_edge_arrays(tables, reach):
    """Flat forward/reverse edge arrays in frozen deterministic order.

    Forward: for pid ascending, mode KEEP/DELETE, key 1..n -> (tgt, w=2a-y).
    Reverse: per-state predecessor lists (u, w) with offset indexing.
    """
    # console.log equivalent [WP5-UH4-10]: edge-array construction.
    console_log("WP5-UH4-10", "building edge arrays R=%d" % len(reach.pair_ids))
    order = reach.pair_ids
    pos = {pid: i for i, pid in enumerate(order)}
    width = 2 * tables.n
    tgt = array("i", [0]) * (len(order) * width)
    wgt = array("i", [0]) * (len(order) * width)
    rev_lists = [[] for _ in order]
    k = 0
    for i, pid in enumerate(order):
        for mode in (KEEP, DELETE):
            for key in range(1, tables.n + 1):
                tgt_id, a, y = graph.successor(tables, pid, mode, key)
                j = pos[tgt_id]
                w = 2 * a - y
                tgt[k] = j
                wgt[k] = w
                rev_lists[j].append((i, w))
                k += 1
    rev_off = array("i", [0]) * (len(order) + 1)
    total = 0
    for i, lst in enumerate(rev_lists):
        rev_off[i] = total
        total += len(lst)
    rev_u = array("i", [0]) * total
    rev_w = array("i", [0]) * total
    k = 0
    for lst in rev_lists:
        for u, w in lst:
            rev_u[k] = u
            rev_w[k] = w
            k += 1
    return tgt, wgt, width, rev_off, rev_u, rev_w


def recompute_U(r_size, diagonals, tgt, wgt, width):
    """Independent U: queue Bellman-Ford shortest diagonal-rooted path sums."""
    INF = 10 ** 30
    dist = [INF] * r_size
    queue = deque()
    in_queue = bytearray(r_size)
    for d in diagonals:
        dist[d] = 0
        queue.append(d)
        in_queue[d] = 1
    pops = 0
    watchdog = r_size * width * max(2, r_size.bit_length() + 4)
    while queue:
        u = queue.popleft()
        in_queue[u] = 0
        pops += 1
        if pops > watchdog:
            raise AssertionError("U recompute watchdog: possible negative cycle")
        base = u * width
        du = dist[u]
        for k in range(width):
            v = tgt[base + k]
            cand = du + wgt[base + k]
            if cand < dist[v]:
                dist[v] = cand
                if not in_queue[v]:
                    queue.append(v)
                    in_queue[v] = 1
    return dist


def recompute_V(r_size, tgt, wgt, width, rev_off, rev_u, rev_w):
    """Independent V: async longest-path propagation from empty continuation.

    V[u] = max(0, max over outgoing (V[v] - w)); no positive -w cycle exists
    exactly when the b=2 instance is valid, so queue propagation converges.
    """
    val = [0] * r_size
    queue = deque(range(r_size))
    in_queue = bytearray(b"\x01") * r_size
    pops = 0
    watchdog = r_size * width * 64
    while queue:
        u = queue.popleft()
        in_queue[u] = 0
        pops += 1
        if pops > watchdog:
            raise AssertionError("V recompute watchdog exceeded")
        base = u * width
        best = 0
        for k in range(width):
            cand = val[tgt[base + k]] - wgt[base + k]
            if cand > best:
                best = cand
        if best > val[u]:
            val[u] = best
            for k in range(rev_off[u], rev_off[u + 1]):
                p = rev_u[k]
                if not in_queue[p]:
                    queue.append(p)
                    in_queue[p] = 1
    return val


def main(argv=None):
    """Verify one hypothesis_bH directory independently."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--pot-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    # console.log equivalent [WP5-UH4-09]: independent verification begin.
    console_log("WP5-UH4-09", "independent b=2 verification begin n=%d" % args.n)
    checks = {}
    with open(os.path.join(args.pot_dir, "bH_geometry.v1.json"), encoding="utf-8") as handle:
        companion = json.load(handle)
    checks["companion"] = (
        companion.get("schema") == "BHG-v0.1"
        and companion.get("b_H") == {"p": "2", "q": "1"}
        and companion.get("n") == args.n
        and "NOT WP-3 b_n* discovery geometry" in companion.get("b_role", ""))
    if not checks["companion"]:
        # console.log equivalent [WP5-UH4-09]: companion refusal emission.
        console_log("WP5-UH4-09", "companion b/schema refusal n=%d" % args.n)
        return _write(args.out, args.n, checks, "FAIL")
    tables = graph.build_tables(args.n)
    reach = graph.build_reachability(tables)
    order = reach.pair_ids
    r_size = len(order)
    checks["counts"] = (companion.get("reachable_pair_count") == r_size
                        and companion.get("tree_count") == tables.tree_count)
    u_rows, u_sha = load_rows(os.path.join(args.pot_dir, "U.json.zst"))
    v_rows, v_sha = load_rows(os.path.join(args.pot_dir, "V.json.zst"))
    g_rows, g_sha = load_rows(os.path.join(args.pot_dir, "G.json.zst"))
    checks["hashes"] = (u_sha == companion["files"]["U"]["logical_sha256"]
                        and v_sha == companion["files"]["V"]["logical_sha256"]
                        and g_sha == companion["files"]["G"]["logical_sha256"])
    U = {r["pair_id"]: int(r["U_scaled"]) for r in u_rows}
    V = {r["pair_id"]: int(r["V_scaled"]) for r in v_rows}
    G = {r["pair_id"]: int(r["G_scaled"]) for r in g_rows}
    c = tables.tree_count
    checks["lengths"] = (len(U) == r_size and len(V) == r_size and len(G) == r_size
                         and set(U) == set(order))
    ok = True
    for pid in order:
        if U[pid] < 0 or V[pid] < 0:
            ok = False
        a_id, b_id = divmod(pid, c)
        if a_id == b_id and (U[pid] != 0 or V[pid] != 0):
            ok = False
        if V[pid] > U[pid] or G[pid] != U[pid] - V[pid]:
            ok = False
    checks["values"] = ok
    with open(os.path.join(args.pot_dir, "forced_states.json"), encoding="utf-8") as handle:
        forced = json.load(handle)["forced_pair_ids"]
    checks["forced"] = sorted(forced) == sorted(pid for pid in order if G[pid] == 0)
    tgt, wgt, width, rev_off, rev_u, rev_w = build_edge_arrays(tables, reach)
    pos = {pid: i for i, pid in enumerate(order)}
    # console.log equivalent [WP5-UH4-11]: full-edge inequality sweep at b=2.
    console_log("WP5-UH4-11", "inequality sweep n=%d R=%d" % (args.n, r_size))
    ok = True
    for i, pid in enumerate(order):
        base = i * width
        for k in range(width):
            j = tgt[base + k]
            w = wgt[base + k]
            if U[order[j]] - U[pid] > w or V[order[j]] - V[pid] > w:
                ok = False
                break
        if not ok:
            break
    checks["inequalities"] = ok
    ok_u, ok_v = True, True
    for i, pid in enumerate(order):
        a_id, b_id = divmod(pid, c)
        if not (a_id == b_id and U[pid] == 0):
            found = False
            for k in range(rev_off[i], rev_off[i + 1]):
                u = rev_u[k]
                if U[order[u]] + rev_w[k] == U[pid]:
                    found = True
                    break
            if not found:
                ok_u = False
        if V[pid] > 0:
            base = i * width
            found_v = False
            for k in range(width):
                if V[order[tgt[base + k]]] - wgt[base + k] == V[pid]:
                    found_v = True
                    break
            if not found_v:
                ok_v = False
    checks["bellman_U"] = ok_u
    checks["bellman_V"] = ok_v
    # console.log equivalent [WP5-UH4-12]: independent value recompute.
    console_log("WP5-UH4-12", "independent U/V recompute n=%d" % args.n)
    diagonals = [pos[t * c + t] for t in range(c)]
    ru = recompute_U(r_size, diagonals, tgt, wgt, width)
    rv = recompute_V(r_size, tgt, wgt, width, rev_off, rev_u, rev_w)
    checks["recompute_U"] = all(ru[i] == U[pid] for i, pid in enumerate(order))
    checks["recompute_V"] = all(rv[i] == V[pid] for i, pid in enumerate(order))
    verdict = "PASS" if all(checks.values()) else "FAIL"
    # console.log equivalent [WP5-UH4-13]: independent verdict.
    console_log("WP5-UH4-13", "independent b=2 geometry n=%d %s" % (args.n, verdict))
    return _write(args.out, args.n, checks, verdict)


def _write(outdir, n, checks, verdict):
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "verify_bh2.json"), "w", encoding="utf-8") as handle:
        json.dump({"checks": checks, "n": n, "b_H": {"p": "2", "q": "1"},
                   "verdict": verdict}, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
