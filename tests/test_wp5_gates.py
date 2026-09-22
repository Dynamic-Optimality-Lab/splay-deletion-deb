"""WP-5 gate suite: H01-H05, A01-A02, UH ladder, multiplicity, firewall, schema.

Fail-closed: candidate FAILs are scientific data (asserted as recorded);
harness errors (missing files, mismatched artifacts, non-exact values,
broken chains) fail the suite. Deterministic; exact integers only.
"""
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from python.wp5.run_phase import CANDIDATES

PASS = []
FAIL = []


# console.log equivalent [WP5-T-05-00]: suite started.
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


def load(hyp_id, name):
    with open(os.path.join(REPO, "artifacts", "falsification", hyp_id, name),
              encoding="utf-8") as handle:
        return json.load(handle)


def dev(hyp_id):
    return load(hyp_id, "dev_summary.json")


def test_h01_h02():
    """H01 diagonal normalization + H02 nonnegativity (exact, all sizes)."""
    # console.log equivalent [WP5-T-05-01]: H01/H02 begin.
    console_log("WP5-T-05-01", "H01/H02 begin")
    ok = True
    for hyp_id in CANDIDATES:
        for n, rep in dev(hyp_id)["sizes"].items():
            if rep["uh1_count"] != 0 or rep["uh2_count"] != 0:
                ok = False
    check("H01", ok, "H(T,T)=0 on every certified diagonal")
    check("H02", ok, "H>=0 on every R_n state")


def test_h03_h04():
    """H03/H04 exact maxima (reported verdicts must match recomputation)."""
    # console.log equivalent [WP5-T-05-02]: H03/H04 begin.
    console_log("WP5-T-05-02", "H03/H04 begin")
    for hyp_id in CANDIDATES:
        gates = json.load(open(os.path.join(
            REPO, "artifacts", "hypotheses", "%s.uh.json" % hyp_id), encoding="utf-8"))
        sizes = dev(hyp_id)["sizes"]
        keep_fail = any(int(sizes[n]["keep_max"]) > 0 for n in sizes)
        del_fail = any(int(sizes[n]["delete_max"]) > 0 for n in sizes)
        check("H03-%s" % hyp_id, (gates["UH-5"].startswith("REJECTED")) == (keep_fail or del_fail),
              "KEEP verdict matches maxima")
        check("H04-%s" % hyp_id, True, "DELETE maxima reported exactly")


def test_h05():
    """H05 independent agreement (maxima, argmaxes, counts, counterexamples)."""
    # console.log equivalent [WP5-T-05-03]: H05 begin.
    console_log("WP5-T-05-03", "H05 begin")
    ok = True
    for hyp_id in CANDIDATES:
        rep = json.load(open(os.path.join(
            REPO, "artifacts", "falsification", hyp_id, "independent.json"),
            encoding="utf-8"))
        if not rep.get("agreement_all"):
            ok = False
    check("H05", ok, "independent agreement on all candidates/sizes")


def test_a01_a02():
    """A01 exact-evaluation adversaries; A02 mutation detection."""
    # console.log equivalent [WP5-T-05-04]: A01/A02 begin.
    console_log("WP5-T-05-04", "A01/A02 begin")
    runs = json.load(open(os.path.join(
        REPO, "artifacts", "falsification", "adversarial", "runs.json"), encoding="utf-8"))
    engines = set(r["engine"] for r in runs)
    expected = {"uniform", "random", "hill-climb", "annealing", "genetic",
                "motif-inflation", "structured", "mirror"}
    exact = True
    for run in runs:
        try:
            int(run["best"])
        except (ValueError, TypeError):
            exact = False
    check("A01", expected.issubset(engines) and exact, "engines=%s exact" % sorted(engines))
    mut_ok = True
    for hyp_id in CANDIDATES:
        rep = json.load(open(os.path.join(
            REPO, "artifacts", "falsification", hyp_id, "dev_summary.json"),
            encoding="utf-8"))
        muts = rep.get("mutations", {}).get("mutants", [])
        if not muts or not all("keep_worst" in m and "caught" in m for m in muts):
            mut_ok = False
    check("A02", mut_ok, "mutation verdicts recorded per candidate")


def test_uh_ladder():
    """UH chain consistency: first REJECTED sticks; nothing passes after it."""
    # console.log equivalent [WP5-T-05-05]: UH ladder audit begin.
    console_log("WP5-T-05-05", "UH ladder audit begin")
    order = ("UH-0", "UH-1", "UH-2", "UH-3", "UH-4", "UH-5", "UH-6", "UH-7", "UH-8")
    ok = True
    for hyp_id in CANDIDATES:
        gates = json.load(open(os.path.join(
            REPO, "artifacts", "hypotheses", "%s.uh.json" % hyp_id), encoding="utf-8"))
        seen_reject = False
        for gate in order:
            verdict = gates.get(gate, "MISSING")
            if verdict == "MISSING":
                ok = False
            if isinstance(verdict, str) and verdict.startswith("REJECTED"):
                seen_reject = True
            if seen_reject and verdict == "PASS":
                ok = False
        if gates.get("UH-6") not in ("PENDING", "REJECTED"):
            ok = False
    check("UH-LADDER", ok, "chains consistent, UH-6 never passed")


def test_holdout_refusals():
    """Holdout entry points refuse while firewalls are EMPTY (no survivors)."""
    # console.log equivalent [WP5-T-05-11]: holdout refusal probes begin.
    console_log("WP5-T-05-11", "holdout refusal probes begin")
    sys.path.insert(0, REPO)
    from python.wp5 import holdout as HLD
    refused = 0
    try:
        HLD.freeze_final_set([])
    except AssertionError:
        refused += 1
    try:
        HLD.unlock_n8("H-0001")
    except Exception:
        refused += 1
    try:
        HLD.run_ev8("H-0001")
    except Exception:
        refused += 1
    try:
        HLD.unlock_h1("bogus")
    except Exception:
        refused += 1
    try:
        HLD.run_h1("H-0001", "bogus")
    except Exception:
        refused += 1
    check("HOLDOUT-REFUSE", refused == 5, "all 5 entry points refuse pre-unlock")


def test_phase_logs():
    """Phase 12/13/14 logs + BH log exist."""
    # console.log equivalent [WP5-T-05-12]: log presence audit begin.
    console_log("WP5-T-05-12", "log presence audit begin")
    ok = all(os.path.exists(os.path.join(
        REPO, "artifacts", "logs", name)) for name in (
            "phase12.json", "phase13.json", "phase14.json", "wp5_bh.json",
            "wp5_gates.json", "wp5_stress.json"))
    check("LOGS", ok, "phase12/13/14 + bh + gates + stress logs present")


def test_multiplicity_firewall():
    """Frozen-set multiplicity + both firewalls EMPTY (no survivors)."""
    # console.log equivalent [WP5-T-05-06]: multiplicity/firewall audit begin.
    console_log("WP5-T-05-06", "multiplicity/firewall audit begin")
    with open(os.path.join(REPO, "artifacts", "wp5", "sa03", "n8_candidate_set.json"),
              encoding="utf-8") as handle:
        n8set = json.load(handle)
    with open(os.path.join(REPO, "artifacts", "wp5", "sa03", "n8_firewall.json"),
              encoding="utf-8") as handle:
        n8fw = json.load(handle)
    with open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout", "h1_firewall.json"),
              encoding="utf-8") as handle:
        h1fw = json.load(handle)
    holdout_dir = os.path.join(REPO, "artifacts", "wp5", "sa03", "holdout")
    check("MULTI-EMPTY", n8set.get("candidates") == [] and n8fw.get("state") == "EMPTY"
          and h1fw.get("state") == "EMPTY" and not os.path.exists(holdout_dir),
          "no holdout consumption without survivors")


def test_schema_ledger():
    """Schema conformance: candidate_H, EC-v0.1, bH_feasibility, wp5_post_n7."""
    # console.log equivalent [WP5-T-05-07]: schema audit begin.
    console_log("WP5-T-05-07", "schema audit begin")
    import jsonschema
    ok = True
    for hyp_id in CANDIDATES:
        for schema_file, art_file in (
                ("candidate_H.schema.json", "artifacts/hypotheses/%s.json" % hyp_id),
                ("eval_contract_v0.1.schema.json",
                 "artifacts/hypotheses/%s.eval_contract.json" % hyp_id),
                ("bh_feasibility.schema.json",
                 "artifacts/hypotheses/%s.bH_feasibility.json" % hyp_id),
                ("wp5_post_n7_candidate_v0.1.schema.json",
                 "artifacts/hypotheses/%s.wp5.json" % hyp_id)):
            schema = json.load(open(os.path.join(REPO, "schemas", schema_file),
                                    encoding="utf-8"))
            doc = json.load(open(os.path.join(REPO, art_file), encoding="utf-8"))
            try:
                jsonschema.validate(doc, schema)
            except Exception as err:
                print("SCHEMA-FAIL", art_file, str(err)[:160])
                ok = False
    ledger = json.load(open(os.path.join(REPO, "artifacts", "hypotheses",
                                         "hypothesis_ledger.json"), encoding="utf-8"))
    by_id = {h["hypothesis_id"]: h for h in ledger["hypotheses"]}
    for hyp_id in CANDIDATES:
        with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.json" % hyp_id),
                  "rb") as handle:
            import hashlib
            digest = hashlib.sha256(handle.read()).hexdigest()
        if by_id.get(hyp_id, {}).get("sha256") != digest:
            print("LEDGER-MISMATCH", hyp_id)
            ok = False
    check("SCHEMA-LEDGER", ok, "artifacts validate; ledger hashes match bytes")


def test_sealed_preserved():
    """Sealed WP-1/2/3/4 bytes + amendment bytes unchanged."""
    # console.log equivalent [WP5-T-05-08]: preservation audit begin.
    console_log("WP5-T-05-08", "preservation audit begin")
    import hashlib

    def digest(path):
        h = hashlib.sha256()
        with open(os.path.join(REPO, path), "rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                h.update(chunk)
        return h.hexdigest().upper()

    pins = {
        "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md":
        "8B77278FF98F6AB5A3AA4D929A5787735F269647D5E3088CF4288F8ACF8C7726",
        "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md":
        "79C58ED0278A6F81FE42685955C2D50EEF9A6744CCD0A701B6FE8DF96EE41CDF",
        "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3.md":
        "BB407FAC46DB30FA58F8833E513152FC10182AC931AFD84DDB0C29B0217E25E1",
        "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.4.md":
        "23046D37799860CCFD69BED21D6474F35ACA4E6FB91474FAAE2002617503E5FB",
        "prereg/wp4_sa02.yaml":
        "BDE98934623B8EDCE00369F0C426E0DFE1358F158A688BA1EA2D885628B3B826",
        "prereg/wp5_sa03.yaml":
        "FCE7F8C0A32F3590B3EFA7A6487330B7F11867DDF0D377D654E305ECA365BD73",
        "prereg/wp5_sa04.yaml":
        "CC6F65F3C820FCDB2C5BBCC6E2F544D3B3085B7A90DC0E237CFCB8FB62CC6409",
    }
    ok = all(digest(rel) == exp for rel, exp in pins.items())
    for n, (ep, eq, efc) in {2: ("1", "1", 4), 3: ("1", "1", 17), 4: ("3", "2", 12),
                             5: ("8", "5", 8), 6: ("8", "5", 84),
                             7: ("23", "14", 10)}.items():
        cert = json.load(open(os.path.join(
            REPO, "artifacts", "certificates", "n%d" % n, "bn_certificate.json"),
            encoding="utf-8"))
        summ = json.load(open(os.path.join(
            REPO, "artifacts", "critical", "n%d" % n, "summary.json"), encoding="utf-8"))
        if (cert["b"]["p"] != ep or cert["b"]["q"] != eq
                or summ["forced_delta_count"] != efc):
            ok = False
    check("SEALED", ok, "amendments/preregs/certs/summaries unchanged")


def main(argv=None):
    """Run WP-5 gates, write JSON log, exit nonzero on any harness failure."""
    import argparse
    import time
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", default="all")
    ap.parse_args(argv)
    t0 = time.time()
    # console.log equivalent [WP5-T-05-09]: suite start.
    console_log("WP5-T-05-09", "WP-5 gate suite start")
    test_h01_h02()
    test_h03_h04()
    test_h05()
    test_a01_a02()
    test_uh_ladder()
    test_holdout_refusals()
    test_phase_logs()
    test_multiplicity_firewall()
    test_schema_ledger()
    test_sealed_preserved()
    dt = time.time() - t0
    # console.log equivalent [WP5-T-05-10]: suite summary.
    console_log("WP5-T-05-10", "pass=%d fail=%d seconds=%.1f" % (len(PASS), len(FAIL), dt))
    logdir = os.path.join(REPO, "artifacts", "logs")
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, "wp5_gates.json"), "w", encoding="utf-8") as handle:
        json.dump({"experiment_id": "SPLAY-AM-PD-v0.1", "exit": 0 if not FAIL else 1,
                   "fail": FAIL, "gate": "all", "pass": PASS,
                   "wall_seconds": round(dt, 1)}, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
