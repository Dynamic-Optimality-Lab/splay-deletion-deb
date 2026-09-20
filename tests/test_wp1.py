"""WP-1 gate suite: SPEC 00/01/02 (M01-M06, E01-E03) plus canary tests.

Usage: python tests/test_wp1.py [--gate 00|01|02|all]
Exit code 0 iff every selected gate passes. Step-logged for Path.md.
Deterministic: no randomness, no wall-clock dependence in verdicts.
"""

import argparse
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
from python.reference import functional_splay as func  # noqa: E402
from python.reference import splay as ref_splay  # noqa: E402
from python.reference import tree as ref_tree  # noqa: E402

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


def keyed_shape(t):
    """Erase labels from a reference keyed tree."""
    if t == ():
        return "."
    return "(" + keyed_shape(t[0]) + keyed_shape(t[2]) + ")"


def ref_run(shape, x):
    """Reference (T,x) -> (after_shape, cost, cases)."""
    t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shape))
    t2, cost, cases, _ = ref_splay.splay(t, x)
    return keyed_shape(t2), cost, cases


def ind_run(shape, x):
    """Independent auditor (T,x) -> (after_shape, cost, cases)."""
    root = independent_tree.build_tree(independent_tree.parse_shape(shape))
    r2, cost, cases = independent_splay.splay(root, x)
    return independent_tree.shape_of(r2), cost, cases


def func_run(shape, x, n):
    """Functional third impl (T,x) -> (cost, cases). Shape via reference."""
    t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shape))
    st = func.from_keyed_tree(t)
    _, cost, cases = func.splay(st, x, n)
    return cost, cases


def load_fixtures():
    """Load frozen fixtures, freezing them first if absent (deterministic)."""
    path = os.path.join(REPO, "python", "reference", "fixtures.json")
    if not os.path.exists(path):
        # console.log equivalent [WP1-T-00]: fixtures absent, freezing.
        console_log("WP1-T-00", "fixtures.json absent, running freeze_fixtures.py")
        r = subprocess.run([sys.executable, os.path.join(REPO, "scripts", "freeze_fixtures.py")],
                           capture_output=True, text=True)
        sys.stdout.write(r.stdout)
        if r.returncode != 0:
            sys.stderr.write(r.stderr)
            raise AssertionError("freeze_fixtures.py failed")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def gate00():
    """SPEC 00: foundation freeze checks."""
    # console.log equivalent [WP1-T-01]: gate 00 begin.
    console_log("WP1-T-01", "gate00 foundation freeze checks begin")
    for rel in ["prereg/experiment.yaml", "prereg/sizes.yaml",
                "prereg/exact_contract.yaml", "prereg/allowed_claims.md",
                "prereg/forbidden_claims.md", "IMPLEMENTATION_SPEC.md",
                "FORMAL_NOTES.md", "math/proof_status.json",
                "external/MANIFEST.json", "Cargo.toml", "rust-toolchain.toml",
                "pyproject.toml", "requirements-lock.txt"]:
        check("G00-FILES", os.path.exists(os.path.join(REPO, rel)), rel)
    with open(os.path.join(REPO, "IMPLEMENTATION_SPEC.md"), "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    with open(os.path.join(REPO, "prereg", "prereg_sha256.txt"), encoding="utf-8") as f:
        recorded = f.read().strip()
    check("G00-SPEC-HASH", digest.lower() == recorded.lower(), digest[:16])
    with open(os.path.join(REPO, "external", "papers", "SHA256SUMS"), encoding="utf-8") as f:
        lines = [ln.split() for ln in f.read().splitlines() if ln.strip()]
    ok = True
    for digest2, name in lines:
        with open(os.path.join(REPO, "external", "papers", name), "rb") as f:
            if hashlib.sha256(f.read()).hexdigest().lower() != digest2.lower():
                ok = False
    check("G00-PAPERS", ok, "%d papers" % len(lines))
    with open(os.path.join(REPO, "math", "proof_status.json"), encoding="utf-8") as f:
        ledger = json.load(f)
    ok = all(t["status"] == "PROVED" and t["reviewed"] for t in ledger["theorems"])
    check("G00-T0", ok, "%d theorems" % len(ledger["theorems"]))
    n_schema = 0
    for root, _, files in os.walk(os.path.join(REPO, "schemas")):
        for fn in files:
            if fn.endswith(".schema.json"):
                with open(os.path.join(root, fn), encoding="utf-8") as f:
                    json.load(f)
                n_schema += 1
    check("G00-SCHEMAS", n_schema == 16, "schemas=%d" % n_schema)
    r = subprocess.run([sys.executable, os.path.join(REPO, "tests", "unit", "test_primitives.py")],
                       capture_output=True, text=True)
    check("G00-UNIT", r.returncode == 0, "unittest primitives")


def gate01():
    """SPEC 01: reference Splay semantics (M01-M06)."""
    # console.log equivalent [WP1-T-02]: gate 01 begin.
    console_log("WP1-T-02", "gate01 Splay semantics begin")
    t1 = ref_tree.assign_inorder_keys(ref_tree.parse_shape("(..)"))
    check("M01", ref_tree.compute_depth(t1, 1) == 0, "root depth")
    check("M02", ref_tree.access_cost(t1, 1) == 1, "root cost")
    ok = True
    for shape in enum.canonical_shapes(2):
        for x in (1, 2):
            if ref_run(shape, x)[:2] != ind_run(shape, x)[:2]:
                ok = False
            c, _ = func_run(shape, x, 2)
            if c != ref_run(shape, x)[1]:
                ok = False
    check("M03", ok, "n=2 triple agreement")
    ok = True
    count = 0
    for shape in enum.canonical_shapes(3):
        for x in (1, 2, 3):
            r = ref_run(shape, x)
            if r[:2] != ind_run(shape, x)[:2]:
                ok = False
            c, cs = func_run(shape, x, 3)
            if (c, cs) != (r[1], r[2]):
                ok = False
            count += 1
    check("M04", ok, "n=3 ops=%d" % count)
    # console.log equivalent [WP1-T-03]: fixtures oracle check.
    console_log("WP1-T-03", "fixture oracle check begin")
    fix = load_fixtures()
    ok = True
    for e in fix["entries"]:
        n = e["n"]
        if ref_run(e["before"], e["key"]) != (e["after"], e["cost"], e["cases"]):
            ok = False
        if ind_run(e["before"], e["key"]) != (e["after"], e["cost"], e["cases"]):
            ok = False
        c, cs = func_run(e["before"], e["key"], n)
        if (c, cs) != (e["cost"], e["cases"]):
            ok = False
    check("M04-FIX", ok, "fixtures=%d" % len(fix["entries"]))
    detected = False
    for shape in enum.canonical_shapes(2):
        t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shape))
        for x in (1, 2):
            faulty = ref_tree.compute_depth(t, x)
            if faulty != ref_tree.access_cost(t, x) - 1:
                pass
            if faulty == ref_run(shape, x)[1]:
                pass
            else:
                detected = True
    check("M05", detected, "depth-vs-depth+1 cost canary detected")
    ll = ref_run("(((..).).)", 1)
    detected = ll[2] == ["LL"] and ll[0] == "(.(.(..)))"
    check("M06", detected, "zig-zig order witness LL->%s" % (ll[0],))


def gate02():
    """SPEC 02: enumeration and canonical indexing (E01-E03)."""
    # console.log equivalent [WP1-T-04]: gate 02 begin.
    console_log("WP1-T-04", "gate02 enumeration begin")
    expected = {1: 1, 2: 2, 3: 5, 4: 14, 5: 42, 6: 132, 7: 429, 8: 1430}
    ok = all(enum.catalan(n) == c for n, c in expected.items())
    check("E01", ok, "Catalan n=1..8")
    ok = True
    for n in range(1, 9):
        shapes = enum.canonical_shapes(n)
        if len(shapes) != expected[n] or len(set(shapes)) != expected[n]:
            ok = False
        if any(enum.serialize_skeleton(enum.parse_shape(s)) != s for s in shapes):
            ok = False
    check("E02-E03", ok, "uniqueness+round-trip n=1..8")
    ok = True
    for n in range(1, 7):
        a = set(enum.canonical_shapes(n))
        b = set(enum.keyed_to_shape(t) for t in enum.enumerate_interval(1, n))
        if a != b:
            ok = False
    check("E-IND", ok, "interval enumerator agreement n<=6")
    ok = True
    for n in range(4, 6):
        for shape in enum.canonical_shapes(n):
            for x in range(1, n + 1):
                r = ref_run(shape, x)
                if r[:2] != ind_run(shape, x)[:2]:
                    ok = False
                c, cs = func_run(shape, x, n) if n <= 5 else (r[1], r[2])
                if (c, cs) != (r[1], r[2]):
                    ok = False
    check("M04-EXT", ok, "n=4..5 exhaustive agreement")
    r = subprocess.run([sys.executable, os.path.join(REPO, "tests", "exhaustive", "test_agreement.py")],
                       capture_output=True, text=True)
    check("G02-EXH", r.returncode == 0, "exhaustive unittest file")


def main():
    """Run selected gates, write a JSON log, exit 0 iff all pass."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", default="all", choices=["00", "01", "02", "all"])
    args = ap.parse_args()
    t0 = time.time()
    # console.log equivalent [WP1-T-05]: suite start.
    console_log("WP1-T-05", "suite start gate=%s" % args.gate)
    if args.gate in ("00", "all"):
        gate00()
    if args.gate in ("01", "all"):
        gate01()
    if args.gate in ("02", "all"):
        gate02()
    dt = time.time() - t0
    # console.log equivalent [WP1-T-06]: suite summary.
    console_log("WP1-T-06", "pass=%d fail=%d seconds=%.1f" % (len(PASS), len(FAIL), dt))
    logdir = os.path.join(REPO, "artifacts", "logs")
    os.makedirs(logdir, exist_ok=True)
    rec = {"experiment_id": "SPLAY-AM-PD-v0.1", "phase": "WP-1",
           "gate": args.gate, "pass": PASS, "fail": FAIL,
           "exit": 0 if not FAIL else 1, "wall_seconds": round(dt, 1)}
    with open(os.path.join(logdir, "wp1_gate_%s.json" % args.gate), "w", encoding="utf-8") as f:
        json.dump(rec, f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
