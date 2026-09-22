"""Freeze final Track-B candidate before n=7 (no coefficient change)."""
import hashlib
import json
import os
import sys
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining import holdout_firewall as firewall

def main():
    base = os.path.join(REPO, "artifacts", "hypotheses")
    with open(os.path.join(base, "H-SA02-B-v1.json"), encoding="utf-8") as f:
        v1 = json.load(f)
    with open(os.path.join(REPO, "artifacts", "validation", "n6_H-SA02-B-v1.json"), encoding="utf-8") as f:
        v6 = json.load(f)
    final = dict(v1)
    final["hypothesis_id"] = "H-SA02-B-v1-final"
    final["parent_hypothesis"] = "H-SA02-B-v1"
    final["status"] = "FROZEN-FINAL (before n7 reveal; n6 validation FAIL max_res=5, no coefficient change so n6 remains validation)"
    final["n6_validation"] = v6
    blob = (json.dumps({k: v for k, v in final.items() if k != "sha256"}, sort_keys=True) + "\n").encode("utf-8")
    final["sha256"] = hashlib.sha256(blob).hexdigest()
    with open(os.path.join(base, "H-SA02-B-v1-final.json"), "w", encoding="utf-8") as f:
        json.dump(final, f, sort_keys=True, indent=2)
        f.write("\n")
    # Ledger.
    with open(os.path.join(base, "hypothesis_ledger.json"), encoding="utf-8") as f:
        ledger = json.load(f)
    ledger["hypotheses"].append({"hypothesis_id": final["hypothesis_id"], "sha256": final["sha256"],
                                 "status": final["status"], "definition": final["definition"]})
    with open(os.path.join(base, "hypothesis_ledger.json"), "w", encoding="utf-8") as f:
        json.dump(ledger, f, sort_keys=True, indent=2)
        f.write("\n")
    # Firewall: need initial in memory before final.
    firewall.hydrate_from_files()
    # Hydrate sets initial from disk? Our hydrate sets initial if file exists.
    # Ensure in-memory initial set (in case hydrate not called in this process before).
    try:
        firewall.freeze_initial_candidate("H-SA02-B-v1")
    except Exception:
        pass
    firewall.freeze_final_candidate("H-SA02-B-v1-final")
    print("[FREEZE-FINAL] H-SA02-B-v1-final sha=%s" % final["sha256"][:16])

if __name__ == "__main__":
    main()
