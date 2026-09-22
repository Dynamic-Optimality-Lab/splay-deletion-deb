"""Freeze Track-B initial candidate (after n=4,5 fit, before n=6 reveal)."""
import hashlib
import json
import os
import sys
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining import holdout_firewall as firewall

def main():
    base = os.path.join(REPO, "artifacts", "hypotheses")
    os.makedirs(base, exist_ok=True)
    with open(os.path.join(base, "track_b_linear_report.json"), encoding="utf-8") as f:
        rep = json.load(f)
    sol = rep["solution_family"]
    order = rep["feature_order"]
    coeffs = {k: v for k, v in zip(order, sol) if v != "0"}
    # Definition string (mathematical, answer-independent features only).
    terms = ["(%s)*%s" % (v, k) for k, v in zip(order, sol) if v != "0"]
    definition = "H_B_v1 = " + " + ".join(terms)
    hyp = {
        "hypothesis_id": "H-SA02-B-v1",
        "parent_hypothesis": None,
        "definition": definition,
        "coefficients": coeffs,
        "coefficient_domain": "rationals-particular-dense (linear exact over Q; sparse integer [-2,2] support<=2 fails with residual 4/5)",
        "state_only": True,
        "uses_history": False,
        "uses_b_n_star_table": False,
        "discovery_sizes": [4, 5],
        "heldout_sizes": [6, 7],
        "status": "FROZEN-INITIAL (before n6 reveal)",
        "dataset_sha256": rep["dataset_sha256"],
        "linear_report": "track_b_linear_report.json",
    }
    blob = (json.dumps(hyp, sort_keys=True) + "\n").encode("utf-8")
    hyp["sha256"] = hashlib.sha256(blob).hexdigest()
    with open(os.path.join(base, "H-SA02-B-v1.json"), "w", encoding="utf-8") as f:
        json.dump(hyp, f, sort_keys=True, indent=2)
        f.write("\n")
    # Ledger.
    ledger_path = os.path.join(base, "hypothesis_ledger.json")
    if os.path.exists(ledger_path):
        with open(ledger_path, encoding="utf-8") as f:
            ledger = json.load(f)
    else:
        ledger = {"hypotheses": []}
    ledger["hypotheses"] = [h for h in ledger["hypotheses"] if h["hypothesis_id"] != "H-SA02-B-v1"]
    ledger["hypotheses"].append({"hypothesis_id": "H-SA02-B-v1", "sha256": hyp["sha256"],
                                 "status": hyp["status"], "definition": definition})
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, sort_keys=True, indent=2)
        f.write("\n")
    firewall.freeze_initial_candidate("H-SA02-B-v1")
    print("[FREEZE-INITIAL] H-SA02-B-v1 sha=%s" % hyp["sha256"][:16])
    print(definition)

if __name__ == "__main__":
    main()
