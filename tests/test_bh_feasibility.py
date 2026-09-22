"""UH-3 b_H-feasibility suite: BH01-BH05 (SA-01 mandatory coverage).

BH01 exact b_H >= b_n* comparison for every certified n.
BH02 b_H < b_n* witness branches: transient_path, cycle, prefix_plus_cycles
     (verifier-recomputed negative slack, minimal k stored).
BH03 b_H == b_n* three-case equality branch (table-reuse decision).
BH04 b_H > b_n* recomputed U_bH,V_bH satisfy canonical inequalities (n=2
     machinery proof to temp dir; full-scale tables materialize for survivors).
BH05 independent verifier agrees on the b_H geometry (audit-side, n=2).
Exact integer arithmetic throughout; no floats.
"""
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

PASS = []
FAIL = []


# console.log equivalent [WP5-T-BH-00]: suite started.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def check(test_id, cond, detail=""):
    """Record one gate verdict. Factual output only."""
    if cond:
        PASS.append(test_id)
        console_log(test_id, "PASS %s" % detail)
    else:
        FAIL.append(test_id)
        console_log(test_id, "FAIL %s" % detail)


def sealed_b(n):
    """Sealed (p, q) for size n."""
    with open(os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                           "bn_certificate.json"), encoding="utf-8") as handle:
        cert = json.load(handle)
    return int(cert["b"]["p"]), int(cert["b"]["q"])


def bh01():
    """BH01: exact b_H >= b_n* per certified n (b_H = 2/1 production value)."""
    # console.log equivalent [WP5-T-BH-01]: BH01 begin.
    console_log("WP5-T-BH-01", "BH01 exact comparisons begin")
    from python.wp5 import candidates as C
    ok = True
    for n in (2, 3, 4, 5, 6, 7):
        p_n, q_n = sealed_b(n)
        if not (2 * q_n >= p_n * 1):
            ok = False
        recs = C.uh3_records("H-0001", 2, 1)
        rec = [r for r in recs if r["n"] == n][0]
        if rec["verdict"] != "PASS" or rec["failure_witness"] is not None:
            ok = False
    check("BH01", ok, "b_H=2/1 feasible on n=2..7")


def bh02():
    """BH02: all three witness branches with verifier-recomputed slack."""
    # console.log equivalent [WP5-T-BH-02]: BH02 begin.
    console_log("WP5-T-BH-02", "BH02 witness branches begin")
    from python.wp5 import candidates as C
    # Transient branch: n=2 (MIXED seal carries a path witness), b_H = 1/2.
    assert C.bh_case(1, 2, 1, 1) == "<"
    wit = C.build_bh_witness_below("H-TEST", 1, 2, 2)
    check("BH02-transient", wit["witness_kind"] == "transient_path"
          and int(wit["slack_under_bH_num"]) < 0 and wit["negative"]
          and wit["repeat_count"] is None, "n=2 path slack=%s" % wit["slack_under_bH_num"])
    # Cyclic branch: n=4, b_H = 1/1 < 3/2.
    assert C.bh_case(1, 1, 3, 2) == "<"
    wit = C.build_bh_witness_below("H-TEST", 1, 1, 4)
    check("BH02-cycle", wit["witness_kind"] == "cycle"
          and int(wit["slack_under_bH_num"]) < 0 and wit["negative"], "n=4 cycle slack=%s" % wit["slack_under_bH_num"])
    # Prefix-plus-cycles branch: same infeasible point, minimal k stored.
    wit = C.build_prefix_plus_cycles(1, 1, 4)
    check("BH02-prefix", wit["witness_kind"] == "prefix_plus_cycles"
          and int(wit["repeat_count"]) >= 1 and int(wit["slack_under_bH_num"]) < 0
          and wit["negative"], "n=4 k=%s slack=%s" % (wit["repeat_count"], wit["slack_under_bH_num"]))


def bh03():
    """BH03: equality branch selects table reuse (byte/hash-consistent rule)."""
    # console.log equivalent [WP5-T-BH-03]: BH03 begin.
    console_log("WP5-T-BH-03", "BH03 equality branch begin")
    from python.wp5 import candidates as C
    check("BH03", C.bh_case(8, 5, 8, 5) == "=" and C.bh_case(2, 1, 1, 1) == ">"
          and C.bh_case(1, 1, 3, 2) == "<", "three-case rule exact")


def bh04_bh05():
    """BH04/BH05: n=2 b_H-table recomputation + independent agreement (machinery
    proof to temp dir; full-scale tables materialize for UH survivors)."""
    # console.log equivalent [WP5-T-BH-04]: BH04/BH05 begin.
    console_log("WP5-T-BH-04", "BH04/BH05 n=2 machinery proof begin")
    from python.wp5 import run_verify as V
    tmp = tempfile.mkdtemp(prefix="wp5_bh_")
    V.build_bh_tables(2, 1, (2,), out_root=tmp)
    with open(os.path.join(tmp, "n2", "audit", "verify_bh_tables.json"),
              encoding="utf-8") as handle:
        rep = json.load(handle)
    check("BH04", rep["checks"]["inequalities"] and rep["checks"]["values"]
          and rep["verdict"] == "PASS", "recomputed tables satisfy canonical form")
    check("BH05", rep["checks"]["bellman_U"] and rep["checks"]["bellman_V"]
          and rep["verdict"] == "PASS", "independent verifier agrees")


def main(argv=None):
    """Run the BH suite, write a JSON log."""
    import argparse
    import time
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", default="all", choices=["BH", "all"])
    ap.parse_args(argv)
    t0 = time.time()
    # console.log equivalent [WP5-T-BH-05]: suite start.
    console_log("WP5-T-BH-05", "BH suite start")
    bh01()
    bh02()
    bh03()
    bh04_bh05()
    dt = time.time() - t0
    # console.log equivalent [WP5-T-BH-06]: suite summary.
    console_log("WP5-T-BH-06", "pass=%d fail=%d seconds=%.1f" % (len(PASS), len(FAIL), dt))
    logdir = os.path.join(REPO, "artifacts", "logs")
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, "wp5_bh.json"), "w", encoding="utf-8") as handle:
        json.dump({"experiment_id": "SPLAY-AM-PD-v0.1", "exit": 0 if not FAIL else 1,
                   "fail": FAIL, "gate": "BH", "pass": PASS,
                   "wall_seconds": round(dt, 1)}, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
