"""Independent U/V/G verifier (imports python/audit only).

Reloads sealed potential tables and re-checks: lengths, nonnegativity,
diagonal zeros, every reachable edge inequality, V<=U pointwise, G==U-V,
forced==exact-zero-gap, and Bellman equality witnesses re-derived
independently (tight predecessor per U state with diagonal-init exception;
tight outgoing edge per V>0 state). Exit 0 iff all pass. Step-logged.
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


def load_table(path, field):
    """Load integer potential table {pair_id: value} from .json.zst."""
    import zstandard as zstd
    with open(path, "rb") as f:
        rows = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    return {r["pair_id"]: int(r[field]) for r in rows}


def main(argv=None):
    """Verify sealed U/V/G tables independently."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--cert-dir", required=True)
    ap.add_argument("--pot-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    # console.log equivalent [WP3-AUD-UV-01]: independent re-derivation begin.
    console_log("WP3-AUD-UV-01", "re-deriving U/V/G inputs n=%d" % args.n)
    checks = {}
    tables = graph.build_tables(args.n)
    reach = graph.build_reachability(tables)
    with open(os.path.join(args.cert_dir, "bn_certificate.json"), encoding="utf-8") as f:
        cert = json.load(f)
    p, q = int(cert["b"]["p"]), int(cert["b"]["q"])
    U = load_table(os.path.join(args.pot_dir, "U.json.zst"), "U_scaled")
    V = load_table(os.path.join(args.pot_dir, "V.json.zst"), "V_scaled")
    G = load_table(os.path.join(args.pot_dir, "G.json.zst"), "G_scaled")
    c = tables.tree_count
    checks["lengths"] = (len(U) == len(reach.pair_ids) and len(V) == len(reach.pair_ids)
                         and len(G) == len(reach.pair_ids))
    ok = True
    for pid in reach.pair_ids:
        if U[pid] < 0 or V[pid] < 0:
            ok = False
        a_id, b_id = divmod(pid, c)
        if a_id == b_id and (U[pid] != 0 or V[pid] != 0):
            ok = False
        if V[pid] > U[pid] or G[pid] != U[pid] - V[pid]:
            ok = False
    checks["values"] = ok
    with open(os.path.join(args.pot_dir, "forced_states.json"), encoding="utf-8") as f:
        forced = json.load(f)["forced_pair_ids"]
    checks["forced"] = sorted(forced) == sorted(pid for pid in reach.pair_ids if G[pid] == 0)
    # console.log equivalent [WP3-AUD-UV-02]: full-edge inequality sweep.
    console_log("WP3-AUD-UV-02", "inequality sweep over %d states" % len(reach.pair_ids))
    ok = True
    for pid in reach.pair_ids:
        for mode in (KEEP, DELETE):
            for key in range(1, args.n + 1):
                tgt, a, y = graph.successor(tables, pid, mode, key)
                w = p * a - q * y
                if U[tgt] - U[pid] > w or V[tgt] - V[pid] > w:
                    ok = False
    checks["inequalities"] = ok
    ok_u, ok_v = True, True
    for pid in reach.pair_ids:
        a_id, b_id = divmod(pid, c)
        if a_id == b_id and U[pid] == 0:
            continue
        found = False
        for mode in (KEEP, DELETE):
            for key in range(1, args.n + 1):
                if _tight_predecessor(tables, reach, pid, mode, key, U, p, q):
                    found = True
                    break
            if found:
                break
        if not found:
            ok_u = False
        if V[pid] > 0:
            found_v = False
            for mode in (KEEP, DELETE):
                for key in range(1, args.n + 1):
                    tgt, a, y = graph.successor(tables, pid, mode, key)
                    if -(p * a - q * y) + V[tgt] == V[pid]:
                        found_v = True
            if not found_v:
                ok_v = False
    checks["bellman_U"] = ok_u
    checks["bellman_V"] = ok_v
    verdict = "PASS" if all(checks.values()) else "FAIL"
    # console.log equivalent [WP3-AUD-UV-03]: verdict.
    console_log("WP3-AUD-UV-03", "U/V/G n=%d %s" % (args.n, verdict))
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify_uv.json"), "w", encoding="utf-8") as f:
        json.dump({"checks": checks, "n": args.n, "verdict": verdict},
                  f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if verdict == "PASS" else 1


def _tight_predecessor(tables, reach, pid, mode, key, U, p, q):
    """Yield Brute-force-free predecessors via inverse single-tree tables.

    DELETE predecessor of (A2,B) under x: {(A,B) : A in pred[x][A2]}.
    KEEP predecessor of (A2,B2): cross product of both pred lists.
    Filtered by R_n membership (spec Phase-07 reverse-edge generation).
    """
    c = tables.tree_count
    a2, b2 = divmod(pid, c)
    if mode == DELETE:
        for a in tables.pred[key][a2]:
            cand = a * c + b2
            if cand in reach.index_of:
                tgt, a_cost, y = graph.successor(tables, cand, mode, key)
                if tgt == pid and U[cand] + p * a_cost - q * y == U[pid]:
                    return True
        return False
    for a in tables.pred[key][a2]:
        for b in tables.pred[key][b2]:
            cand = a * c + b
            if cand in reach.index_of:
                tgt, a_cost, y = graph.successor(tables, cand, mode, key)
                if tgt == pid and U[cand] + p * a_cost - q * y == U[pid]:
                    return True
    return False


if __name__ == "__main__":
    sys.exit(main())
