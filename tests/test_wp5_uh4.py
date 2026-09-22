"""WP-5 UH-4 corrective compliance suite (UH4-01..UH4-19).

Verifies the append-only UH-4 repair: fresh b_H=2 canonical geometry,
independent verification, exact UH-4 verdicts for H-0001..H-0006, honest
ladder order, UH-5 evidence preservation, frozen-artifact pins, firewall
states, exact arithmetic, and determinism.

Usage: python tests/test_wp5_uh4.py
Exit 0 iff every gate passes. Step-logged.
"""
import ast
import hashlib
import json
import os
import subprocess
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


H_IDS = ("H-0001", "H-0002", "H-0003", "H-0004", "H-0005", "H-0006")
SIZES = (2, 3, 4, 5, 6, 7)
REPAIR_CODE = (
    "python/wp5/uh4_geometry.py",
    "python/wp5/uh4_sandwich.py",
    "python/wp5_independent/uh4_check.py",
    "python/audit/verify_bh_geometry.py",
)


def git_diff_quiet(*paths):
    """True iff no working-tree/HEAD difference on the given paths."""
    r = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"] + list(paths),
                       capture_output=True)
    return r.returncode == 0


def bh_dir(n):
    """hypothesis_bH directory for one size."""
    return os.path.join(REPO, "artifacts", "potentials", "n%d" % n, "hypothesis_bH")


def test_uh4_01_artifacts():
    """UH4-01: b=2 canonical U/V artifacts exist for every certified n."""
    # console.log equivalent [WP5-T-UH4-01]: geometry artifact presence.
    console_log("WP5-T-UH4-01", "UH4-01 artifact presence begin")
    ok = True
    for n in SIZES:
        for name in ("U.json.zst", "V.json.zst", "G.json.zst",
                     "forced_states.json", "bellman_witnesses.json",
                     "summary.json", "bH_geometry.v1.json"):
            if not os.path.exists(os.path.join(bh_dir(n), name)):
                print("MISSING n=%d %s" % (n, name))
                ok = False
    check("UH4-01", ok, "b=2 geometry artifacts present n=2..7")


def test_uh4_02_unconfusable():
    """UH4-02: artifacts state b=2/1 and differ from WP-3 b_n* geometry."""
    # console.log equivalent [WP5-T-UH4-02]: b-declaration audit begin.
    console_log("WP5-T-UH4-02", "UH4-02 b-declaration audit begin")
    import zstandard as zstd
    ok = True
    for n in SIZES:
        with open(os.path.join(bh_dir(n), "bH_geometry.v1.json"), encoding="utf-8") as handle:
            companion = json.load(handle)
        with open(os.path.join(bh_dir(n), "summary.json"), encoding="utf-8") as handle:
            summary = json.load(handle)
        if companion.get("schema") != "BHG-v0.1":
            ok = False
        if companion.get("b_H") != {"p": "2", "q": "1"}:
            ok = False
        if summary.get("b") != {"p": "2", "q": "1"}:
            ok = False
        with open(os.path.join(bh_dir(n), "U.json.zst"), "rb") as handle:
            new_blob = zstd.ZstdDecompressor().decompress(handle.read())
        sealed = os.path.join(REPO, "artifacts", "potentials", "n%d" % n, "U.json.zst")
        with open(sealed, "rb") as handle:
            old_blob = zstd.ZstdDecompressor().decompress(handle.read())
        if hashlib.sha256(new_blob).hexdigest() == hashlib.sha256(old_blob).hexdigest():
            print("CONFUSABLE n=%d: b=2 U identical to b_n* U" % n)
            ok = False
    check("UH4-02", ok, "b=2/1 declared; tables distinct from b_n* geometry")


def test_uh4_03_independent():
    """UH4-03: independent verifier agrees on U_2 and V_2."""
    # console.log equivalent [WP5-T-UH4-03]: independent geometry verification.
    console_log("WP5-T-UH4-03", "UH4-03 independent verification begin")
    ok = True
    for n in SIZES:
        outdir = os.path.join(REPO, "artifacts", "audits", "n%d" % n)
        r = subprocess.run(
            [sys.executable, os.path.join(REPO, "python", "audit", "verify_bh_geometry.py"),
             "--n", str(n), "--pot-dir", bh_dir(n), "--out", outdir],
            capture_output=True, text=True)
        sys.stdout.write(r.stdout)
        if r.returncode != 0:
            sys.stderr.write(r.stderr[-2000:] if r.stderr else "")
            ok = False
        with open(os.path.join(outdir, "verify_bh2.json"), encoding="utf-8") as handle:
            report = json.load(handle)
        if report.get("verdict") != "PASS":
            print("VERIFY-FAIL n=%d %s" % (n, report.get("checks")))
            ok = False
    check("UH4-03", ok, "independent U_2/V_2 agreement n=2..7")


def test_uh4_04_feasibility():
    """UH4-04: V_2 <= U_2 for every reachable state n=2..7."""
    # console.log equivalent [WP5-T-UH4-04]: feasibility sweep begin.
    console_log("WP5-T-UH4-04", "UH4-04 V<=U sweep begin")
    import zstandard as zstd
    ok = True
    total = 0
    for n in SIZES:
        with open(os.path.join(bh_dir(n), "U.json.zst"), "rb") as handle:
            u_rows = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
        with open(os.path.join(bh_dir(n), "V.json.zst"), "rb") as handle:
            v_rows = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
        U = {r["pair_id"]: int(r["U_scaled"]) for r in u_rows}
        V = {r["pair_id"]: int(r["V_scaled"]) for r in v_rows}
        if set(U) != set(V):
            ok = False
        for pid in U:
            total += 1
            if V[pid] > U[pid]:
                ok = False
    check("UH4-04", ok, "V_2<=U_2 on %d states" % total)


def test_uh4_05_verdicts():
    """UH4-05: all six candidates have a non-PENDING UH-4 verdict."""
    # console.log equivalent [WP5-T-UH4-05]: verdict presence audit begin.
    console_log("WP5-T-UH4-05", "UH4-05 verdict audit begin")
    ok = True
    for hyp_id in H_IDS:
        path = os.path.join(REPO, "artifacts", "hypotheses", "%s.uh4.json" % hyp_id)
        if not os.path.exists(path):
            ok = False
            continue
        with open(path, encoding="utf-8") as handle:
            record = json.load(handle)
        if record.get("schema") != "UH4-v0.1":
            ok = False
        if record.get("verdict") not in ("PASS", "FAIL"):
            ok = False
        if [r["n"] for r in record.get("per_n", [])] != [2, 3, 4, 5, 6, 7]:
            ok = False
        with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.uh.json" % hyp_id),
                  encoding="utf-8") as handle:
            ladder = json.load(handle)
        expected = "PASS" if record["verdict"] == "PASS" else "REJECTED"
        if ladder.get("UH-4") != expected:
            print("LADDER-MISMATCH %s uh4=%s ladder=%s" % (hyp_id, record["verdict"], ladder.get("UH-4")))
            ok = False
    check("UH4-05", ok, "6/6 non-PENDING UH-4 verdicts, ladder matches")


def test_uh4_06_agreement():
    """UH4-06: primary and independent UH-4 candidate evaluations agree."""
    # console.log equivalent [WP5-T-UH4-06]: candidate agreement audit begin.
    console_log("WP5-T-UH4-06", "UH4-06 candidate agreement begin")
    from python.wp5_independent import uh4_check as IND
    from python.wp5 import candidates as C
    ok = True
    compared = 0
    for hyp_id in H_IDS:
        with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.uh4.json" % hyp_id),
                  encoding="utf-8") as handle:
            record = json.load(handle)
        formula_id = C.FORMULA_IDS[hyp_id]
        for row in record["per_n"]:
            mine = IND.independent_uh4(hyp_id, formula_id, row["n"], REPO)
            compared += 1
            for field in ("lower_violations", "upper_violations",
                          "max_lower_margin", "max_upper_margin", "status",
                          "states_checked"):
                if mine[field] != row[field]:
                    print("AGREE-FAIL %s n=%d %s: %r vs %r" %
                          (hyp_id, row["n"], field, mine[field], row[field]))
                    ok = False
            mf, rf = mine["first_violation"], row["first_violation"]
            if (mf is None) != (rf is None):
                print("AGREE-FAIL %s n=%d first-null mismatch" % (hyp_id, row["n"]))
                ok = False
            elif mf is not None:
                for field in ("pair_id", "kind", "H", "U_2", "V_2", "signed_diff"):
                    if mf[field] != rf[field]:
                        print("AGREE-FAIL %s n=%d first.%s" % (hyp_id, row["n"], field))
                        ok = False
    check("UH4-06", ok, "primary==independent on %d H/n cells" % compared)


def test_uh4_07_ladder_order():
    """UH4-07: first decisive rejection is represented honestly."""
    # console.log equivalent [WP5-T-UH4-07]: ladder-order audit begin.
    console_log("WP5-T-UH4-07", "UH4-07 ladder-order audit begin")
    order = ("UH-0", "UH-1", "UH-2", "UH-3", "UH-4", "UH-5", "UH-6", "UH-7", "UH-8")
    ok = True
    for hyp_id in H_IDS:
        with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.uh4.json" % hyp_id),
                  encoding="utf-8") as handle:
            uh4 = json.load(handle)["verdict"]
        with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.uh.json" % hyp_id),
                  encoding="utf-8") as handle:
            ladder = json.load(handle)
        if uh4 == "FAIL":
            if ladder.get("UH-4") != "REJECTED":
                ok = False
            if "EARLIER_AT_UH4" not in str(ladder.get("UH-5")):
                print("ORDER-FAIL %s: UH-4 FAIL but UH-5 not marked supplementary" % hyp_id)
                ok = False
        else:
            if ladder.get("UH-4") != "PASS" or ladder.get("UH-5") != "REJECTED":
                ok = False
        seen_reject = False
        for gate in order:
            verdict = ladder.get(gate, "MISSING")
            if verdict == "MISSING":
                ok = False
            if isinstance(verdict, str) and verdict.startswith("REJECTED"):
                seen_reject = True
            if seen_reject and verdict == "PASS":
                ok = False
    check("UH4-07", ok, "first-failure order honest 6/6")


def test_uh4_08_uh5_preserved():
    """UH4-08: existing UH-5 scientific evidence byte-preserved."""
    # console.log equivalent [WP5-T-UH4-08]: UH-5 preservation audit begin.
    console_log("WP5-T-UH4-08", "UH4-08 UH-5 preservation audit begin")
    paths = ["artifacts/falsification"]
    for hyp_id in H_IDS:
        for suffix in (".json", ".eval_contract.json", ".bH_feasibility.json",
                       ".og.json", ".wp5.json"):
            paths.append("artifacts/hypotheses/%s%s" % (hyp_id, suffix))
    paths.append("artifacts/hypotheses/hypothesis_ledger.json")
    check("UH4-08", git_diff_quiet(*paths),
          "UH-5 evidence + frozen H records unchanged vs HEAD")


def test_uh4_09_frozen_h():
    """UH4-09: no hypothesis formula, coefficient, b_H, or ID changed."""
    # console.log equivalent [WP5-T-UH4-09]: frozen-H audit begin.
    console_log("WP5-T-UH4-09", "UH4-09 frozen-H audit begin")
    paths = []
    for hyp_id in H_IDS:
        paths.append("artifacts/hypotheses/%s.json" % hyp_id)
        paths.append("artifacts/hypotheses/%s.eval_contract.json" % hyp_id)
    paths.append("python/wp5/structural.py")
    paths.append("python/wp5/candidates.py")
    paths.append("python/wp5_independent/independent.py")
    ok = git_diff_quiet(*paths)
    for hyp_id in H_IDS:
        with open(os.path.join(REPO, "artifacts", "hypotheses",
                               "%s.eval_contract.json" % hyp_id), encoding="utf-8") as handle:
            ec = json.load(handle)
        if ec.get("b_hypothesis") != {"p": "2", "q": "1"}:
            print("BH-CHANGED %s" % hyp_id)
            ok = False
    check("UH4-09", ok, "formulas/coefficients/b_H/IDs frozen")


def test_uh4_10_n8_firewall():
    """UH4-10: n8 firewall remains EMPTY."""
    # console.log equivalent [WP5-T-UH4-10]: n8 firewall audit begin.
    console_log("WP5-T-UH4-10", "UH4-10 n8 firewall audit begin")
    with open(os.path.join(REPO, "artifacts", "wp5", "sa03", "n8_firewall.json"),
              encoding="utf-8") as handle:
        fw = json.load(handle)
    check("UH4-10", fw.get("state") == "EMPTY" and fw.get("unlock") is None,
          "n8 firewall EMPTY")


def test_uh4_11_h1_firewall():
    """UH4-11: H1 firewall remains EMPTY."""
    # console.log equivalent [WP5-T-UH4-11]: H1 firewall audit begin.
    console_log("WP5-T-UH4-11", "UH4-11 H1 firewall audit begin")
    with open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout", "h1_firewall.json"),
              encoding="utf-8") as handle:
        fw = json.load(handle)
    check("UH4-11", fw.get("state") == "EMPTY" and fw.get("unlock") is None,
          "H1 firewall EMPTY")


def test_uh4_12_n8_unread():
    """UH4-12: corrective code never references n8 detailed records."""
    # console.log equivalent [WP5-T-UH4-12]: n8 static audit begin.
    console_log("WP5-T-UH4-12", "UH4-12 n8 static audit begin")
    forbidden = ("n8_holdout", "bank_secret", "trees/n8", "sa03/holdout",
                 "HOLDOUT-H1", "h1_firewall", "n8_firewall", "holdout_bank")
    ok = True
    for rel in REPAIR_CODE:
        with open(os.path.join(REPO, rel), encoding="utf-8") as handle:
            text = handle.read()
        for token in forbidden:
            if token in text:
                print("N8REF %s contains %r" % (rel, token))
                ok = False
    check("UH4-12", ok, "no n8 detailed references in repair code")


def test_uh4_13_h1_unread():
    """UH4-13: corrective code never reads the H1 detailed bank."""
    # console.log equivalent [WP5-T-UH4-13]: H1 static audit begin.
    console_log("WP5-T-UH4-13", "UH4-13 H1 static audit begin")
    ok = True
    for rel in REPAIR_CODE:
        with open(os.path.join(REPO, rel), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "holdout_bank" in node.module or "n8_holdout" in node.module:
                    print("H1IMPORT %s" % rel)
                    ok = False
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "holdout_bank" in alias.name or "n8_holdout" in alias.name:
                        print("H1IMPORT %s" % rel)
                        ok = False
        with open(os.path.join(REPO, rel), encoding="utf-8") as handle:
            text = handle.read()
        for token in ("h1_holdout", "120000", "4120000", "4,120,000"):
            if token in text:
                print("H1REF %s contains %r" % (rel, token))
                ok = False
    check("UH4-13", ok, "no H1 bank reads in repair code")


def test_uh4_14_sealed():
    """UH4-14: all pre-WP5 sealed WP-1/2/3/4 hashes still match."""
    # console.log equivalent [WP5-T-UH4-14]: seal re-verification begin.
    console_log("WP5-T-UH4-14", "UH4-14 seal re-verification begin")
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
    check("UH4-14", ok, "sealed pins + certs unchanged")


def test_uh4_15_sa_bytes():
    """UH4-15: all SA-01..SA-04 bytes/hashes unchanged."""
    # console.log equivalent [WP5-T-UH4-15]: amendment byte audit begin.
    console_log("WP5-T-UH4-15", "UH4-15 amendment byte audit begin")
    paths = ["SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md",
             "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md",
             "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3.md",
             "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.4.md",
             "IMPLEMENTATION_SPEC.md", "WorkPlan.md",
             "prereg/wp4_sa02.yaml", "prereg/wp5_sa03.yaml", "prereg/wp5_sa04.yaml"]
    check("UH4-15", git_diff_quiet(*paths), "normative stack bytes unchanged")


def test_uh4_16_claim():
    """UH4-16: claim level is not promoted."""
    # console.log equivalent [WP5-T-UH4-16]: claim-level audit begin.
    console_log("WP5-T-UH4-16", "UH4-16 claim-level audit begin")
    with open(os.path.join(REPO, "THEOREM_MINING_REPORT.md"), encoding="utf-8") as handle:
        report = handle.read()
    ok = ("FINITE_EXACT_BN_RESULTS" in report
          and "CANDIDATE_H_SURVIVES" not in report
          and git_diff_quiet("artifacts/hypotheses/hypothesis_ledger.json"))
    check("UH4-16", ok, "claim stays FINITE_EXACT_BN_RESULTS")


def test_uh4_17_path():
    """UH4-17: Path.md corrects the old prose and records the repair."""
    # console.log equivalent [WP5-T-UH4-17]: Path prose audit begin.
    console_log("WP5-T-UH4-17", "UH4-17 Path prose audit begin")
    with open(os.path.join(REPO, "Path.md"), encoding="utf-8") as handle:
        text = handle.read()
    stale = ("built for survivors only" in text
             or "UH-4 tables omitted under explicit NO-SUBJECTS rule" in text)
    fresh = ("WP-5 corrective compliance repair" in text
             and "REJECTED_EARLIER_AT_UH4" in text)
    check("UH4-17", (not stale) and fresh, "stale prose gone, repair recorded")


def test_uh4_18_exact():
    """UH4-18: all new authoritative calculations use exact arithmetic."""
    # console.log equivalent [WP5-T-UH4-18]: exactness static audit begin.
    console_log("WP5-T-UH4-18", "UH4-18 exactness audit begin")
    ok = True
    for rel in REPAIR_CODE:
        with open(os.path.join(REPO, rel), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Div):
                print("FLOATDIV %s line %d" % (rel, node.lineno))
                ok = False
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "float":
                print("FLOATCALL %s line %d" % (rel, node.lineno))
                ok = False
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in ("numpy", "scipy"):
                        print("FLOATLIB %s" % rel)
                        ok = False
    check("UH4-18", ok, "no float division/calls/libs in repair code")


def test_uh4_19_deterministic():
    """UH4-19: deterministic rerun gives identical UH-4 outputs."""
    # console.log equivalent [WP5-T-UH4-19]: determinism audit begin.
    console_log("WP5-T-UH4-19", "UH4-19 determinism audit begin")
    from python.reference import canonical as cn
    from python.reference import solve_small as sv
    import zstandard as zstd
    n = 3
    tables = sv.load_tables(os.path.join(REPO, "artifacts", "transitions", "n3"))
    reach = sv.load_reach(os.path.join(REPO, "artifacts", "reachability", "n3"),
                          tables.tree_count)
    csr = sv.build_csr(tables, reach)
    U, _ = cn.compute_U(csr, 2, 1)
    V, _ = cn.compute_V(csr, 2, 1)
    with open(os.path.join(bh_dir(3), "U.json.zst"), "rb") as handle:
        filed_u = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    with open(os.path.join(bh_dir(3), "V.json.zst"), "rb") as handle:
        filed_v = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    fu = {r["pair_id"]: int(r["U_scaled"]) for r in filed_u}
    fv = {r["pair_id"]: int(r["V_scaled"]) for r in filed_v}
    ok = all(U[i] == fu[pid] for i, pid in enumerate(csr.pids))
    ok = ok and all(V[i] == fv[pid] for i, pid in enumerate(csr.pids))
    raw = open(os.path.join(REPO, "artifacts", "hypotheses", "H-0001.uh4.json"),
               encoding="utf-8").read()
    again = json.dumps(json.loads(raw), sort_keys=True, indent=2) + "\n"
    ok = ok and (raw == again)
    check("UH4-19", ok, "recompute identical; serialization canonical")


def main(argv=None):
    """Run UH-4 corrective gates, exit nonzero on any failure."""
    t0 = __import__("time").time()
    # console.log equivalent [WP5-T-UH4-20]: suite start.
    console_log("WP5-T-UH4-20", "UH-4 corrective gate suite start")
    test_uh4_01_artifacts()
    test_uh4_02_unconfusable()
    test_uh4_03_independent()
    test_uh4_04_feasibility()
    test_uh4_05_verdicts()
    test_uh4_06_agreement()
    test_uh4_07_ladder_order()
    test_uh4_08_uh5_preserved()
    test_uh4_09_frozen_h()
    test_uh4_10_n8_firewall()
    test_uh4_11_h1_firewall()
    test_uh4_12_n8_unread()
    test_uh4_13_h1_unread()
    test_uh4_14_sealed()
    test_uh4_15_sa_bytes()
    test_uh4_16_claim()
    test_uh4_17_path()
    test_uh4_18_exact()
    test_uh4_19_deterministic()
    dt = __import__("time").time() - t0
    # console.log equivalent [WP5-T-UH4-21]: suite summary.
    console_log("WP5-T-UH4-21", "pass=%d fail=%d seconds=%.1f" % (len(PASS), len(FAIL), dt))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())