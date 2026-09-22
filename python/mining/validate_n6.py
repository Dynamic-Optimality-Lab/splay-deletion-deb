"""Track-B n=6 validation (after initial freeze, before final freeze).

Evaluates frozen H-SA02-B-v1 exactly on n=6 forced rows.
If max residual != 0, assigns new hypothesis ID and marks n=6 as development.
"""
import json
import os
import sys
from fractions import Fraction
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining import holdout_firewall as firewall

def evaluate(candidate_id, target_n):
    firewall.hydrate_from_files()
    # Guard: n=6 detailed allowed only after initial freeze (hydrated).
    firewall.guard_initial_fit_load("artifacts/features/n%d/edge_deltas.json.zst" % target_n)
    import zstandard as zstd
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.json" % candidate_id), encoding="utf-8") as f:
        hyp = json.load(f)
    coeffs = hyp["coefficients"]
    with open(os.path.join(REPO, "artifacts", "features", "n%d" % target_n, "edge_deltas.json.zst"), "rb") as f:
        deltas = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    with open(os.path.join(REPO, "artifacts", "certificates", "n%d" % target_n, "bn_certificate.json"), encoding="utf-8") as f:
        cert = json.load(f)
    prime_q = int(cert["b"]["q"])
    worst = Fraction(0)
    worst_row = None
    n_eval = 0
    for row in deltas:
        # Validation for Track B: evaluate on FCYCLE rows (cyclic forcing).
        if "FCYCLE" not in row["provenance"]:
            continue
        n_eval += 1
        pred = sum(Fraction(coeffs.get(k, "0")) * row["delta_F"].get(k, 0) for k in row["delta_F"])
        # Target ell = L/q
        target = Fraction(int(row["scaled_slack"]), prime_q)
        res = abs(pred - target)
        if res > worst:
            worst = res
            worst_row = row
    report = {
        "candidate_id": candidate_id,
        "n": target_n,
        "evaluated_rows": n_eval,
        "exact_max_residual": "%s/%s" % (worst.numerator, worst.denominator),
        "worst_row": ({k: worst_row[k] for k in ("n", "source_state_id", "target_state_id", "mode", "key", "scaled_slack")} if worst_row else None),
        "verdict": "PASS" if worst == 0 else "FAIL",
    }
    outdir = os.path.join(REPO, "artifacts", "validation")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "n%d_%s.json" % (target_n, candidate_id)), "w", encoding="utf-8") as f:
        json.dump(report, f, sort_keys=True, indent=2)
        f.write("\n")
    print("[VALIDATION] %s n=%d rows=%d max_res=%s verdict=%s" % (candidate_id, target_n, n_eval, worst, report["verdict"]))
    return report

if __name__ == "__main__":
    rep = evaluate("H-SA02-B-v1", 6)
    # If FAIL, document that n=6 becomes development info (new ID required for revision).
    if rep["verdict"] == "FAIL":
        print("[VALIDATION] n=6 FAIL -> any revision gets new hypothesis ID; n=6 now development info")
