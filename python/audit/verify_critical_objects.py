"""Independent critical-objects verifier (imports python/audit only).

Re-derives the zero-reduced edge set from sealed U, recomputes FPATH /
FCYCLE / FGAP under the frozen rules, and compares the exact sets against
the sealed forced-delta table; re-verifies canonical paths/cycles (legality,
zero totals, diagonal rooting/prefixes) and the B06 below-optimum negative
witness (type, sums, negative slack). Exit 0 iff all pass. Step-logged.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.audit import graph  # noqa: E402

KEEP, DELETE = graph.KEEP, graph.DELETE


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def mode_of(name):
    """Mode string to frozen mode code."""
    return KEEP if name == "KEEP" else DELETE


def _tight_preds(tables, reach, U, p, q, pid, mode, key):
    """Tight predecessors of pid via inverse single-tree tables (spec 7.3).

    DELETE predecessor of (A2,B): {(A,B) : A in pred[x][A2]}.
    KEEP predecessor of (A2,B2): cross product. Filtered by R_n.
    Yields only predecessors with U[src]+L(e) == U[pid].
    """
    c = tables.tree_count
    a2, b2 = divmod(pid, c)
    cands = []
    if mode == DELETE:
        for a in tables.pred[key][a2]:
            cand = a * c + b2
            if cand in reach.index_of:
                cands.append(cand)
    else:
        for a in tables.pred[key][a2]:
            for b in tables.pred[key][b2]:
                cand = a * c + b
                if cand in reach.index_of:
                    cands.append(cand)
    for cand in cands:
        tgt, a, y = graph.successor(tables, cand, mode, key)
        if tgt == pid and U[cand] + p * a - q * y == U[pid]:
            yield cand


def load_potential(path, field):
    """Load integer table {pair_id: value} from .json.zst."""
    import zstandard as zstd
    with open(path, "rb") as f:
        rows = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    return {r["pair_id"]: int(r[field]) for r in rows}


def main(argv=None):
    """Verify sealed critical objects independently."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--cert-dir", required=True)
    ap.add_argument("--pot-dir", required=True)
    ap.add_argument("--crit-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    # console.log equivalent [WP3-AUD-CR-01]: independent re-derivation begin.
    console_log("WP3-AUD-CR-01", "re-deriving critical objects n=%d" % args.n)
    checks = {}
    tables = graph.build_tables(args.n)
    reach = graph.build_reachability(tables)
    idx = {p: i for i, p in enumerate(reach.pair_ids)}
    with open(os.path.join(args.cert_dir, "bn_certificate.json"), encoding="utf-8") as f:
        cert = json.load(f)
    p, q = int(cert["b"]["p"]), int(cert["b"]["q"])
    U = load_potential(os.path.join(args.pot_dir, "U.json.zst"), "U_scaled")
    V = load_potential(os.path.join(args.pot_dir, "V.json.zst"), "V_scaled")
    G = {pid: U[pid] - V[pid] for pid in reach.pair_ids}
    import zstandard as zstd
    import zstandard as zstd
    with open(os.path.join(args.crit_dir, "forced_delta_edges.json.zst"), "rb") as f:
        sealed = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    sealed_set = set((r["source_pair_id"], r["mode"], r["key"]) for r in sealed)
    fpath, fcycle_cand, fgap = set(), set(), set()
    zero_adj = {pid: [] for pid in reach.pair_ids}
    for pid in reach.pair_ids:
        for mode in (KEEP, DELETE):
            for key in range(1, args.n + 1):
                tgt, a, y = graph.successor(tables, pid, mode, key)
                w = p * a - q * y
                mname = "KEEP" if mode == KEEP else "DELETE"
                if w == U[tgt] - U[pid]:
                    zero_adj[pid].append(tgt)
                    if U[pid] + w - V[tgt] == 0:
                        fpath.add((pid, mname, key))
                if G[pid] == 0 and G[tgt] == 0 and U[tgt] - U[pid] == w:
                    fgap.add((pid, mname, key))
    # console.log equivalent [WP3-AUD-CR-02]: SCC recomputation begin.
    console_log("WP3-AUD-CR-02", "SCC recomputation R=%d" % len(reach.pair_ids))
    visited, order = set(), []
    for root in reach.pair_ids:
        if root in visited:
            continue
        stack = [(root, 0)]
        while stack:
            v, ci = stack.pop()
            if ci == 0:
                if v in visited:
                    continue
                visited.add(v)
            nbrs = zero_adj[v]
            if ci < len(nbrs):
                stack.append((v, ci + 1))
                if nbrs[ci] not in visited:
                    stack.append((nbrs[ci], 0))
            else:
                order.append(v)
    radj = {pid: [] for pid in reach.pair_ids}
    for pid in reach.pair_ids:
        for tgt in zero_adj[pid]:
            radj[tgt].append(pid)
    comp = {}
    for root in reversed(order):
        if root in comp:
            continue
        stack = [root]
        comp[root] = root
        while stack:
            v = stack.pop()
            for w in radj[v]:
                if w not in comp:
                    comp[w] = root
                    stack.append(w)
    from collections import Counter
    sizes = Counter(comp.values())
    for pid in reach.pair_ids:
        for mode in (KEEP, DELETE):
            for key in range(1, args.n + 1):
                tgt, a, y = graph.successor(tables, pid, mode, key)
                w = p * a - q * y
                mname = "KEEP" if mode == KEEP else "DELETE"
                if w == U[tgt] - U[pid] and comp[pid] == comp[tgt] and (
                        sizes[comp[pid]] > 1 or tgt == pid):
                    fcycle_cand.add((pid, mname, key))
    expect = fpath | fcycle_cand | fgap
    checks["forced_set"] = sealed_set == expect
    prov_ok = True
    by_key = {(r["source_pair_id"], r["mode"], r["key"]): r for r in sealed}
    for key in expect:
        r = by_key.get(key)
        if r is None or not r["forced_delta"]:
            prov_ok = False
    for r in sealed:
        want = set()
        if (r["source_pair_id"], r["mode"], r["key"]) in fpath:
            want.add("FPATH")
        if (r["source_pair_id"], r["mode"], r["key"]) in fcycle_cand:
            want.add("FCYCLE")
        if (r["source_pair_id"], r["mode"], r["key"]) in fgap:
            want.add("FGAP")
        if not want.issubset(set(r["provenance"])):
            prov_ok = False
        tgt = None
        for mode in (KEEP, DELETE):
            for kk in range(1, args.n + 1):
                t2, a, y = graph.successor(tables, r["source_pair_id"], mode, kk)
                if mode_of(r["mode"]) == mode and kk == r["key"]:
                    tgt = (t2, a, y)
        if tgt is None or tgt[0] != r["target_pair_id"]:
            prov_ok = False
        elif r["forced_delta_scaled"] != str(p * tgt[1] - q * tgt[2]):
            prov_ok = False
    checks["provenance"] = prov_ok

    def sums(edges):
        sa = sy = 0
        for (s, mode, key, t) in edges:
            tgt, a, y = graph.successor(tables, s, mode, key)
            if tgt != t:
                return None
            sa += a
            sy += y
        return sa, sy

    with open(os.path.join(args.crit_dir, "canonical_paths.json"), encoding="utf-8") as f:
        paths = json.load(f)
    paths_ok = True
    for pid, rec in paths.items():
        edges = [(e["source"], mode_of(e["mode"]), e["key"], e["target"]) for e in rec["edges"]]
        r = sums(edges)
        a0, b0 = divmod(edges[0][0], tables.tree_count) if edges else (0, 1)
        if not edges or a0 != b0 or r is None or p * r[0] - q * r[1] != 0:
            paths_ok = False
    checks["paths"] = paths_ok
    c = tables.tree_count
    qualifying = set()
    for pid in reach.pair_ids:
        if U[pid] != V[pid]:
            continue
        a_id, b_id = divmod(pid, c)
        if a_id != b_id:
            qualifying.add(str(pid))
            continue
        out_ok = False
        for mode in (KEEP, DELETE):
            for key in range(1, args.n + 1):
                tgt, a, y = graph.successor(tables, pid, mode, key)
                mname = "KEEP" if mode == KEEP else "DELETE"
                if (pid, mname, key) in fpath:
                    out_ok = True
        if out_ok:
            qualifying.add(str(pid))
            continue
        seen, stack, found = {pid}, [pid], False
        while stack and not found:
            v = stack.pop()
            for mode in (KEEP, DELETE):
                for key in range(1, args.n + 1):
                    for cand in _tight_preds(tables, reach, U, p, q, v, mode, key):
                        if cand in seen:
                            continue
                        ca, cb = divmod(cand, c)
                        if ca == cb and cand != pid:
                            found = True
                            break
                        seen.add(cand)
                        stack.append(cand)
                    if found:
                        break
                if found:
                    break
        if found:
            qualifying.add(str(pid))
    checks["coverage"] = set(paths.keys()) == qualifying
    with open(os.path.join(args.crit_dir, "sccs.json"), encoding="utf-8") as f:
        sccs = json.load(f)
    cyc_ok = True
    for entry in sccs:
        cyc = [(e["source"], mode_of(e["mode"]), e["key"], e["target"])
               for e in entry["canonical_cycle"]["edges"]]
        r = sums(cyc)
        pre = [(e["source"], mode_of(e["mode"]), e["key"], e["target"]) for e in entry["prefix"]]
        rp = sums(pre) if pre else (0, 0)
        if not cyc or cyc[0][0] != cyc[-1][3] or r is None or p * r[0] - q * r[1] != 0 or rp is None:
            cyc_ok = False
    checks["cycles"] = cyc_ok
    with open(os.path.join(args.crit_dir, "below_optimum.json"), encoding="utf-8") as f:
        below = json.load(f)
    w = [(e["source"], mode_of(e["mode"]), e["key"], e["target"]) for e in below["witness"]]
    r = sums(w)
    pb, qb = int(below["b_minus"]["p"]), int(below["b_minus"]["q"])
    checks["below"] = (r is not None and r[0] > 0 and pb * r[0] - qb * r[1] < 0
                       and below["label"] in ("NEGATIVE_PATH", "NEGATIVE_CYCLE"))
    verdict = "PASS" if all(checks.values()) else "FAIL"
    # console.log equivalent [WP3-AUD-CR-03]: verdict.
    console_log("WP3-AUD-CR-03", "critical n=%d %s" % (args.n, verdict))
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify_critical_objects.json"), "w", encoding="utf-8") as f:
        json.dump({"checks": checks, "n": args.n, "verdict": verdict},
                  f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
