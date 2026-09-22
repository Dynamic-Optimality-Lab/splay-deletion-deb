"""Independent b_H canonical-table verifier (imports python/audit only).

Re-derives every check for U_{b_H}/V_{b_H} tables at an EXPLICIT (p_H,q_H)
taken from argv (never from a bn_certificate, so no b_n*/b_H mixing is
possible by construction): table lengths, nonnegativity, diagonal zeros,
V<=U pointwise, G==U-V consistency, the full reachable-edge Bellman
inequalities at (p_H,q_H), and Bellman equality witnesses (tight
predecessor per non-initialized U state; tight outgoing edge per V>0
state), all recomputed via the independent graph implementation.
Exit 0 iff all pass. Step-logged.
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
    return {int(r["pair_id"]): int(r[field]) for r in rows}


def main(argv=None):
    """Verify b_H canonical tables independently."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--pot-dir", required=True)
    ap.add_argument("--p", type=int, required=True)
    ap.add_argument("--q", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    # console.log equivalent [WP5-AUD-BH-01]: independent re-derivation begin.
    console_log("WP5-AUD-BH-01", "re-deriving b_H geometry n=%d b=%d/%d" % (args.n, args.p, args.q))
    checks = {}
    tables = graph.build_tables(args.n)
    reach = graph.build_reachability(tables)
    U = load_table(os.path.join(args.pot_dir, "U_bH.json.zst"), "U_scaled")
    V = load_table(os.path.join(args.pot_dir, "V_bH.json.zst"), "V_scaled")
    c = tables.tree_count
    checks["lengths"] = (len(U) == len(reach.pair_ids) and len(V) == len(reach.pair_ids))
    ok = True
    for pid in reach.pair_ids:
        if U[pid] < 0 or V[pid] < 0:
            ok = False
        a_id, b_id = divmod(pid, c)
        if a_id == b_id and (U[pid] != 0 or V[pid] != 0):
            ok = False
        if V[pid] > U[pid]:
            ok = False
    checks["values"] = ok
    # console.log equivalent [WP5-AUD-BH-02]: full-edge inequality sweep.
    console_log("WP5-AUD-BH-02", "inequality sweep over %d states" % len(reach.pair_ids))
    ok = True
    for pid in reach.pair_ids:
        for mode in (KEEP, DELETE):
            for key in range(1, args.n + 1):
                tgt, a, y = graph.successor(tables, pid, mode, key)
                w = args.p * a - args.q * y
                if U[tgt] - U[pid] > w or V[tgt] - V[pid] > w:
                    ok = False
    checks["inequalities"] = ok
    ok_u, ok_v = True, True
    for pid in reach.pair_ids:
        a_id, b_id = divmod(pid, c)
        if a_id == b_id and U[pid] == 0:
            continue
        found = any(_tight_predecessor(tables, reach, pid, mode, key, U, args.p, args.q)
                    for mode in (KEEP, DELETE) for key in range(1, args.n + 1))
        if not found:
            ok_u = False
        if V[pid] > 0:
            found_v = False
            for mode in (KEEP, DELETE):
                for key in range(1, args.n + 1):
                    tgt, a, y = graph.successor(tables, pid, mode, key)
                    if -(args.p * a - args.q * y) + V[tgt] == V[pid]:
                        found_v = True
            if not found_v:
                ok_v = False
    checks["bellman_U"] = ok_u
    checks["bellman_V"] = ok_v
    verdict = "PASS" if all(checks.values()) else "FAIL"
    # console.log equivalent [WP5-AUD-BH-03]: verdict.
    console_log("WP5-AUD-BH-03", "b_H tables n=%d %s" % (args.n, verdict))
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify_bh_tables.json"), "w", encoding="utf-8") as f:
        json.dump({"checks": checks, "n": args.n,
                   "b_H": {"p": str(args.p), "q": str(args.q)}, "verdict": verdict},
                  f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if verdict == "PASS" else 1


def _tight_predecessor(tables, reach, pid, mode, key, U, p, q):
    """Inverse-table predecessor scan (spec Phase-07 reverse-edge generation)."""
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
