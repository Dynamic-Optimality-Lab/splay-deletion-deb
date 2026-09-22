"""SA-03 freeze gates (fail-closed; NO WP-5 candidate synthesis here).

Covers Task section 19 (SA03-01..SA03-20) plus SA03-SEP (separation audit),
SA03-UH3 (feasibility gate machinery) and SA03-AGREE4 (n=4 cross-check smoke).

The ONLY detailed-n8 execution in this file is the frozen machinery
self-test with the degenerate H=0 TEST VECTOR while the production candidate
set is EMPTY (nothing to adapt; outputs in-memory only, never written under
artifacts/wp5/sa03/holdout/). Firewall state-machine tests use isolated temp
state files and never touch the production n8_firewall.json.
"""
import hashlib
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from python.n8_holdout import contract as C
from python.n8_holdout import n8_firewall as FW
from python.n8_holdout import freeze as FZ
from python.n8_holdout import sweep as S

PASS = []
FAIL = []
N8_PRIMARY = {}
N8_INDEP = {}


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def check(test_id, cond, detail=""):
    if cond:
        PASS.append(test_id)
        console_log(test_id, "PASS %s" % detail)
    else:
        FAIL.append(test_id)
        console_log(test_id, "FAIL %s" % detail)


def sha256_file(path):
    # UPPERCASE convention matches WorkPlan headers + .sha256 sidecars (SA-02 precedent).
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def temp_state():
    fd, path = tempfile.mkstemp(prefix="n8fw_", suffix=".json")
    os.close(fd)
    os.remove(path)
    return path


def test_era_labels():
    import jsonschema
    sch = json.load(open(os.path.join(REPO, "schemas", "wp5_post_n7_candidate_v0.1.schema.json"),
                         encoding="utf-8"))
    claiming = {"hypothesis_id": "H-SA03-BAD", "formula_H": "H=0", "tie_breaking_rules": "none",
                "normalization": "H(T,T)=0", "structural_definitions": "none",
                "b_H": {"p": "23", "q": "14"}, "candidate_source_hash": "x",
                "evaluation_source_hash": "y", "schema_version": "v0.1", "provenance": "test",
                "development_evidence": [], "og_diagnostics": {}, "uh_status": {},
                "candidate_era": "POST_N7", "n7_status": "REVEALED_DEVELOPMENT_DATA",
                "untouched_sizes": [7], "state_only": True, "uses_history": False,
                "uses_b_n_star_table": False}
    try:
        jsonschema.validate(claiming, sch)
        check("SA03-01", False, "untouched-7 claim validated (must fail)")
    except Exception:
        check("SA03-01", True, "untouched-7 claim schema-rejected")
    led = json.load(open(os.path.join(REPO, "artifacts", "hypotheses", "hypothesis_ledger.json"),
                         encoding="utf-8"))
    by_id = {h["hypothesis_id"]: h for h in led["hypotheses"]}
    ok = (by_id["H-SA02-B-v1"]["sha256"] == "7b4079a65ddb698d3eefcd6ded72558932546107bb0357372a4ba1e1ec561b2f"
          and by_id["H-SA02-B-v1-final"]["sha256"] == "04bfacadfd28f69d7cb985adbe5e3ef2034c056782b665723067245c08e38d14"
          and by_id["H-SA02-C-1"]["status"] == "POST-n7-DEVELOPMENT"
          and by_id["H-SA02-C-2"]["status"] == "POST-n7-DEVELOPMENT")
    check("SA03-02", ok, "historical metadata unchanged")


def test_firewall_blocks():
    try:
        FW.guard_n8_read("artifacts/transitions/n8/forward.bin.zst")
        check("SA03-03", False, "detailed n8 read allowed pre-freeze")
    except Exception as e:
        check("SA03-03", "N8_FIREWALL_BLOCKS" in str(e), "blocked")
    agg_ok = True
    for rel in ("artifacts/transitions/n8/summary.json",
                "artifacts/reachability/n8/summary.json",
                "artifacts/wp5/sa03/n8_known_aggregates.json"):
        try:
            FW.guard_n8_read(rel)
        except Exception:
            agg_ok = False
    known = json.load(open(os.path.join(REPO, "artifacts", "wp5", "sa03",
                                        "n8_known_aggregates.json"), encoding="utf-8"))
    agg_ok = agg_ok and known["R_8_size"] == 2044900 and known["catalan_C_8"] == 1430
    check("SA03-04", agg_ok, "aggregates permitted + values pinned")


def test_freeze_semantics():
    sp = temp_state()
    tp = sp + ".set.json"
    try:
        FW.freeze_candidate_set([], state_path=sp, set_path=tp)
        check("SA03-07-empty", False, "empty set froze")
    except Exception as e:
        check("SA03-07-empty", "empty" in str(e).lower(), "empty set refused")
    FW.init_empty_state(state_path=sp, set_path=tp)
    try:
        FW.init_empty_state(state_path=sp, set_path=tp)
        check("SA03-SEED-ONCE", False, "re-seed allowed")
    except Exception:
        check("SA03-SEED-ONCE", True, "re-seed refused")
    doc = {"hypothesis_id": "H-TEST-T1", "formula_H": "H=0",
           "tie_breaking_rules": "none", "normalization": "H(T,T)=0",
           "structural_definitions": "test only", "b_H": {"p": "23", "q": "14"},
           "candidate_source_hash": "a", "evaluation_source_hash": "b",
           "schema_version": "v0.1", "provenance": "SA03 freeze self-test (never a hypothesis)",
           "development_evidence": ["n<=7 revealed"], "og_diagnostics": {},
           "uh_status": {"UH-0": "PASS", "UH-1": "PASS", "UH-2": "PASS",
                         "UH-3": "PASS", "UH-4": "SKIP", "UH-5": "PASS"},
           "candidate_era": "POST_N7", "n7_status": "REVEALED_DEVELOPMENT_DATA",
           "untouched_sizes": [], "state_only": True, "uses_history": False,
           "uses_b_n_star_table": False, "discovery_sizes": [4, 5], "heldout_sizes": []}
    frozen, digest = FZ.freeze_candidate_manifest(doc)
    check("SA03-05", FZ.verify_manifest_hash(frozen), "formula hash binds")
    tampered = dict(frozen)
    tampered["formula_H"] = "H=1"
    check("SA03-05-tamper", not FZ.verify_manifest_hash(tampered), "tamper detected")
    bh = dict(frozen)
    bh["b_H"] = {"p": "99", "q": "1"}
    check("SA03-06", not FZ.verify_manifest_hash(bh), "b_H change detected")
    st = FW.freeze_candidate_set(
        [FZ.new_set_entry("H-TEST-T1", digest, digest, (23, 14)),
         FZ.new_set_entry("H-TEST-T2", digest, digest, (23, 14))],
        state_path=sp, set_path=tp)
    check("SA03-07", True, "2-entry set frozen %s" % st[:16])
    holdout_dir = os.path.join(REPO, "artifacts", "wp5", "sa03", "holdout")
    noresults = (not os.path.exists(holdout_dir)
                 or not any(os.scandir(holdout_dir)))
    check("SA03-07-noresults", noresults, "no candidate results pre-exist")
    prod_set = json.load(open(os.path.join(REPO, "artifacts", "wp5", "sa03",
                                           "n8_candidate_set.json"), encoding="utf-8"))
    prod_fw = json.load(open(os.path.join(REPO, "artifacts", "wp5", "sa03",
                                          "n8_firewall.json"), encoding="utf-8"))
    check("SA03-07-prodempty", prod_set.get("candidates") == [] and prod_fw.get("state") == "EMPTY",
          "production set EMPTY, firewall EMPTY")
    FW.unlock("H-TEST-T1", state_path=sp, set_path=tp)
    try:
        FW.unlock("H-TEST-T1", state_path=sp, set_path=tp)
        check("SA03-08-unlock", False, "second unlock allowed")
    except Exception as e:
        check("SA03-08-unlock", "already" in str(e).lower() or "UNLOCKED" in str(e), "once-only")
    with open(tp, encoding="utf-8") as f:
        cur = json.load(f)
    cur["candidates"].append(FZ.new_set_entry("H-TEST-T3", digest, digest, (23, 14)))
    with open(tp, "w", encoding="utf-8") as f:
        json.dump(cur, f, sort_keys=True)
        f.write("\n")
    try:
        FW.assert_set_unchanged(state_path=sp, set_path=tp)
        check("SA03-08-tamper", False, "post-unlock addition undetected")
    except Exception as e:
        check("SA03-08-tamper", "MODIFICATION" in str(e), "tamper detected")
    try:
        FZ.assert_revision_identity(
            {"hypothesis_id": "H-X", "formula_sha256": "aa"},
            {"hypothesis_id": "H-X", "formula_sha256": "bb"})
        check("SA03-16", False, "same-ID revision allowed")
    except Exception:
        check("SA03-16", True, "same-ID revision forbidden")
    check("SA03-17", (not FZ.untouched_claim_valid([7], True))
          and (not FZ.untouched_claim_valid([8], True))
          and FZ.untouched_claim_valid([], True)
          and FZ.untouched_claim_valid([8], False), "untouched-claim rule")
    for p in (sp, tp):
        if os.path.exists(p):
            os.remove(p)


def test_uh3():
    recs = C.uh3_feasibility(23, 14)
    ok = all(r["verdict"] == "PASS" for r in recs) and len(recs) == 6
    for r in recs:
        p_n, q_n = C.load_bn_certificate_b(r["n"], REPO)
        if (p_n, q_n) != (int(r["b_n_star"]["p"]), int(r["b_n_star"]["q"])):
            ok = False
    check("SA03-UH3", ok, "b_H=23/14 feasible on sealed n=2..7")


def run_n8_selftest():
    """Frozen machinery self-test: H=0 test vector, EMPTY set, in-memory only."""
    FW.guard_n8_read("artifacts/transitions/n8/forward.bin.zst", test_vector=True)
    FW.guard_n8_read("artifacts/reachability/n8/reachable.json.zst", test_vector=True)
    n, C8, pids, after, cost = S.load_domain(
        os.path.join(REPO, "artifacts", "transitions", "n8"),
        os.path.join(REPO, "artifacts", "reachability", "n8"))
    zero = lambda _p: 0
    prim = S.sweep_pair_access(pids, C8, n, after, cost, zero, 1, 23, 14)
    from python.n8_holdout import independent as I
    n2, C2, pids2, nxt, pay = I.load_domain_ind(
        os.path.join(REPO, "artifacts", "transitions", "n8"),
        os.path.join(REPO, "artifacts", "reachability", "n8"))
    ind = I.sweep_ind(pids2, C2, n2, nxt, pay, lambda _p: 0, 1, 23, 14)
    N8_PRIMARY.update(prim)
    N8_INDEP.update(ind)
    # n=4 smoke agreement first (fail fast on machinery bugs).
    n4, C4, p4, a4, c4 = S.load_domain(
        os.path.join(REPO, "artifacts", "transitions", "n4"),
        os.path.join(REPO, "artifacts", "reachability", "n4"))
    p4out = S.sweep_pair_access(p4, C4, n4, a4, c4, zero, 1, 23, 14)
    from python.n8_holdout import independent as I2
    _n, _C, _p, _nx, _py = I2.load_domain_ind(
        os.path.join(REPO, "artifacts", "transitions", "n4"),
        os.path.join(REPO, "artifacts", "reachability", "n4"))
    i4out = I2.sweep_ind(_p, _C, _n, _nx, _py, lambda _p: 0, 1, 23, 14)
    agree4 = all(p4out[k] == i4out[k] for k in (
        "edge_count", "norm_count", "nonneg_count", "keep_max", "keep_argmax",
        "delete_max", "delete_argmax", "keep_pos_count", "delete_pos_count"))
    check("SA03-AGREE4", agree4, "n=4 primary==independent")


def test_n8_sweeps():
    p, i = N8_PRIMARY, N8_INDEP
    check("SA03-09", p["norm_count"] == 0 and p["norm_bad"] == [], "n8 normalization exact")
    check("SA03-10", p["nonneg_count"] == 0 and p["nonneg_bad"] == [], "n8 nonnegativity exact")
    check("SA03-11", p["keep_max"] == "89" and p["keep_argmax"] == [1429, 0, 8]
          and p["edge_count"] == 32718400, "KEEP max=89(cB=8,cA=1) edges=32718400")
    check("SA03-12", p["delete_max"] == "-23" and p["delete_argmax"] == [0, 1, 8]
          and p["edge_count"] == 32718400, "DELETE max=-23(cA=1) edges=32718400")
    check("SA03-13", p["edge_count"] == C.N8_EDGE_CHECKS == 2 * 8 * 2044900,
          "edge count == 2n|R_n|")
    agree = all(p[k] == i[k] for k in (
        "edge_count", "norm_count", "nonneg_count", "keep_max", "keep_argmax",
        "delete_max", "delete_argmax", "keep_pos_count", "delete_pos_count",
        "keep_cex", "delete_cex"))
    check("SA03-14", agree, "primary==independent on full n8")
    check("SA03-15", FZ.verdict_for(p["keep_max"], p["delete_max"], p["norm_count"],
                                   p["nonneg_count"]) == "REJECTED"
          and FZ.verdict_for("-5", "-1", 0, 0) == "UH-6_PASS_FINITE_N8",
          "positive residual forces REJECTED")


def test_preservation():
    pins = {
        "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md": "8B77278FF98F6AB5A3AA4D929A5787735F269647D5E3088CF4288F8ACF8C7726",
        "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md": "79C58ED0278A6F81FE42685955C2D50EEF9A6744CCD0A701B6FE8DF96EE41CDF",
        "artifacts/certificates/n2/bn_certificate.json": "2D398D546E64C45FF8C08CDF5589D641984B9445792BF0E0036AA370ED7F7610",
        "artifacts/certificates/n3/bn_certificate.json": "5BD738013F5BCAC7548A24E894C064B02DAAFE76C143235C1E5F06B4DCEF44AB",
        "artifacts/certificates/n4/bn_certificate.json": "CA26D7265A518C41DB0F8E011B955CD4D6A9F4DD3CC3ACF34F9D77DDB63B2310",
        "artifacts/certificates/n5/bn_certificate.json": "DD4199842BD34891236BCF3735DA9EC0422E362F2EAFEE02E5B47A0DC695FE2A",
        "artifacts/certificates/n6/bn_certificate.json": "70B8801FBC444C9ED249C85660E4629F68F593A63B48C22CF1F919168AE9F356",
        "artifacts/certificates/n7/bn_certificate.json": "4ED03273DDE286CDBFCA5CB7271EE7CB32192A7D5C491BE57809B145AE892535",
        "artifacts/critical/n2/summary.json": "C869327B1F5FB454BC492E2F2001E3004965B03C5C910D53B82F81A348E1BAA5",
        "artifacts/critical/n3/summary.json": "9FDC57FED96A2FCF830B2721D26BFF6F4E49A19644747F3ED0F202469AAA3C61",
        "artifacts/critical/n4/summary.json": "67159D261BC7354A37C646607B7D427FD27098CBB564D3B393012E7DDC7C8708",
        "artifacts/critical/n5/summary.json": "AEA3415451170A7CF90A936B976D14C862BDD4D7D66855883F827D36F8FF27EC",
        "artifacts/critical/n6/summary.json": "207A2F0C2887CE0C0952286CFD20D3AFF18A0844691BF4DD12C6026F26BB6221",
        "artifacts/critical/n7/summary.json": "E2CC1D03807CCAB4EEB2B7018F68EE9F28F7DFCF4303AE296AF7E8B8C3284933",
        "artifacts/datasets/track_a_manifest.json": "6CF9FC2ECFD2DCCEADCC8883B84853A1961E2EA173EC66A69AEA12260C42C3EA",
        "artifacts/datasets/track_b_manifest.json": "E639B33D749FFB263B396635BEB851D31114E19F1681970178A2BD8B51BCB33D",
        "artifacts/hypotheses/H-SA02-B-v1-final.json": "1AEF5D42163121537A44169F7AD0E8453D55AB2EEDF8BD633DF1B0356BB78A1E",
        "artifacts/hypotheses/H-SA02-B-v1.json": "DC96CABFCBBD3E6E722ACEB6BB6446C010B2A5B2A53AB1343D6C65BE4B44B005",
        "artifacts/reachability/n8/summary.json": "E5F3ACDA678956FCBE5DC3EBD38AD99C3AE9F2F454BF7D5129444E8C457F6A26",
        "artifacts/transitions/n8/summary.json": "E5BDBA8EF41AF2B4AD76E612F9E3473952E30CF203F44AAE4EFF9C7A58CE0CD5",
        "prereg/wp4_sa02.yaml": "BDE98934623B8EDCE00369F0C426E0DFE1358F158A688BA1EA2D885628B3B826",
    }
    ok = True
    for rel, exp in pins.items():
        if sha256_file(os.path.join(REPO, rel)) != exp:
            print("PIN-MISMATCH", rel)
            ok = False
    check("SA03-18", ok, "%d sealed pins unchanged" % len(pins))
    check("SA03-19", sha256_file(os.path.join(REPO, "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md")) ==
          pins["SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md"]
          and sha256_file(os.path.join(REPO, "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md")) ==
          pins["SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md"], "SA-01/SA-02 bytes unchanged")


def test_prereg():
    actual = sha256_file(os.path.join(REPO, "prereg", "wp5_sa03.yaml"))
    with open(os.path.join(REPO, "prereg", "wp5_sa03.sha256"), encoding="utf-8") as f:
        sidecar = f.read().strip()
    with open(os.path.join(REPO, "WorkPlan.md"), encoding="utf-8") as f:
        wp = f.read()
    check("SA03-20", actual in sidecar and actual in wp, actual[:16])
    sa03 = sha256_file(os.path.join(REPO, "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3.md"))
    check("SA03-HASH", sa03 in wp and len(sa03) == 64, sa03[:16])
    check("SA03-PLAN-REV", "v0.1.7 FROZEN" in wp and "20 total" in wp
          and "v0.1.3-SA03" in wp, "WorkPlan v0.1.7 + 20 schemas + SA-03")


def test_separation():
    import ast
    text = open(os.path.join(REPO, "python", "n8_holdout", "independent.py"),
                encoding="utf-8").read()
    # Precise rule (AST-level, docstring-proof): real imports may name only
    # stdlib json/os/sys/argparse plus zstandard (sealed-table reader).
    allowed = {"json", "os", "sys", "argparse", "zstandard"}
    bad = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in allowed:
                    bad.append(a.name)
        elif isinstance(node, ast.ImportFrom):
            bad.append(node.module or "<relative>")
    uses_sys_path = any(
        isinstance(n, ast.Attribute) and getattr(n.value, "id", "") == "sys"
        and n.attr == "path" for n in ast.walk(ast.parse(text)))
    check("SA03-SEP", not bad and not uses_sys_path, "clean-room imports")


def main(argv=None):
    console_log("SA03-00", "SA-03 freeze gates begin (no candidate synthesis)")
    test_era_labels()
    test_firewall_blocks()
    test_freeze_semantics()
    test_uh3()
    run_n8_selftest()
    test_n8_sweeps()
    test_preservation()
    test_prereg()
    test_separation()
    console_log("SA03-99", "pass=%d fail=%d" % (len(PASS), len(FAIL)))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
