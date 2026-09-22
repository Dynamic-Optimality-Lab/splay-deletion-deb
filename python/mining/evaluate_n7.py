"""n=7 hard-holdout evaluation (exactly once, after final freeze)."""
import json
import os
import sys
from fractions import Fraction
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining import holdout_firewall as firewall

def main():
    firewall.hydrate_from_files()
    # Ensure final in memory (hydrate loads from files).
    # Unlock exactly once.
    firewall.unlock_n7_for_evaluation("H-SA02-B-v1-final")
    print("[HOLDOUT] n7 unlocked once for H-SA02-B-v1-final")
    # Build n7 state + deltas + anatomy (now permitted).
    from python.mining import build_features as bf
    import python.mining.cycle_anatomy as ca
    bf.build_state_table(7, os.path.join(REPO, "artifacts", "features", "n7"))
    bf.build_edge_deltas(7,
                         os.path.join(REPO, "artifacts", "features", "n7"),
                         os.path.join(REPO, "artifacts", "critical", "n7"),
                         os.path.join(REPO, "artifacts", "features", "n7", "edge_deltas.json.zst"))
    ca.build_anatomy(7, os.path.join(REPO, "artifacts", "cycle_anatomy", "n7"),
                     allow_n6=True, allow_n7=True)
    # Evaluate final candidate on n7 FCYCLE.
    import zstandard as zstd
    with open(os.path.join(REPO, "artifacts", "hypotheses", "H-SA02-B-v1-final.json"), encoding="utf-8") as f:
        hyp = json.load(f)
    coeffs = hyp["coefficients"]
    with open(os.path.join(REPO, "artifacts", "features", "n7", "edge_deltas.json.zst"), "rb") as f:
        deltas = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    with open(os.path.join(REPO, "artifacts", "certificates", "n7", "bn_certificate.json"), encoding="utf-8") as f:
        cert = json.load(f)
    prime_q = int(cert["b"]["q"])
    worst = Fraction(0)
    worst_row = None
    n_eval = 0
    for row in deltas:
        if "FCYCLE" not in row["provenance"]:
            continue
        n_eval += 1
        pred = sum(Fraction(coeffs.get(k, "0")) * row["delta_F"].get(k, 0) for k in row["delta_F"])
        target = Fraction(int(row["scaled_slack"]), prime_q)
        res = abs(pred - target)
        if res > worst:
            worst = res
            worst_row = row
    report = {
        "candidate_id": "H-SA02-B-v1-final",
        "n": 7,
        "evaluated_rows": n_eval,
        "exact_max_residual": "%s/%s" % (worst.numerator, worst.denominator),
        "worst_row": ({k: worst_row[k] for k in ("n", "source_state_id", "target_state_id", "mode", "key", "scaled_slack")} if worst_row else None),
        "verdict": "PASS" if worst == 0 else "FAIL",
        "untouched": True,
        "note": "hard holdout revealed exactly once after final freeze; any revision loses untouched claim",
    }
    outdir = os.path.join(REPO, "artifacts", "holdout")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "n7_H-SA02-B-v1-final.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, sort_keys=True, indent=2)
        f.write("\n")
    print("[HOLDOUT] n=7 rows=%d max_res=%s verdict=%s untouched=True" % (n_eval, worst, report["verdict"]))

if __name__ == "__main__":
    main()
