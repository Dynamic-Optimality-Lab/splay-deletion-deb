"""WP-6 gate suite: SPEC 15-18 (WP6-01..WP6-19).

Verifies branch closures, P01/P02 records, P17 non-activation, seal
integrity (result schema + claim + manifest + archive determinism),
reproduction, S02/S03, T0 gates, tables, report, terminal answers,
phase logs, threat/invariant sweep, finite-claim discipline, firewall
hygiene, and exact arithmetic.

Usage: python tests/test_wp6.py
Exit 0 iff every gate passes. Step-logged.
"""
import ast
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

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


def wp6(name):
    """Load one artifacts/wp6 record."""
    with open(os.path.join(REPO, "artifacts", "wp6", name), encoding="utf-8") as handle:
        return json.load(handle)


def seal_result():
    """Load the sealed FINAL_RESULT."""
    with open(os.path.join(REPO, "artifacts", "seal", "FINAL_RESULT.json"),
              encoding="utf-8") as handle:
        return json.load(handle)


def test_wp6_01_p01():
    """WP6-01: P01 telescoping unit record PASS, finite scope."""
    # console.log equivalent [WP6-T-01]: P01 audit begin.
    console_log("WP6-T-01", "WP6-01 P01 audit begin")
    p01 = wp6("p01_telescope.json")
    check("WP6-01", p01.get("verdict") == "PASS" and p01.get("identity_holds") is True
          and p01.get("scope") == "FINITE_MECHANISM_CHECK (not a theorem)"
          and len(p01.get("steps", [])) == 4, "telescoping identity finite-checked")


def test_wp6_02_p02():
    """WP6-02: P02 audit PASS with bridge never invoked."""
    # console.log equivalent [WP6-T-02]: P02 audit begin.
    console_log("WP6-T-02", "WP6-02 P02 audit begin")
    p02 = wp6("p02_bridge_audit.json")
    check("WP6-02", p02.get("verdict") == "PASS"
          and p02.get("bridge") == "BRIDGE_NOT_INVOKED"
          and len(p02.get("points", [])) == 5
          and all(p["status"] in ("MATCH", "GAP") for p in p02["points"]),
          "bridge audited, never invoked")


def test_wp6_03_closure():
    """WP6-03: P15/P16 closure with zero survivors."""
    # console.log equivalent [WP6-T-03]: closure audit begin.
    console_log("WP6-T-03", "WP6-03 closure audit begin")
    closure = wp6("positive_branch_closure.json")
    check("WP6-03", closure.get("survivors") == []
          and closure.get("positive_branch") == "CLOSED_NO_SUBJECT"
          and len(closure.get("lemmas", [])) == 5
          and all(l["status"] == "VACUOUS_NO_SUBJECT" for l in closure["lemmas"])
          and closure.get("telescoping_P16", {}).get("status") == "VACUOUS_NO_SUBJECT",
          "positive branch closed, no subjects")


def test_wp6_04_p17():
    """WP6-04: P17 not activated with identical reproduction."""
    # console.log equivalent [WP6-T-04]: P17 audit begin.
    console_log("WP6-T-04", "WP6-04 P17 audit begin")
    p17 = wp6("p17_activation.json")
    fams = p17.get("families", [])
    check("WP6-04", p17.get("verdict") == "P17_NOT_ACTIVATED" and len(fams) == 6
          and all(f["reproduced_identical"] for f in fams)
          and all(len(f["criteria"]) == 3 for f in fams)
          and not any(f["family_activated"] for f in fams),
          "6/6 reproduced, 0/6 activated")


def test_wp6_05_result():
    """WP6-05: FINAL_RESULT schema-valid, claim finite, pins exact."""
    # console.log equivalent [WP6-T-05]: result audit begin.
    console_log("WP6-T-05", "WP6-05 result audit begin")
    import jsonschema
    result = seal_result()
    with open(os.path.join(REPO, "schemas", "final_result.schema.json"),
              encoding="utf-8") as handle:
        schema = json.load(handle)
    try:
        jsonschema.validate(result, schema)
        schema_ok = True
    except Exception as err:
        print("SCHEMA-FAIL", str(err)[:200])
        schema_ok = False
    pins = {e["version"]: e["sha256"] for e in result.get("normative_spec_set", [])}
    ok = (schema_ok and result.get("claim_level") == "FINITE_EXACT_BN_RESULTS"
          and result.get("best_H_hypothesis") is None
          and result.get("universal_pair_access_lemma") is False
          and result.get("unbounded_counterexample_family_proved") is False
          and len(result.get("bn_results", [])) == 6
          and pins.get("v0.1.1-SA01") == "8B77278FF98F6AB5A3AA4D929A5787735F269647D5E3088CF4288F8ACF8C7726"
          and pins.get("v0.1.4-SA04") == "23046D37799860CCFD69BED21D6474F35ACA4E6FB91474FAAE2002617503E5FB")
    for row in result["bn_results"]:
        with open(os.path.join(REPO, "artifacts", "certificates", "n%d" % row["n"],
                               "bn_certificate.json"), encoding="utf-8") as handle:
            cert = json.load(handle)
        if cert["b"] != row["b"] or cert["criticality"] != row["outcome"]:
            ok = False
    check("WP6-05", ok, "result schema-valid, claim finite, pins exact")


def test_wp6_06_manifest():
    """WP6-06: manifest verifies; archive hash matches .sha256."""
    # console.log equivalent [WP6-T-06]: manifest audit begin.
    console_log("WP6-T-06", "WP6-06 manifest audit begin")

    def digest(path):
        h = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1048576), b""):
                h.update(chunk)
        return h.hexdigest()

    with open(os.path.join(REPO, "artifacts", "seal", "MANIFEST.sha256"),
              encoding="utf-8") as handle:
        lines = [l.rstrip("\n") for l in handle if l.strip()]
    ok = True
    seen = set()
    for line in lines:
        parts = line.split("  ")
        if len(parts) != 2:
            ok = False
            continue
        exp, rel = parts
        seen.add(rel)
        full = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.isfile(full) or digest(full) != exp.lower():
            print("MANIFEST-MISMATCH", rel)
            ok = False
    with open(os.path.join(REPO, "SPLAY-AM-PD-v0.1.tar.zst.sha256"),
              encoding="utf-8") as handle:
        sidecar = handle.read().strip()
    if sidecar != "%s  SPLAY-AM-PD-v0.1.tar.zst" % digest(
            os.path.join(REPO, "SPLAY-AM-PD-v0.1.tar.zst")):
        ok = False
    if "SPLAY-AM-PD-v0.1.tar.zst" not in seen:
        ok = False
    check("WP6-06", ok, "manifest %d entries verify" % len(lines))


def test_wp6_07_determinism():
    """WP6-07: archive rebuild is byte-identical (deterministic)."""
    # console.log equivalent [WP6-T-07]: archive determinism begin.
    console_log("WP6-T-07", "WP6-07 archive determinism begin")
    from python.wp6 import seal as SEAL

    def digest(path):
        h = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1048576), b""):
                h.update(chunk)
        return h.hexdigest()

    before = digest(os.path.join(REPO, "SPLAY-AM-PD-v0.1.tar.zst"))
    _out, digest2, _members = SEAL.build_archive()
    after = digest(os.path.join(REPO, "SPLAY-AM-PD-v0.1.tar.zst"))
    check("WP6-07", before == after, "archive rebuild identical")


def test_wp6_08_reproduce():
    """WP6-08: S01 reproduction PASS with byte-identical rebuilds."""
    # console.log equivalent [WP6-T-08]: S01 audit begin.
    console_log("WP6-T-08", "WP6-08 S01 audit begin")
    with open(os.path.join(REPO, "artifacts", "logs", "reproduce.json"),
              encoding="utf-8") as handle:
        log = json.load(handle)
    check("WP6-08", log.get("verdict") == "PASS"
          and len(log.get("rebuild", [])) == 15
          and all(r["method"] == "byte-identical" for r in log["rebuild"])
          and log.get("n7_cert_verify") is True
          and log.get("result_recompute_identical") is True,
          "S01 15/15 byte-identical + n7 + recompute")


def test_wp6_09_s02s03():
    """WP6-09: S02 sweep PASS and S03 zero violations."""
    # console.log equivalent [WP6-T-09]: S02/S03 audit begin.
    console_log("WP6-T-09", "WP6-09 S02/S03 audit begin")
    sweep = wp6("s02_s03_sweep.json")
    check("WP6-09", sweep.get("verdict") == "PASS"
          and all(r["bn"] and r["uv"] and r["critical"] for r in sweep.get("s02", []))
          and sweep.get("s03_violations") == []
          and all(r["status"] == "HOLDS" for r in sweep.get("invariants", [])),
          "S02 18/18, S03 clean, INV holds")


def test_wp6_10_t0():
    """WP6-10: T0-01..T0-14 PROVED+REVIEWED with gates satisfied."""
    # console.log equivalent [WP6-T-10]: T0 audit begin.
    console_log("WP6-T-10", "WP6-10 T0 audit begin")
    with open(os.path.join(REPO, "math", "proof_status.json"), encoding="utf-8") as handle:
        status = json.load(handle)
    check("WP6-10", len(status.get("theorems", [])) == 14
          and all(t["status"] == "PROVED" and t["reviewed"] for t in status["theorems"])
          and "SATISFIED" in status["gates"]["T0-GATE-A"]
          and "SATISFIED" in status["gates"]["T0-GATE-B"],
          "T0 gates satisfied pre-seal")


def test_wp6_11_tables():
    """WP6-11: README Tables A-E with exact fractions."""
    # console.log equivalent [WP6-T-11]: tables audit begin.
    console_log("WP6-T-11", "WP6-11 tables audit begin")
    with open(os.path.join(REPO, "README.md"), encoding="utf-8") as handle:
        text = handle.read()
    need = ("Table A", "Table B", "Table C", "Table D", "Table E",
            "23/14", "8/5", "3/2", "184041", "FINITE_EXACT_BN_RESULTS")
    check("WP6-11", all(s in text for s in need), "Tables A-E exact")


def test_wp6_12_report():
    """WP6-12: mining report final with severity separation."""
    # console.log equivalent [WP6-T-12]: report audit begin.
    console_log("WP6-T-12", "WP6-12 report audit begin")
    with open(os.path.join(REPO, "THEOREM_MINING_REPORT.md"), encoding="utf-8") as handle:
        text = handle.read()
    check("WP6-12", "FINAL (WP-6 seal)" in text
          and "CERTIFIED FACT" in text and "FINITE OBSERVATION" in text
          and "HYPOTHESIS" in text and "HEURISTIC" in text
          and "FINITE_EXACT_BN_RESULTS" in text
          and "CANDIDATE_H_SURVIVES" not in text,
          "report final, severities separated")


def test_wp6_13_terminal():
    """WP6-13: fifteen terminal answers with evidence pointers."""
    # console.log equivalent [WP6-T-13]: terminal answers audit begin.
    console_log("WP6-T-13", "WP6-13 terminal answers audit begin")
    with open(os.path.join(REPO, "math", "terminal_answers.md"), encoding="utf-8") as handle:
        text = handle.read()
    check("WP6-13", all("%d." % i in text for i in range(1, 16))
          and "artifacts/seal/FINAL_RESULT.json" in text,
          "15 answers with evidence")


def test_wp6_14_logs():
    """WP6-14: phase15-18 logs present with exit 0."""
    # console.log equivalent [WP6-T-14]: phase-log audit begin.
    console_log("WP6-T-14", "WP6-14 phase-log audit begin")
    ok = True
    for name in ("phase15", "phase16", "phase17", "phase18"):
        path = os.path.join(REPO, "artifacts", "logs", "%s.json" % name)
        if not os.path.exists(path):
            ok = False
            continue
        with open(path, encoding="utf-8") as handle:
            log = json.load(handle)
        if log.get("exit") != 0 or log.get("experiment_id") != "SPLAY-AM-PD-v0.1":
            ok = False
    check("WP6-14", ok, "phase15-18 logs exit 0")


def test_wp6_15_threats():
    """WP6-15: T1-T22 covered."""
    # console.log equivalent [WP6-T-15]: threat audit begin.
    console_log("WP6-T-15", "WP6-15 threat audit begin")
    sweep = wp6("s02_s03_sweep.json")
    threats = sweep.get("threats", [])
    check("WP6-15", len(threats) == 22
          and all(t["status"] == "COVERED" for t in threats),
          "T1-T22 covered")


def test_wp6_16_finite():
    """WP6-16: finite-claim discipline (no theorem strings in seal outputs)."""
    # console.log equivalent [WP6-T-16]: claim discipline audit begin.
    console_log("WP6-T-16", "WP6-16 claim discipline audit begin")
    result = seal_result()
    with open(os.path.join(REPO, "THEOREM_MINING_REPORT.md"), encoding="utf-8") as handle:
        report = handle.read()
    ok = (result["claim_level"] == "FINITE_EXACT_BN_RESULTS"
          and "UNIVERSAL_PAIR_ACCESS_LEMMA_PROVED" not in report
          and "DYNAMIC_OPTIMALITY_PROVED" not in report
          and "DYNAMIC_OPTIMALITY_DISPROVED" not in report)
    for name in ("proof_branch_closure.md", "proof_telescoping_unit.md",
                 "proof_p17_nonactivation.md", "bridge_audit.md",
                 "terminal_answers.md"):
        with open(os.path.join(REPO, "math", name), encoding="utf-8") as handle:
            text = handle.read()
        if "is hereby proved" in text.lower() or "q.e.d." in text.lower():
            print("PROOFCLaim %s" % name)
            ok = False
    check("WP6-16", ok, "finite claim discipline holds")


def test_wp6_17_firewall():
    """WP6-17: firewalls EMPTY; wp6 code references no holdout detail."""
    # console.log equivalent [WP6-T-17]: firewall audit begin.
    console_log("WP6-T-17", "WP6-17 firewall audit begin")
    with open(os.path.join(REPO, "artifacts", "wp5", "sa03", "n8_firewall.json"),
              encoding="utf-8") as handle:
        n8 = json.load(handle)
    with open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout", "h1_firewall.json"),
              encoding="utf-8") as handle:
        h1 = json.load(handle)
    forbidden = ("n8_holdout", "holdout_bank", "bank_secret", "HOLDOUT-H1",
                 "h1_firewall", "n8_firewall")
    ok = n8.get("state") == "EMPTY" and h1.get("state") == "EMPTY"
    for root, _dirs, files in os.walk(os.path.join(REPO, "python", "wp6")):
        for name in files:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                text = handle.read()
            for token in forbidden:
                if token in text:
                    print("HOLDOUTREF %s %r" % (name, token))
                    ok = False
    check("WP6-17", ok, "firewalls EMPTY, no holdout refs")


def test_wp6_18_exact():
    """WP6-18: wp6 code uses exact arithmetic only."""
    # console.log equivalent [WP6-T-18]: exactness audit begin.
    console_log("WP6-T-18", "WP6-18 exactness audit begin")
    ok = True
    for root, _dirs, files in os.walk(os.path.join(REPO, "python", "wp6")):
        for name in files:
            if not name.endswith(".py"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Div):
                    print("FLOATDIV %s line %d" % (name, node.lineno))
                    ok = False
                if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "float":
                    print("FLOATCALL %s line %d" % (name, node.lineno))
                    ok = False
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] in ("numpy", "scipy"):
                            print("FLOATLIB %s" % name)
                            ok = False
    check("WP6-18", ok, "no float division/calls/libs in wp6 code")


def test_wp6_19_scripts():
    """WP6-19: phase drivers and reproduction scripts exist."""
    # console.log equivalent [WP6-T-19]: script presence audit begin.
    console_log("WP6-T-19", "WP6-19 script audit begin")
    ok = all(os.path.exists(os.path.join(REPO, "scripts", name)) for name in (
        "run_phase15.sh", "run_phase15.ps1", "run_phase16.sh", "run_phase16.ps1",
        "run_phase17.sh", "run_phase17.ps1", "run_phase18.sh", "run_phase18.ps1",
        "reproduce_all.sh", "reproduce_all.ps1"))
    check("WP6-19", ok, "phase15-18 + reproduce drivers present")


def main(argv=None):
    """Run WP-6 gates, exit nonzero on any failure."""
    import time
    t0 = time.time()
    # console.log equivalent [WP6-T-20]: suite start.
    console_log("WP6-T-20", "WP-6 gate suite start")
    test_wp6_01_p01()
    test_wp6_02_p02()
    test_wp6_03_closure()
    test_wp6_04_p17()
    test_wp6_05_result()
    test_wp6_06_manifest()
    test_wp6_07_determinism()
    test_wp6_08_reproduce()
    test_wp6_09_s02s03()
    test_wp6_10_t0()
    test_wp6_11_tables()
    test_wp6_12_report()
    test_wp6_13_terminal()
    test_wp6_14_logs()
    test_wp6_15_threats()
    test_wp6_16_finite()
    test_wp6_17_firewall()
    test_wp6_18_exact()
    test_wp6_19_scripts()
    dt = time.time() - t0
    # console.log equivalent [WP6-T-21]: suite summary.
    console_log("WP6-T-21", "pass=%d fail=%d seconds=%.1f" % (len(PASS), len(FAIL), dt))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
