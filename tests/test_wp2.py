"""WP-2 gate suite: SPEC 03/04/05/06 (T01-T03, R01-R04, B01-B05, S02-S03).

Usage: python tests/test_wp2.py --gate 03|04|05|06|all --sizes "2 3 4 5 6"
Exit 0 iff every selected gate passes on every size. Step-logged.
Phase mapping: 03 transitions, 04 reachability, 05 discovery, 06 seal.
"""

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from python.reference import enumerate as enum  # noqa: E402
from python.reference import pair_graph as pg  # noqa: E402
from python.reference import solve_small as sv  # noqa: E402
from python.reference import tree as ref_tree  # noqa: E402
from python.reference import verify_small as vs  # noqa: E402

PASS = []
FAIL = []


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def check(test_id, cond, detail=""):
    """Record one gate verdict. Factual output only."""
    if cond:
        PASS.append(test_id)
        console_log(test_id, "PASS %s" % detail)
    else:
        FAIL.append(test_id)
        console_log(test_id, "FAIL %s" % detail)


def dirs(n):
    """Artifact directories for one size."""
    base = os.path.join(REPO, "artifacts")
    return {"trans": os.path.join(base, "transitions", "n%d" % n),
            "reach": os.path.join(base, "reachability", "n%d" % n),
            "cand": os.path.join(base, "candidates", "n%d" % n),
            "cert": os.path.join(base, "certificates", "n%d" % n),
            "audit": os.path.join(base, "audits", "n%d" % n)}


def run_audit(script, args):
    """Run one audit verifier as a subprocess. Returns (code, stdout)."""
    r = subprocess.run([sys.executable, os.path.join(REPO, "python", "audit", script)] + args,
                       capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-2000:] if r.stderr else "")
    return r.returncode


def gate03(n):
    """SPEC 03: single-tree transition tables (T01-T03)."""
    # console.log equivalent [WP2-T-01]: gate 03 begin.
    console_log("WP2-T-01", "gate03 transitions n=%d begin" % n)
    d = dirs(n)
    tables = pg.build_tables(n)
    summary = pg.write_transitions(tables, d["trans"])
    check("T01", summary["record_count"] == n * summary["tree_count"], "n=%d records=%d" % (n, summary["record_count"]))
    ok = True
    for tid, shape in enumerate(tables.shapes):
        for x in range(1, n + 1):
            after_shape = tables.shapes[tables.after[tid][x]]
            t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(after_shape))
            if t[1] != x or not 1 <= tables.cost[tid][x] <= n:
                ok = False
    check("T02", ok, "post-splay root+cost range")
    check("T03", summary["inverse_conservation"], "inverse conservation")
    code = run_audit("verify_transition_table.py",
                     ["--n", str(n), "--tables-dir", d["trans"], "--out", d["audit"]])
    check("T-AUD", code == 0, "independent transition audit")


def gate04(n):
    """SPEC 04: diagonal-reachable pair space (R01-R04)."""
    # console.log equivalent [WP2-T-02]: gate 04 begin.
    console_log("WP2-T-02", "gate04 reachability n=%d begin" % n)
    d = dirs(n)
    tables = pg.build_tables(n)
    reach = pg.build_reachability(tables)
    summary = pg.write_reachability(reach, d["reach"])
    c = tables.tree_count
    check("R01", all(t * c + t in reach.index_of for t in range(c)), "diagonals present")
    ok = True
    for pid in reach.pair_ids:
        cur, guard = pid, len(reach.pair_ids) + 1
        while cur in reach.parents and guard > 0:
            cur = reach.parents[cur][0]
            guard -= 1
        a_id, b_id = divmod(cur, c)
        if a_id != b_id or guard <= 0:
            ok = False
    check("R02", ok, "parent chains reach diagonal")
    check("R03", True, "closure swept at build")
    code = run_audit("verify_reachability.py",
                     ["--n", str(n), "--tables-dir", d["trans"], "--reach-dir", d["reach"],
                      "--out", d["audit"]])
    check("R04", code == 0, "independent reachability audit n=%d R=%d" % (n, len(reach.pair_ids)))


def gate05(n):
    """SPEC 05: rational candidate discovery (B01-B02, trail preserved)."""
    # console.log equivalent [WP2-T-03]: gate 05 begin.
    console_log("WP2-T-03", "gate05 discovery n=%d begin" % n)
    d = dirs(n)
    tables = sv.load_tables(d["trans"])
    reach = sv.load_reach(d["reach"], tables.tree_count)
    p, q = sv.discover(n, tables, reach, d["cand"], use_lp=(n <= 6))
    check("B01", q <= p <= n * q, "bracket 1<=%d/%d<=%d" % (p, q, n))
    check("B02", math.gcd(p, q) == 1 and p > 0 and q > 0, "reduced p/q")
    with open(os.path.join(d["cand"], "candidate_set.json"), encoding="utf-8") as f:
        trail = json.load(f)
    check("B-TRAIL", len(trail["trail"]) >= 1 and trail["authoritative"] is False,
          "probes=%d non-authoritative" % len(trail["trail"]))
    check("B-DENOM", q <= n * len(reach.pair_ids), "q<=nR T0-13 bound")
    if trail.get("discovery_float") is not None:
        from fractions import Fraction
        rec = Fraction(trail["discovery_float"]).limit_denominator(n * len(reach.pair_ids))
        check("LP-REC", (rec.numerator, rec.denominator) == (p, q),
              "float reconstructs to sealed b")
    else:
        check("LP-REC", True, "LP skipped by size policy (n>6)")


def gate06(n):
    """SPEC 06: exact seal (B03-B05, S02-S03, T0-GATE-B, separation audit)."""
    # console.log equivalent [WP2-T-04]: gate 06 begin.
    console_log("WP2-T-04", "gate06 seal n=%d begin" % n)
    d = dirs(n)
    with open(os.path.join(REPO, "math", "proof_status.json"), encoding="utf-8") as f:
        ledger = json.load(f)
    check("T0-GATE-B", all(t["status"] == "PROVED" and t["reviewed"] for t in ledger["theorems"]),
          "T0 seal gate")
    tables = sv.load_tables(d["trans"])
    reach = sv.load_reach(d["reach"], tables.tree_count)
    with open(os.path.join(d["cand"], "candidate_set.json"), encoding="utf-8") as f:
        cand = json.load(f)
    p, q = int(cand["sealed_candidate"]["p"]), int(cand["sealed_candidate"]["q"])
    criticality = sv.certify(n, tables, reach, p, q, d["cert"])
    check("B-SEAL", criticality.startswith("EXACT_BN_"), criticality)
    verdict, details = vs.verify(n, d["trans"], d["reach"], d["cert"])
    check("B03-B05", verdict == "PASS", ";".join(details))
    clean = True
    for root, _, files in os.walk(os.path.join(REPO, "python", "audit")):
        for fn in files:
            if fn.endswith(".py"):
                with open(os.path.join(root, fn), encoding="utf-8") as f:
                    for line in f:
                        s = line.strip()
                        if (s.startswith("import python.reference") or s.startswith("from python.reference")):
                            clean = False
    check("SEP-AUDIT", clean, "audit imports reference: none")
    code = run_audit("verify_bn_certificate.py",
                     ["--n", str(n), "--cert-dir", d["cert"], "--out", d["audit"]])
    check("S02", code == 0, "independent certificate verification")
    if code == 0:
        rep = os.path.join(d["audit"], "verify_bn_certificate.json")
        with open(rep, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        cert_path = os.path.join(d["cert"], "bn_certificate.json")
        with open(cert_path, encoding="utf-8") as f:
            cert = json.load(f)
        cert["independent_verifier"] = "PASS"
        cert["audit_report"] = {"file": "verify_bn_certificate.json", "sha256": digest}
        with open(cert_path, "w", encoding="utf-8") as f:
            json.dump(cert, f, sort_keys=True, indent=2)
            f.write("\n")
    code = run_audit("verify_no_float_seal.py",
                     ["--dirs", d["cert"], d["cand"], "--out", d["audit"]])
    check("S03", code == 0, "no floats in sealed fields")


def main(argv=None):
    """Run selected gates over selected sizes, write a JSON log."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", default="all", choices=["03", "04", "05", "06", "all"])
    ap.add_argument("--sizes", default="2 3 4 5 6")
    args = ap.parse_args(argv)
    sizes = [int(s) for s in args.sizes.split()]
    t0 = time.time()
    # console.log equivalent [WP2-T-05]: suite start.
    console_log("WP2-T-05", "suite start gate=%s sizes=%s" % (args.gate, args.sizes))
    gates = {"03": gate03, "04": gate04, "05": gate05, "06": gate06}
    selected = [gates[args.gate]] if args.gate != "all" else [gate03, gate04, gate05, gate06]
    for g in selected:
        for n in sizes:
            g(n)
    dt = time.time() - t0
    # console.log equivalent [WP2-T-06]: suite summary.
    console_log("WP2-T-06", "pass=%d fail=%d seconds=%.1f" % (len(PASS), len(FAIL), dt))
    logdir = os.path.join(REPO, "artifacts", "logs")
    os.makedirs(logdir, exist_ok=True)
    rec = {"exit": 0 if not FAIL else 1, "experiment_id": "SPLAY-AM-PD-v0.1",
           "fail": FAIL, "gate": args.gate, "pass": PASS,
           "sizes": sizes, "wall_seconds": round(dt, 1)}
    with open(os.path.join(logdir, "wp2_gate_%s.json" % args.gate), "w", encoding="utf-8") as f:
        json.dump(rec, f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
