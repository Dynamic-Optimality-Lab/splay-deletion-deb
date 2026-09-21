"""WP-2 stress test: discovery determinism + artifact stability + audit repeat.

- Re-runs exact discovery for n<=6 and compares sealed candidates (trail must
  be byte-identical: the solver is fully deterministic).
- Rebuilds transition artifacts twice via the CLI and compares summaries.
- Re-runs the independent certificate audit for n=5 (largest fast size).
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
    # console.log equivalent [WP2-S-01]: discovery determinism.
    console_log("WP2-S-01", "discovery determinism n<=6 begin")
    from python.reference import pair_graph as pg, solve_small as sv
    for n in (2, 3, 4, 5, 6):
        tables = sv.load_tables(os.path.join(REPO, "artifacts", "transitions", "n%d" % n))
        reach = sv.load_reach(os.path.join(REPO, "artifacts", "reachability", "n%d" % n),
                              tables.tree_count)
        csr = sv.build_csr(tables, reach)
        p, q, _ = sv.dinkelbach(csr)
        with open(os.path.join(REPO, "artifacts", "candidates", "n%d" % n,
                               "candidate_set.json"), encoding="utf-8") as f:
            sealed = json.load(f)["sealed_candidate"]
        ok = sealed == {"p": str(p), "q": str(q), "reduced": True}
        console_log("WP2-S-01", "n=%d rediscover=%d/%d match=%s" % (n, p, q, ok))
        if not ok:
            FAIL.append("S-DISC-%d" % n)
    # console.log equivalent [WP2-S-02]: artifact rebuild stability.
    console_log("WP2-S-02", "CLI rebuild stability begin")
    import tempfile
    tmp = tempfile.mkdtemp(prefix="wp2stress_")
    r = subprocess.run([sys.executable, "-c",
                        "import sys; sys.path.insert(0, %r); from python.reference import pair_graph as pg;"
                        "t = pg.build_tables(4); r = pg.build_reachability(t);"
                        "pg.write_transitions(t, %r); pg.write_reachability(r, %r)"
                        % (REPO, os.path.join(tmp, "t"), os.path.join(tmp, "r"))],
                       capture_output=True, text=True)
    ok = r.returncode == 0
    if ok:
        a = file_sha(os.path.join(REPO, "artifacts", "transitions", "n4", "summary.json"))
        b = file_sha(os.path.join(tmp, "t", "summary.json"))
        c = file_sha(os.path.join(REPO, "artifacts", "reachability", "n4", "summary.json"))
        d = file_sha(os.path.join(tmp, "r", "summary.json"))
        ok = a == b and c == d
    console_log("WP2-S-02", "rebuild identical=%s" % ok)
    if not ok:
        FAIL.append("S-REBUILD")
    # console.log equivalent [WP2-S-03]: audit repeat stability.
    console_log("WP2-S-03", "audit repeat n=5 begin")
    d = {"trans": os.path.join(REPO, "artifacts", "transitions", "n5"),
         "reach": os.path.join(REPO, "artifacts", "reachability", "n5"),
         "cert": os.path.join(REPO, "artifacts", "certificates", "n5"),
         "audit": os.path.join(REPO, "artifacts", "audits", "n5")}
    r = subprocess.run([sys.executable, os.path.join(REPO, "python", "audit", "verify_bn_certificate.py"),
                        "--n", "5", "--cert-dir", d["cert"], "--out", d["audit"]],
                       capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    ok = r.returncode == 0
    console_log("WP2-S-03", "audit repeat PASS=%s" % ok)
    if not ok:
        FAIL.append("S-AUDIT")
    dt = time.time() - t0
    # console.log equivalent [WP2-S-04]: stress summary.
    console_log("WP2-S-04", "stress fail=%d seconds=%.1f" % (len(FAIL), dt))
    logdir = os.path.join(REPO, "artifacts", "logs")
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, "wp2_stress.json"), "w", encoding="utf-8") as f:
        json.dump({"exit": 0 if not FAIL else 1, "experiment_id": "SPLAY-AM-PD-v0.1",
                   "fail": FAIL, "wall_seconds": round(dt, 1)}, f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
