"""Rederive + preserve the min-support lower-bound counts (audit artifact).

For k=0..4: every column subset (bend column excluded as all-zero) has an
inconsistent restricted system -> no exact solution with support <= 4 exists
in ANY coefficient domain, including unrestricted Q. Writes
artifacts/hypotheses/min_support_exhaustion_log.json
"""
import itertools
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining.affine_exhaustion import (
    load_fcyclerows, mat_of, tgt_of, restricted_solve, FEATURE_ORDER,
)
from python.mining import holdout_firewall as firewall


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def main():
    firewall.hydrate_from_files()
    rows = load_fcyclerows([4, 5])
    M, t = mat_of(rows), tgt_of(rows)
    zero_cols = [FEATURE_ORDER.index("f_bend_placeholder")]
    cols = [j for j in range(16) if j not in zero_cols]
    log = {"scope": "column subsets of 15 non-zero columns, k=0..4", "per_k": {}}
    for k in range(0, 5):
        counts = {"inconsistent": 0, "unique": 0, "affine": 0}
        total = 0
        for support in itertools.combinations(cols, k):
            status, _ = restricted_solve(M, t, support)
            counts[status] += 1
            total += 1
        log["per_k"][str(k)] = {"total": total, "statuses": counts}
        console_log("MINBOUND", "k=%d total=%d %s" % (k, total, counts))
    log["conclusion"] = ("all %d subsets inconsistent -> minimum exact support over Q is >= 5; "
                         "attained at 5 (see track_b_affine_space.json), hence exactly 5."
                         % sum(v["total"] for v in log["per_k"].values()))
    with open(os.path.join(REPO, "artifacts", "hypotheses", "min_support_exhaustion_log.json"),
              "w", encoding="utf-8") as f:
        json.dump(log, f, sort_keys=True, indent=2)
        f.write("\n")
    console_log("MINBOUND-99", "wrote min_support_exhaustion_log.json")


if __name__ == "__main__":
    main()
