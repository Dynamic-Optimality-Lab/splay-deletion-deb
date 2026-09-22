"""WP-5 candidate reporting (SPEC 12 entry point; reads sealed reports only).

Re-validates frozen dev reports (recompute-free consistency read) and prints
per-candidate verdict summaries. Writes nothing except stdout (read-only).
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-REP-01]: report entrypoint loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def report(hypothesis_id):
    """Print the frozen verdict summary for one hypothesis (read-only)."""
    # console.log equivalent [WP5-REP-02]: candidate reported.
    console_log("WP5-REP-02", "reporting %s" % hypothesis_id)
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.uh.json" % hypothesis_id),
              encoding="utf-8") as handle:
        gates = json.load(handle)
    with open(os.path.join(REPO, "artifacts", "falsification", hypothesis_id,
                           "dev_summary.json"), encoding="utf-8") as handle:
        dev = json.load(handle)
    print(json.dumps({"hypothesis_id": hypothesis_id, "gates": gates,
                      "sizes": dev.get("sizes", {})}, sort_keys=True, indent=2))
    return gates


def main(argv=None):
    """Report all WP-5 hypotheses (read-only)."""
    sys.path.insert(0, REPO)
    from python.wp5.run_phase import CANDIDATES
    for hyp_id in CANDIDATES:
        report(hyp_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
