"""Independent transition-table verifier (imports python/audit only).

Re-derives every (T, x) record via the independent Splay implementation and
compares cost + after-tree id against the sealed forward artifact; checks
inverse conservation. Exit 0 iff all checks pass. Step-logged.
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
    """Verify sealed transition tables independently."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--tables-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    # console.log equivalent [WP2-AUD-T-01]: independent re-derivation begin.
    console_log("WP2-AUD-T-01", "re-deriving transitions n=%d" % args.n)
    import zstandard as zstd
    with open(os.path.join(args.tables_dir, "forward.bin.zst"), "rb") as f:
        fwd = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    with open(os.path.join(args.tables_dir, "inverse.bin.zst"), "rb") as f:
        inv = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    tables = graph.build_tables(args.n)
    mismatches = []
    for r in fwd["records"]:
        if tables.cost[r["tree"]][r["x"]] != r["cost"]:
            mismatches.append(("cost", r["tree"], r["x"]))
        if tables.after[r["tree"]][r["x"]] != r["after"]:
            mismatches.append(("after", r["tree"], r["x"]))
    if len(fwd["records"]) != args.n * len(tables.shapes):
        mismatches.append(("count", len(fwd["records"])))
    for x in range(1, args.n + 1):
        if sum(len(v) for v in inv["pred"][str(x)]) != len(tables.shapes):
            mismatches.append(("conservation", x))
        for after_id, befores in enumerate(inv["pred"][str(x)]):
            if sorted(befores) != befores or befores != tables.pred[x][after_id]:
                mismatches.append(("inverse", x, after_id))
    verdict = "PASS" if not mismatches else "FAIL"
    # console.log equivalent [WP2-AUD-T-02]: verdict.
    console_log("WP2-AUD-T-02", "transitions n=%d %s mismatches=%d" % (args.n, verdict, len(mismatches)))
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify_transitions.json"), "w", encoding="utf-8") as f:
        json.dump({"mismatches": mismatches[:20], "n": args.n,
                   "records": len(fwd["records"]), "verdict": verdict},
                  f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
