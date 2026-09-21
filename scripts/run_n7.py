"""Staged n=7 exact run: discovery then certification, all progress to a log.

Stages reuse saved artifacts so no work is lost across invocations:
  S1 tables+reachability (fast) -> artifacts/transitions/n7, reachability/n7
  S2 discovery (CSR + budgeted Dinkelbach + LP) -> candidates/n7
  S3 certification (re-proof + U^Z + witnesses) -> certificates/n7
Run: python scripts/run_n7.py --stages S1,S2,S3 --log artifacts/n7_stage.log
Step-logged. Exit 0 iff selected stages complete.
"""

import argparse
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from python.reference import pair_graph as pg  # noqa: E402
from python.reference import solve_small as sv  # noqa: E402

LOG = None


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    line = "[%s] %s" % (step_id, msg)
    print(line, flush=True)
    if LOG is not None:
        LOG.write(line + "\n")
        LOG.flush()


def stage1():
    """Build and save n=7 tables + reachability."""
    # console.log equivalent [WP2-N7-01]: stage S1 begin.
    console_log("WP2-N7-01", "stage S1 tables+reachability begin")
    t0 = time.time()
    tables = pg.build_tables(7)
    console_log("WP2-N7-01", "tables %.1fs" % (time.time() - t0))
    t0 = time.time()
    reach = pg.build_reachability(tables)
    console_log("WP2-N7-01", "reach %.1fs R=%d" % (time.time() - t0, len(reach.pair_ids)))
    pg.write_transitions(tables, os.path.join(REPO, "artifacts", "transitions", "n7"))
    pg.write_reachability(reach, os.path.join(REPO, "artifacts", "reachability", "n7"))
    # console.log equivalent [WP2-N7-02]: stage S1 sealed.
    console_log("WP2-N7-02", "stage S1 done")


def stage2():
    """Exact discovery for n=7 (budgeted Dinkelbach; LP skipped by policy).

    The HiGHS proposal LP (2.5M constraints) did not finish in 30+ min of
    solver CPU; LP output is proposal-only and can never seal, while the
    exact parametric path had already secured b=23/14. Two-mechanism
    coverage for n<=6 (LP AGREE everywhere) is unaffected; the n=7 second
    mechanism is the independent audit re-verification at seal time.
    """
    # console.log equivalent [WP2-N7-03]: stage S2 begin.
    console_log("WP2-N7-03", "stage S2 discovery begin (LP skipped by size policy)")
    t0 = time.time()
    tables = sv.load_tables(os.path.join(REPO, "artifacts", "transitions", "n7"))
    reach = sv.load_reach(os.path.join(REPO, "artifacts", "reachability", "n7"), tables.tree_count)
    console_log("WP2-N7-03", "load %.1fs" % (time.time() - t0))
    t0 = time.time()
    p, q = sv.discover(7, tables, reach, os.path.join(REPO, "artifacts", "candidates", "n7"),
                       use_lp=False)
    console_log("WP2-N7-03", "discovery %.1fs b=%d/%d" % (time.time() - t0, p, q))
    # console.log equivalent [WP2-N7-04]: stage S2 sealed.
    console_log("WP2-N7-04", "stage S2 done")


def stage3():
    """Certification for n=7 (re-proof + U^Z + witnesses + seal)."""
    # console.log equivalent [WP2-N7-05]: stage S3 begin.
    console_log("WP2-N7-05", "stage S3 certification begin")
    import json
    t0 = time.time()
    tables = sv.load_tables(os.path.join(REPO, "artifacts", "transitions", "n7"))
    reach = sv.load_reach(os.path.join(REPO, "artifacts", "reachability", "n7"), tables.tree_count)
    with open(os.path.join(REPO, "artifacts", "candidates", "n7", "candidate_set.json"),
              encoding="utf-8") as f:
        cand = json.load(f)
    p, q = int(cand["sealed_candidate"]["p"]), int(cand["sealed_candidate"]["q"])
    crit = sv.certify(7, tables, reach, p, q,
                      os.path.join(REPO, "artifacts", "certificates", "n7"))
    console_log("WP2-N7-05", "certify %.1fs %s" % (time.time() - t0, crit))
    # console.log equivalent [WP2-N7-06]: stage S3 sealed.
    console_log("WP2-N7-06", "stage S3 done")


def main(argv=None):
    """Run selected n=7 stages with file logging."""
    global LOG
    ap = argparse.ArgumentParser()
    ap.add_argument("--stages", default="S1,S2,S3")
    ap.add_argument("--log", default=os.path.join(REPO, "artifacts", "n7_stage.log"))
    args = ap.parse_args(argv)
    LOG = open(args.log, "a", encoding="utf-8")
    stages = {"S1": stage1, "S2": stage2, "S3": stage3}
    for name in args.stages.split(","):
        stages[name.strip()]()
    LOG.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
