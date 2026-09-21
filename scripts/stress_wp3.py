"""WP-3 stress test: rebuild determinism + audit repeat stability.

- Rebuilds U/V/G + critical geometry for n<=5 via fresh in-process runs and
  compares summary hashes against sealed artifacts (determinism).
- Re-runs the independent critical audit for n=4 (largest fast cyclic size).
Exit 0 iff all stress checks pass. Step-logged.
"""

import hashlib
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

FAIL = []


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def file_sha(path):
    """SHA-256 of a file."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    """Run stress checks. Exit 0 iff all pass."""
    t0 = time.time()
    # console.log equivalent [WP3-S-01]: rebuild determinism begin.
    console_log("WP3-S-01", "rebuild determinism n<=5 begin")
    from python.reference import canonical as cn
    from python.reference import critical as cr
    from python.reference import solve_small as sv
    for n in (2, 3, 4, 5):
        d = {"trans": os.path.join(REPO, "artifacts", "transitions", "n%d" % n),
             "reach": os.path.join(REPO, "artifacts", "reachability", "n%d" % n),
             "cert": os.path.join(REPO, "artifacts", "certificates", "n%d" % n)}
        tables = sv.load_tables(d["trans"])
        reach = sv.load_reach(d["reach"], tables.tree_count)
        with open(os.path.join(d["cert"], "bn_certificate.json"), encoding="utf-8") as f:
            cert = json.load(f)
        p, q = int(cert["b"]["p"]), int(cert["b"]["q"])
        csr = sv.build_csr(tables, reach)
        U, _ = cn.compute_U(csr, p, q)
        V, _ = cn.compute_V(csr, p, q)
        import tempfile
        tmp = tempfile.mkdtemp(prefix="wp3stress_")
        cn.build_potentials(n, tables, reach, p, q, os.path.join(tmp, "pot"))
        cr.build_critical(n, tables, reach, p, q, U, V, os.path.join(tmp, "crit"))
        ok = True
        for a, b in (("potentials", "summary.json"), ("critical", "summary.json")):
            x = file_sha(os.path.join(REPO, "artifacts", a, "n%d" % n, b))
            y = file_sha(os.path.join(tmp, "pot" if a == "potentials" else "crit", b))
            if x != y:
                ok = False
        console_log("WP3-S-01", "n=%d summaries identical=%s" % (n, ok))
        if not ok:
            FAIL.append("S-REBUILD-%d" % n)
    # console.log equivalent [WP3-S-02]: audit repeat stability.
    console_log("WP3-S-02", "audit repeat n=4 begin")
    d = {"cert": os.path.join(REPO, "artifacts", "certificates", "n4"),
         "pot": os.path.join(REPO, "artifacts", "potentials", "n4"),
         "crit": os.path.join(REPO, "artifacts", "critical", "n4"),
         "audit": os.path.join(REPO, "artifacts", "audits", "n4")}
    r = subprocess.run([sys.executable, os.path.join(REPO, "python", "audit", "verify_critical_objects.py"),
                        "--n", "4", "--cert-dir", d["cert"], "--pot-dir", d["pot"],
                        "--crit-dir", d["crit"], "--out", d["audit"]],
                       capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    ok = r.returncode == 0
    console_log("WP3-S-02", "audit repeat PASS=%s" % ok)
    if not ok:
        FAIL.append("S-AUDIT")
    dt = time.time() - t0
    # console.log equivalent [WP3-S-03]: stress summary.
    console_log("WP3-S-03", "stress fail=%d seconds=%.1f" % (len(FAIL), dt))
    logdir = os.path.join(REPO, "artifacts", "logs")
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, "wp3_stress.json"), "w", encoding="utf-8") as f:
        json.dump({"exit": 0 if not FAIL else 1, "experiment_id": "SPLAY-AM-PD-v0.1",
                   "fail": FAIL, "wall_seconds": round(dt, 1)}, f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
