"""WP-1 stress test (beyond gate suite): n=6 agreement, determinism reruns,
faulty-variant canary proofs. Step-logged. Exit 0 iff all stress checks pass.
"""

import hashlib
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from python.audit import independent_splay, independent_tree  # noqa: E402
from python.reference import enumerate as enum  # noqa: E402
from python.reference import splay as ref_splay  # noqa: E402
from python.reference import tree as ref_tree  # noqa: E402

FAIL = []


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def keyed_shape(t):
    """Erase labels from a reference keyed tree."""
    if t == ():
        return "."
    return "(" + keyed_shape(t[0]) + keyed_shape(t[2]) + ")"


def transition_digest(n, impl="ref"):
    """Hash of all (shape, x) -> after-shape records for size n."""
    recs = []
    for shape in enum.canonical_shapes(n):
        for x in range(1, n + 1):
            if impl == "ref":
                t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shape))
                t2, _, _, _ = ref_splay.splay(t, x)
                recs.append("%s|%d|%s" % (shape, x, keyed_shape(t2)))
            else:
                r = independent_tree.build_tree(independent_tree.parse_shape(shape))
                r2, _, _ = independent_splay.splay(r, x)
                recs.append("%s|%d|%s" % (shape, x, independent_tree.shape_of(r2)))
    return hashlib.sha256(("\n".join(recs) + "\n").encode()).hexdigest(), len(recs)


def faulty_zigzig_splay(t, x):
    """Deliberately wrong LL/RR (rotations in swapped order). Canary only."""
    from python.reference.tree import find_path
    path0 = find_path(t, x)
    cost = len(path0)
    cur = t
    while True:
        path = find_path(cur, x)
        if len(path) == 1:
            break
        v, p = path[-1], path[-2]
        vl = v < p
        if len(path) == 2:
            cur = ref_splay.rotate_right(cur, p) if vl else ref_splay.rotate_left(cur, p)
        else:
            g = path[-3]
            pl = p < g
            if vl and pl:
                cur = ref_splay.rotate_right(cur, p)
                cur = ref_splay.rotate_right(cur, g)
            elif not vl and not pl:
                cur = ref_splay.rotate_left(cur, p)
                cur = ref_splay.rotate_left(cur, g)
            elif not vl and pl:
                cur = ref_splay.rotate_left(cur, p)
                cur = ref_splay.rotate_right(cur, g)
            else:
                cur = ref_splay.rotate_right(cur, p)
                cur = ref_splay.rotate_left(cur, g)
    return cur, cost


def main():
    """Run stress checks. Exit 0 iff all pass."""
    t0 = time.time()
    # console.log equivalent [WP1-S-01]: n=6 two-implementation agreement.
    console_log("WP1-S-01", "n=6 reference vs independent begin")
    d_ref, c_ref = transition_digest(6, "ref")
    d_ind, c_ind = transition_digest(6, "ind")
    ok = d_ref == d_ind and c_ref == c_ind == 792
    console_log("WP1-S-01", "ops=%d match=%s" % (c_ref, ok))
    if not ok:
        FAIL.append("S-N6")
    # console.log equivalent [WP1-S-02]: determinism across clean reruns.
    console_log("WP1-S-02", "clean-rerun determinism begin")
    outs = []
    for _ in range(2):
        r = subprocess.run([sys.executable, os.path.join(REPO, "python", "reference", "enumerate.py"),
                            "--n", "5", "--out",
                            os.path.join(REPO, "artifacts", "trees", "n5")],
                           capture_output=True, text=True)
        if r.returncode != 0:
            FAIL.append("S-RERUN-ENUM")
            break
        outs.append(r.stdout)
    ok = len(outs) == 2 and outs[0] == outs[1]
    console_log("WP1-S-02", "enumerate rerun identical=%s" % ok)
    if not ok:
        FAIL.append("S-RERUN")
    h1, _ = transition_digest(4, "ref")
    h2, _ = transition_digest(4, "ref")
    ok = h1 == h2
    console_log("WP1-S-02", "transition digest stable=%s %s" % (ok, h1[:16]))
    if not ok:
        FAIL.append("S-TRANS")
    # console.log equivalent [WP1-S-03]: faulty-variant canaries must differ.
    console_log("WP1-S-03", "faulty-variant canaries begin")
    t = ref_tree.assign_inorder_keys(ref_tree.parse_shape("(((..).).)"))
    bad, _ = faulty_zigzig_splay(t, 1)
    good, _, _, _ = ref_splay.splay(t, 1)
    ok = keyed_shape(bad) != keyed_shape(good)
    console_log("WP1-S-03", "reversed-zigzig detected=%s" % ok)
    if not ok:
        FAIL.append("S-CANARY-ZZ")
    ok = ref_tree.compute_depth(t, 1) != ref_tree.access_cost(t, 1)
    console_log("WP1-S-03", "depth-cost-offset detected=%s" % ok)
    if not ok:
        FAIL.append("S-CANARY-COST")
    dt = time.time() - t0
    # console.log equivalent [WP1-S-04]: stress summary.
    console_log("WP1-S-04", "stress fail=%d seconds=%.1f" % (len(FAIL), dt))
    logdir = os.path.join(REPO, "artifacts", "logs")
    os.makedirs(logdir, exist_ok=True)
    rec = {"experiment_id": "SPLAY-AM-PD-v0.1", "phase": "WP-1-STRESS",
           "fail": FAIL, "exit": 0 if not FAIL else 1,
           "n6_digest": d_ref, "wall_seconds": round(dt, 1)}
    with open(os.path.join(logdir, "wp1_stress.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
