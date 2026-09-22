"""SA-04 corrective-freeze gates (fail-closed; NO WP-5 candidate synthesis here).

Covers Task section 16 (SA04-01..SA04-23) plus SA04-SEPH1 (clean-room audit
for the H1 independent twin). No hypothesis is synthesized: the only
candidate-like objects are TEMP-STATE freeze-logic exercises (H-TEST-*
pseudo-IDs, never written near production paths) and synthetic smoke
fixtures built inline (never bank records, never ledgered).

Detailed-n8 re-execution (SA04-13) reuses the frozen SA-03 H=0 test vector
with the production set still EMPTY (authorized self-test path); outputs
stay in memory. Full H1 bank replay (SA04-07) runs BOTH Splay
implementations over all 120,000 stored histories.
"""
import hashlib
import json
import os
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from python.n8_holdout import contract as C8
from python.n8_holdout import n8_firewall as N8FW
from python.n8_holdout import freeze as FZ
from python.holdout_bank import h1_firewall as H1FW
from python.holdout_bank import protocol as PROTO

PASS = []
FAIL = []


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
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def temp_state():
    fd, path = tempfile.mkstemp(prefix="sa04_", suffix=".json")
    os.close(fd)
    os.remove(path)
    return path


def test_sa03_untouched():
    for rel in ("SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3.md", "prereg/wp5_sa03.yaml",
                "python/n8_holdout/sweep.py", "python/n8_holdout/independent.py",
                "python/n8_holdout/n8_firewall.py", "python/n8_holdout/freeze.py"):
        _ = open(os.path.join(REPO, rel), "rb").read()
    check("SA04-01", sha256_file(os.path.join(REPO, "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3.md")) ==
          "BB407FAC46DB30FA58F8833E513152FC10182AC931AFD84DDB0C29B0217E25E1"
          and sha256_file(os.path.join(REPO, "prereg", "wp5_sa03.yaml")) ==
          "FCE7F8C0A32F3590B3EFA7A6487330B7F11867DDF0D377D654E305ECA365BD73",
          "SA-03 bytes/hash unchanged")


def test_era_ban():
    import jsonschema
    sch = json.load(open(os.path.join(REPO, "schemas", "wp5_post_n7_candidate_v0.1.schema.json"),
                         encoding="utf-8"))
    base = {"hypothesis_id": "H-SA04-BAD", "formula_H": "H=0", "tie_breaking_rules": "none",
            "normalization": "H(T,T)=0", "structural_definitions": "test",
            "b_H": {"p": "23", "q": "14"}, "candidate_source_hash": "x",
            "evaluation_source_hash": "y", "schema_version": "v0.1", "provenance": "test",
            "development_evidence": [], "og_diagnostics": {}, "uh_status": {},
            "candidate_era": "POST_N7", "n7_status": "REVEALED_DEVELOPMENT_DATA",
            "untouched_sizes": [7], "state_only": True, "uses_history": False,
            "uses_b_n_star_table": False}
    try:
        jsonschema.validate(dict(base, untouched_sizes=[7, 8]), sch)
        check("SA04-02", False, "fresh/untouched n8 claim validated")
    except Exception:
        check("SA04-02", True, "fresh n8 + untouched-7 claims schema-rejected")


def test_canary_ledger():
    led = json.load(open(os.path.join(REPO, "artifacts", "audits", "contamination_ledger.json"),
                         encoding="utf-8"))
    cats = [e["category"] for e in led["entries"]]
    rec = next(e for e in led["entries"] if e["category"] == "N8_CANARY_RECLASSIFIED_SA04")
    det = rec["detail"]["revealed_by_canary"]
    ok = ("N8_CANARY_RECLASSIFIED_SA04" in cats
          and det["keep_max_scaled"] == "89" and det["delete_max_scaled"] == "-23"
          and det["keep_argmax"] == [1429, 0, 8] and det["delete_argmax"] == [0, 1, 8])
    check("SA04-03", ok, "canary facts preserved in ledger")


def test_n8_still_firewalled():
    try:
        N8FW.guard_n8_read("artifacts/transitions/n8/forward.bin.zst")
        check("SA04-04", False, "unrevealed n8 detail readable")
    except Exception as e:
        check("SA04-04", "N8_FIREWALL_BLOCKS" in str(e), "still blocked")


def bank_manifest():
    return json.load(open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout",
                                       "bank_manifest.json"), encoding="utf-8"))


def test_bank_counts():
    m = bank_manifest()
    ok = (m["bank_id"] == "HOLDOUT-H1-v0.1" and m["sizes"] == [9, 10, 12, 16, 24, 32]
          and all(v["states"] == 20000 for v in m["per_size"].values())
          and m["total_states"] == 120000
          and m["future_edge_evaluations_exact"] == 4120000)
    check("SA04-05", ok, "120,000 states")
    check("SA04-06", m["sizes"] == [9, 10, 12, 16, 24, 32], "sizes exact")


def test_bank_schema():
    import jsonschema
    import zstandard as zstd
    sch = json.load(open(os.path.join(REPO, "schemas", "wp5_holdout_bank_v0.1.schema.json"),
                         encoding="utf-8"))
    m = bank_manifest()
    try:
        jsonschema.validate(m, sch)
        ok = True
    except Exception as e:
        print("SCHEMA-FAIL bank manifest", str(e)[:200])
        ok = False
    with open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout", "n9",
                           "bank.json.zst"), "rb") as f:
        rec0 = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))["states"][0]
    for k in ("init_A_shape", "init_B_shape", "actions", "end_A_shape", "end_B_shape",
              "stratum", "history_length"):
        ok = ok and k in rec0
    check("SA04-SCHEMA", ok, "bank manifest + record conformance")


def test_bank_schema():
    import jsonschema
    import zstandard as zstd
    sch = json.load(open(os.path.join(REPO, "schemas", "wp5_holdout_bank_v0.1.schema.json"),
                         encoding="utf-8"))
    m = bank_manifest()
    try:
        jsonschema.validate(m, sch)
        ok = True
    except Exception as e:
        print("SCHEMA-FAIL bank manifest", str(e)[:200])
        ok = False
    with open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout", "n9",
                           "bank.json.zst"), "rb") as f:
        rec0 = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))["states"][0]
    for k in ("init_A_shape", "init_B_shape", "actions", "end_A_shape", "end_B_shape",
              "stratum", "history_length"):
        ok = ok and k in rec0
    for rel in ("schemas/wp5_post_n7_candidate_v0.1.schema.json",
                "schemas/n8_pair_access_holdout_v0.1.schema.json",
                "schemas/wp5_holdout_result_v0.1.schema.json"):
        try:
            jsonschema.Draft202012Validator.check_schema(
                json.load(open(os.path.join(REPO, rel), encoding="utf-8")))
        except Exception as e:
            print("SCHEMA-FAIL meta", rel, str(e)[:200])
            ok = False
    check("SA04-SCHEMA", ok, "bank manifest + record + meta-schemas")


def test_bank_commitment():
    import zstandard as zstd
    parts = []
    for n in (9, 10, 12, 16, 24, 32):
        with open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout", "n%d" % n,
                               "bank.json.zst"), "rb") as f:
            blob = zstd.ZstdDecompressor().decompress(f.read())
        parts.append(blob)
        recs = json.loads(blob.decode("utf-8"))
        if len(recs["states"]) != 20000 or recs["n"] != n or recs["bank_id"] != "HOLDOUT-H1-v0.1":
            check("SA04-08", False, "bank file mismatch n=%d" % n)
            return
    recomputed = hashlib.sha256(b"".join(parts)).hexdigest()
    m = bank_manifest()
    with open(os.path.join(REPO, "prereg", "wp5_sa04.yaml"), encoding="utf-8") as f:
        prereg = f.read()
    # Hex case carries no value info; compare canonically uppercased.
    check("SA04-08", recomputed.upper() == m["bank_commitment_sha256"].upper()
          and recomputed.upper() in prereg, recomputed[:16].upper())


def test_bank_synthesis_blocked():
    hits = H1FW.assert_no_holdout_access(
        ["python/mining", "python/n8_holdout", "python/reference", "python/audit"])
    check("SA04-09", hits == [], "synthesis namespaces clean")
    try:
        H1FW.guard_bank_read("artifacts/wp5/h1_holdout/n9/bank.json.zst")
        check("SA04-09-guard", False, "bank read allowed")
    except Exception as e:
        check("SA04-09-guard", "H1_FIREWALL_BLOCKS" in str(e), "bank blocked")


def test_bank_aggregates():
    m = bank_manifest()
    ok = all(k in m for k in ("bank_id", "sizes", "total_states",
                              "future_edge_evaluations_exact", "bank_commitment_sha256"))
    try:
        H1FW.guard_bank_read("artifacts/wp5/h1_holdout/bank_manifest.json")
        ok = ok and True
    except Exception:
        ok = False
    check("SA04-10", ok, "aggregates visible, no case data")


def test_multiplicity_temp():
    sp = temp_state()
    tp = sp + ".set.json"
    H1FW  # firewall untouched by candidate-set logic (separate module owns it)
    from python.n8_holdout import n8_firewall as TFW
    TFW.init_empty_state(state_path=sp, set_path=tp)
    e1 = FZ.new_set_entry("H-TEST-A", "a" * 64, "b" * 64, (23, 14))
    e2 = FZ.new_set_entry("H-TEST-B", "c" * 64, "d" * 64, (23, 14))
    TFW.freeze_candidate_set([e1, e2], state_path=sp, set_path=tp)
    check("SA04-11", True, "temp set frozen pre-unlock")
    TFW.unlock("H-TEST-A", state_path=sp, set_path=tp)
    with open(tp, encoding="utf-8") as f:
        cur = json.load(f)
    cur["candidates"].append(FZ.new_set_entry("H-TEST-C", "e" * 64, "f" * 64, (23, 14)))
    with open(tp, "w", encoding="utf-8") as f:
        json.dump(cur, f, sort_keys=True)
        f.write("\n")
    try:
        TFW.assert_set_unchanged(state_path=sp, set_path=tp)
        check("SA04-12", False, "post-unlock addition undetected")
    except Exception as e:
        check("SA04-12", "MODIFICATION" in str(e), "addition detected")
    for p in (sp, tp):
        if os.path.exists(p):
            os.remove(p)


def test_ev8_edge_count():
    from python.n8_holdout import sweep as S
    n, C, pids, after, cost = S.load_domain(
        os.path.join(REPO, "artifacts", "transitions", "n8"),
        os.path.join(REPO, "artifacts", "reachability", "n8"))
    out = S.sweep_pair_access(pids, C, n, after, cost, lambda _p: 0, 1, 23, 14)
    check("SA04-13", out["edge_count"] == 32718400, "EV-8 edges exact")
    check("SA04-15", FZ.verdict_for(out["keep_max"], out["delete_max"],
                                    out["norm_count"], out["nonneg_count"]) == "REJECTED",
          "positive residual rejects")


def test_h1_edge_identity():
    m = bank_manifest()
    total = sum(2 * m["per_size"][str(n)]["states"] * n for n in m["sizes"])
    check("SA04-14", total == 4120000 == m["future_edge_evaluations_exact"],
          "H1 edges exact from metadata (no candidate needed)")


def test_h1_verdict_rules():
    check("SA04-16", PROTO.uh6_verdict("PASS", "REJECTED", True) == "REJECTED"
          and PROTO.uh6_verdict("REJECTED", "PASS", True) == "REJECTED",
          "positive residual on either rejects")
    check("SA04-17", PROTO.uh6_verdict("PASS", "PASS", True) == "UH-6_PASS_FRESH_H1"
          and PROTO.uh6_verdict("PASS", "SKIP", True) != "UH-6_PASS_FRESH_H1",
          "EV-8 alone never UH-6")
    check("SA04-18", PROTO.uh6_verdict("PASS", "PASS", True) == "UH-6_PASS_FRESH_H1"
          and PROTO.uh6_verdict("PASS", "PASS", False) != "UH-6_PASS_FRESH_H1",
          "independent pass required")


def skeleton_node_count(shape_str):
    from python.holdout_bank import independent as IND
    def count(node):
        return 0 if node == () else 1 + count(node[0]) + count(node[1])
    return count(IND.parse_shape(shape_str))


def smoke_fixture():
    """Hand-built diagonal-start legal histories at n=4 (NOT bank records).

    Every shape is node-count asserted (fail-closed against fixture typos).
    """
    fix = [
        ("((((..).).).)", "((((..).).).)", [["KEEP", 2], ["DELETE", 1], ["KEEP", 3]]),
        ("(((..)(..)).)", "(((..)(..)).)", [["DELETE", 2], ["KEEP", 4]]),
        ("(.(.(.(..))))", "(.(.(.(..))))", [["KEEP", 1], ["KEEP", 4], ["DELETE", 3], ["KEEP", 2]]),
    ]
    for a, b, _acts in fix:
        assert skeleton_node_count(a) == 4 and skeleton_node_count(b) == 4, (a, b)
    return fix


def test_smoke_agreement():
    from python.holdout_bank import evaluate as EV
    from python.holdout_bank import independent as IND
    from python.reference import tree as RT
    from python.reference import splay as RS
    from python.reference import enumerate as RE
    zero = lambda _A, _B, _n: 0
    for init_a, init_b, actions in smoke_fixture():
        A = RT.assign_inorder_keys(RT.parse_shape(init_a))
        B = RT.assign_inorder_keys(RT.parse_shape(init_b))
        acts = [(0 if m == "KEEP" else 1, k) for m, k in actions]
        # Primary replay must reproduce a legal end state (sanity).
        ea, eb = EV.replay_history(init_a, init_b, actions, RT.parse_shape,
                                   RT.assign_inorder_keys, RS.splay, RE.keyed_to_shape)
        ia, ib = IND.replay_history_ind(init_a, init_b, actions)
        if (ea, eb) != (ia, ib):
            check("SA04-19", False, "replay mismatch")
            return
    states = []
    for init_a, init_b, actions in smoke_fixture():
        ea, eb = EV.replay_history(init_a, init_b, actions, RT.parse_shape,
                                   RT.assign_inorder_keys, RS.splay, RE.keyed_to_shape)
        states.append((ea, eb))
    p = EV.evaluate_states(states, 4, zero, 1, 23, 14, RS.splay,
                           RT.parse_shape, RT.assign_inorder_keys, RE.keyed_to_shape)
    q = IND.evaluate_states_ind(states, 4, lambda _A, _B, _n: 0, 1, 23, 14)
    check("SA04-19", p["edge_count"] == q["edge_count"] == 2 * len(states) * 4
          and p["keep_max"] == q["keep_max"] and p["delete_max"] == q["delete_max"]
          and p["keep_argmax"] == q["keep_argmax"] and p["delete_argmax"] == q["delete_argmax"],
          "primary==independent on smoke fixture")


def test_bank_replay():
    """SA04-07: every H1 state replayed by BOTH Splay implementations."""
    import zstandard as zstd
    from python.reference import tree as RT
    from python.reference import splay as RS
    from python.reference import enumerate as RE
    from python.holdout_bank import independent as IND
    total = 0
    for n in (9, 10, 12, 16, 24, 32):
        with open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout", "n%d" % n,
                               "bank.json.zst"), "rb") as f:
            recs = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))["states"]
        if len(recs) != 20000:
            check("SA04-07", False, "count n=%d" % n)
            return
        bad = 0
        for r in recs:
            total += 1
            if r["init_A_shape"] != r["init_B_shape"]:
                bad += 1
                continue
            ea, eb = EV_replay(r)
            ia, ib = IND.replay_history_ind(r["init_A_shape"], r["init_B_shape"], r["actions"])
            if ea != r["end_A_shape"] or eb != r["end_B_shape"]:
                bad += 1
            elif ia != r["end_A_shape"] or ib != r["end_B_shape"]:
                bad += 1
                console_log("SA04-07-IND", "independent mismatch n=%d" % n)
                break
        console_log("SA04-07-n%d" % n, "replayed %d bad=%d" % (len(recs), bad))
        if bad:
            check("SA04-07", False, "replay failures n=%d" % n)
            return
    check("SA04-07", total == 120000, "120,000 histories legal, dual-verified")


def EV_replay(r):
    from python.holdout_bank import evaluate as EV
    from python.reference import tree as RT
    from python.reference import splay as RS
    from python.reference import enumerate as RE
    return EV.replay_history(r["init_A_shape"], r["init_B_shape"], r["actions"],
                             RT.parse_shape, RT.assign_inorder_keys, RS.splay,
                             RE.keyed_to_shape)


def test_descendant_rule():
    check("SA04-20", (not PROTO.h1_untouched_claim_valid([9], True))
          and (not PROTO.h1_untouched_claim_valid([7], False))
          and PROTO.h1_untouched_claim_valid([9], False)
          and PROTO.h1_untouched_claim_valid([], True), "descendant claims")


def test_prereg_sa04():
    actual = sha256_file(os.path.join(REPO, "prereg", "wp5_sa04.yaml"))
    with open(os.path.join(REPO, "prereg", "wp5_sa04.sha256"), encoding="utf-8") as f:
        sidecar = f.read().strip()
    with open(os.path.join(REPO, "WorkPlan.md"), encoding="utf-8") as f:
        wp = f.read()
    led = json.load(open(os.path.join(REPO, "prereg", "ledger.json"), encoding="utf-8"))
    rec = [x for x in led["files"] if x["file"] == "wp5_sa04.yaml"]
    check("SA04-PREREG", actual in sidecar and actual in wp
          and rec and rec[0]["sha256"] == actual, actual[:16])


def test_no_synthesis():
    led = json.load(open(os.path.join(REPO, "artifacts", "hypotheses", "hypothesis_ledger.json"),
                         encoding="utf-8"))
    ids = sorted(h["hypothesis_id"] for h in led["hypotheses"])
    fw = json.load(open(os.path.join(REPO, "artifacts", "wp5", "sa03", "n8_firewall.json"),
                        encoding="utf-8"))
    cs = json.load(open(os.path.join(REPO, "artifacts", "wp5", "sa03", "n8_candidate_set.json"),
                        encoding="utf-8"))
    import glob as gb
    holdout_dir = os.path.join(REPO, "artifacts", "wp5", "sa03", "holdout")
    check("SA04-23", ids == ["H-SA02-B-v1", "H-SA02-B-v1-final", "H-SA02-C-1", "H-SA02-C-2"]
          and fw.get("state") == "EMPTY" and cs.get("candidates") == []
          and not os.path.exists(holdout_dir)
          and [f for f in gb.glob(os.path.join(REPO, "artifacts", "hypotheses", "H-SA*.json"))
               if os.path.basename(f) not in ("H-SA02-B-v1.json", "H-SA02-B-v1-final.json",
                                              "H-SA02-C-1.json", "H-SA02-C-2.json")] == [],
          "zero WP-5 candidates synthesized")


def test_preservation():
    # Read-only pins reuse: parse the pins dict source without executing the module.
    text = open(os.path.join(REPO, "tests", "test_sa03_freeze.py"), encoding="utf-8").read()
    start = text.find("    pins = {")
    end = text.find("\n    }", start)
    pins = eval(text[start + len("    pins = "):end + len("\n    }")].strip())
    ok = True
    for rel, exp in pins.items():
        if sha256_file(os.path.join(REPO, rel)) != exp:
            print("PIN-MISMATCH", rel)
            ok = False
    check("SA04-21", ok, "%d sealed pins unchanged" % len(pins))
    check("SA04-22", sha256_file(os.path.join(REPO, "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md")) ==
          pins["SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md"]
          and sha256_file(os.path.join(REPO, "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md")) ==
          pins["SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md"]
          and sha256_file(os.path.join(REPO, "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3.md")) ==
          "BB407FAC46DB30FA58F8833E513152FC10182AC931AFD84DDB0C29B0217E25E1",
          "SA-01/02/03 bytes unchanged")


def test_separation():
    import ast
    text = open(os.path.join(REPO, "python", "holdout_bank", "independent.py"),
                encoding="utf-8").read()
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
    check("SA04-SEPH1", not bad and not uses_sys_path, "H1 clean-room imports")


def main(argv=None):
    console_log("SA04-00", "SA-04 corrective-freeze gates begin (no synthesis)")
    test_sa03_untouched()
    test_era_ban()
    test_canary_ledger()
    test_n8_still_firewalled()
    test_bank_counts()
    test_bank_schema()
    test_bank_commitment()
    test_prereg_sa04()
    test_bank_synthesis_blocked()
    test_bank_aggregates()
    test_multiplicity_temp()
    test_ev8_edge_count()
    test_h1_edge_identity()
    test_h1_verdict_rules()
    test_smoke_agreement()
    test_bank_replay()
    test_descendant_rule()
    test_no_synthesis()
    test_preservation()
    test_separation()
    console_log("SA04-99", "pass=%d fail=%d" % (len(PASS), len(FAIL)))
    return 0 if not FAIL else 1


def test_sa03_untouched():
    check("SA04-01", sha256_file(os.path.join(REPO, "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3.md")) ==
          "BB407FAC46DB30FA58F8833E513152FC10182AC931AFD84DDB0C29B0217E25E1"
          and sha256_file(os.path.join(REPO, "prereg", "wp5_sa03.yaml")) ==
          "FCE7F8C0A32F3590B3EFA7A6487330B7F11867DDF0D377D654E305ECA365BD73",
          "SA-03 bytes/hash unchanged")


if __name__ == "__main__":
    sys.exit(main())
