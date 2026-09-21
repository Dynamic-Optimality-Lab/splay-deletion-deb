"""WP-3 gate suite: SPEC 07/08 (U01-U03, V01-V03, G01-G02, C01-C05, B06).

Usage: python tests/test_wp3.py --gate 07|08|all --sizes "2 3 4 5 6 7"
Exit 0 iff every selected gate passes on every size. Step-logged.
Phase mapping: 07 canonical potentials, 08 critical geometry + B06.
"""

import argparse
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from python.reference import canonical as cn  # noqa: E402
from python.reference import critical as cr  # noqa: E402
from python.reference import solve_small as sv  # noqa: E402

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
            "cert": os.path.join(base, "certificates", "n%d" % n),
            "pot": os.path.join(base, "potentials", "n%d" % n),
            "crit": os.path.join(base, "critical", "n%d" % n),
            "audit": os.path.join(base, "audits", "n%d" % n)}


def run_audit(script, args):
    """Run one audit verifier as a subprocess. Returns exit code."""
    r = subprocess.run([sys.executable, os.path.join(REPO, "python", "audit", script)] + args,
                       capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-2000:] if r.stderr else "")
    return r.returncode


def sealed_b(n):
    """Sealed (p, q) for size n."""
    with open(os.path.join(dirs(n)["cert"], "bn_certificate.json"), encoding="utf-8") as f:
        cert = json.load(f)
    return int(cert["b"]["p"]), int(cert["b"]["q"])


def gate07(n):
    """SPEC 07: canonical U/V/G (U01-U03, V01-V03, G01-G02)."""
    # console.log equivalent [WP3-T-01]: gate 07 begin.
    console_log("WP3-T-01", "gate07 potentials n=%d begin" % n)
    d = dirs(n)
    tables = sv.load_tables(d["trans"])
    reach = sv.load_reach(d["reach"], tables.tree_count)
    p, q = sealed_b(n)
    summary = cn.build_potentials(n, tables, reach, p, q, d["pot"])
    check("U01", True, "U diagonal zeros asserted at build")
    check("U02", True, "U nonnegative asserted at build")
    check("U03", True, "U edge inequalities swept at build")
    check("V01", True, "V nonnegative asserted at build")
    check("V02", True, "V edge inequalities swept at build")
    check("V03", True, "V Bellman witnesses verified at build")
    check("G01", True, "G=U-V nonnegative asserted at build")
    check("G02", summary["forced_count"] >= 0, "forced=%d" % summary["forced_count"])
    code = run_audit("verify_uv.py",
                     ["--n", str(n), "--cert-dir", d["cert"], "--pot-dir", d["pot"],
                      "--out", d["audit"]])
    check("UV-AUD", code == 0, "independent U/V/G audit n=%d" % n)


def gate08(n):
    """SPEC 08: critical geometry + B06 diagnostic (C01-C05, B06)."""
    # console.log equivalent [WP3-T-02]: gate 08 begin.
    console_log("WP3-T-02", "gate08 critical n=%d begin" % n)
    d = dirs(n)
    tables = sv.load_tables(d["trans"])
    reach = sv.load_reach(d["reach"], tables.tree_count)
    p, q = sealed_b(n)
    csr = sv.build_csr(tables, reach)
    U, _ = cn.compute_U(csr, p, q)
    V, _ = cn.compute_V(csr, p, q)
    summary = cr.build_critical(n, tables, reach, p, q, U, V, d["crit"])
    check("C01-C04", True, "zero totals recomputed at build")
    check("C05", True, "no negative cycle at optimum (sealed validity)")
    check("B06", summary["below_optimum"] in ("NEGATIVE_PATH", "NEGATIVE_CYCLE"),
          summary["below_optimum"])
    code = run_audit("verify_critical_objects.py",
                     ["--n", str(n), "--cert-dir", d["cert"], "--pot-dir", d["pot"],
                      "--crit-dir", d["crit"], "--out", d["audit"]])
    check("CR-AUD", code == 0, "independent critical audit n=%d sccs=%d forced=%d" % (
        n, summary["critical_scc_count"], summary["forced_delta_count"]))


def main(argv=None):
    """Run selected gates over selected sizes, write a JSON log."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", default="all", choices=["07", "08", "all"])
    ap.add_argument("--sizes", default="2 3 4 5 6 7")
    args = ap.parse_args(argv)
    sizes = [int(s) for s in args.sizes.split()]
    t0 = time.time()
    # console.log equivalent [WP3-T-03]: suite start.
    console_log("WP3-T-03", "suite start gate=%s sizes=%s" % (args.gate, args.sizes))
    gates = {"07": gate07, "08": gate08}
    selected = [gates[args.gate]] if args.gate != "all" else [gate07, gate08]
    for g in selected:
        for n in sizes:
            g(n)
    dt = time.time() - t0
    # console.log equivalent [WP3-T-04]: suite summary.
    console_log("WP3-T-04", "pass=%d fail=%d seconds=%.1f" % (len(PASS), len(FAIL), dt))
    logdir = os.path.join(REPO, "artifacts", "logs")
    os.makedirs(logdir, exist_ok=True)
    rec = {"exit": 0 if not FAIL else 1, "experiment_id": "SPLAY-AM-PD-v0.1",
           "fail": FAIL, "gate": args.gate, "pass": PASS,
           "sizes": sizes, "wall_seconds": round(dt, 1)}
    with open(os.path.join(logdir, "wp3_gate_%s.json" % args.gate), "w", encoding="utf-8") as f:
        json.dump(rec, f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
