"""WP-5 symbolic candidate freezing (SPEC 12 entry point; delegates to wp5 package).

This module exists to satisfy the WorkPlan §7 file layout
(`python/mining/symbolic_candidates.py`); all freezing logic lives in
`python/wp5/candidates.py` (single implementation, no duplication).
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-SYN-10]: symbolic-candidate entrypoint loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def main(argv=None):
    """Freeze ERA-B universal hypotheses (delegates; no holdout contact)."""
    # console.log equivalent [WP5-SYN-11]: delegation to wp5 candidates.
    console_log("WP5-SYN-11", "delegating to python/wp5/candidates.py")
    from python.wp5 import candidates as C
    return C.main(argv)


if __name__ == "__main__":
    sys.exit(main())
