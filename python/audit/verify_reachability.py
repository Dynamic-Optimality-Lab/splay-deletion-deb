"""Independent reachability verifier (imports python/audit only).

Re-derives R_n, compares the exact sorted pair-id set against the sealed
artifact, checks every diagonal present, every parent chain reaching a
diagonal, and full forward closure. Exit 0 iff all checks pass. Step-logged.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.audit import graph  # noqa: E402


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def main(argv=None):
    """Verify sealed reachability independently."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--tables-dir", required=True)
    ap.add_argument("--reach-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    # console.log equivalent [WP2-AUD-R-01]: independent re-derivation begin.
    console_log("WP2-AUD-R-01", "re-deriving reachability n=%d" % args.n)
    import zstandard as zstd
    with open(os.path.join(args.tables_dir, "forward.bin.zst"), "rb") as f:
        fwd = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    c = max(r["tree"] for r in fwd["records"]) + 1
    after = [[0] * (args.n + 1) for _ in range(c)]
    cost = [[0] * (args.n + 1) for _ in range(c)]
    for r in fwd["records"]:
        after[r["tree"]][r["x"]] = r["after"]
        cost[r["tree"]][r["x"]] = r["cost"]
    shapes = graph.canonical_shapes(args.n)
    pred = [None] + [[[b for b in range(c) if after[b][x] == a] for a in range(c)]
                     for x in range(1, args.n + 1)]
    tables = graph.Tables(args.n, shapes, after, cost, pred)
    reach = graph.build_reachability(tables)
    with open(os.path.join(args.reach_dir, "reachable.json.zst"), "rb") as f:
        sealed = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    checks = {}
    checks["exact_set"] = reach.pair_ids == sealed["pair_ids"]
    diags = [t * c + t for t in range(c)]
    checks["diagonals"] = all(d in reach.pair_ids for d in diags)
    ok = True
    for pid in reach.pair_ids:
        cur = pid
        guard = len(reach.pair_ids) + 1
        while cur in reach.parents and guard > 0:
            cur = reach.parents[cur][0]
            guard -= 1
        a_id, b_id = divmod(cur, c)
        if a_id != b_id or guard <= 0:
            ok = False
            break
    checks["parent_chains"] = ok
    closed = True
    for pid in reach.pair_ids:
        for mode in (graph.KEEP, graph.DELETE):
            for key in range(1, args.n + 1):
                tgt, _, _ = graph.successor(tables, pid, mode, key)
                if tgt not in reach.index_of:
                    closed = False
    checks["closure"] = closed
    verdict = "PASS" if all(checks.values()) else "FAIL"
    # console.log equivalent [WP2-AUD-R-02]: verdict.
    console_log("WP2-AUD-R-02", "reachability n=%d %s R=%d" % (args.n, verdict, len(reach.pair_ids)))
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify_reachability.json"), "w", encoding="utf-8") as f:
        json.dump({"checks": checks, "n": args.n,
                   "reachable_pair_count": len(reach.pair_ids), "verdict": verdict},
                  f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
