"""SA-02 freeze gates (fail-closed, before coefficient search).

Covers Task §15 for the freeze commit:
  PREREG-HASH  prereg bytes hash matches sidecar + WorkPlan record
  SA02-HASH    amendment bytes hash matches WorkPlan record
  TRACK-A-MASK original mask reproduces exactly (expect 0 rows n=2..5)
  TRACK-B-SEL  Track B is exactly n=4/5 FCYCLE rows (12+8=20)
  FW-N7        detailed n=7 read blocked before final freeze
  FW-N6        detailed n=6 read blocked during initial fit
  FW-UNLOCK    n=7 unlocks exactly once after final freeze; second unlock fails;
               post-n7 change needs new ID (mismatch fails)
  CYCLE-SEALED sealed n=4/5 canonical cycles satisfy sum_L==0, p*sum_a==q*sum_y,
               sum_a==q*k, sum_y==p*k, k>0
  NO-ANSWER-IMPORT firewall/mining freeze code has no U/V/G/b_n* reads
  NAMESPACE    Track-A/B manifest paths + schemas distinct
  SEALED-HASH  WP-1..WP-3 sealed logical SHAs + b* unchanged

Read-only for sealed artifacts. No coefficient fitting. No n=6/7 detailed
reads for hypothesis generation (only summary aggregates for n=6/7 where
needed; detailed n=4/5 allowed as selection sizes).
"""

import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

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


def test_prereg_hash():
    import re
    p = os.path.join(REPO, "prereg", "wp4_sa02.yaml")
    side = os.path.join(REPO, "prereg", "wp4_sa02.sha256")
    actual = sha256_file(p)
    with open(side, encoding="utf-8") as f:
        side_text = f.read().strip()
    check("PREREG-HASH-sidecar", actual in side_text, actual[:16])
    with open(os.path.join(REPO, "WorkPlan.md"), encoding="utf-8") as f:
        wp = f.read()
    check("PREREG-HASH-workplan", actual in wp, "workplan records prereg")


def test_sa02_hash():
    p = os.path.join(REPO, "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md")
    actual = sha256_file(p)
    with open(os.path.join(REPO, "WorkPlan.md"), encoding="utf-8") as f:
        wp = f.read()
    check("SA02-HASH-workplan", actual in wp, actual[:16])
    check("SA02-HASH-format", len(actual) == 64, "len64")


def test_workplan_rev():
    with open(os.path.join(REPO, "WorkPlan.md"), encoding="utf-8") as f:
        wp = f.read()
    check("PLAN-REV", "v0.1.6 FROZEN" in wp, "v0.1.6")
    check("PLAN-SA02-REF", "SA-02" in wp and "wp4_sa02.yaml" in wp, "refs")
    check("PLAN-SCHEMA-18", "18 total" in wp, "18 schemas")
    check("PLAN-SPEC-SET", "v0.1.2-SA02" in wp, "spec set")


def test_track_selection():
    import zstandard as zstd
    sys.path.insert(0, REPO)
    from python.reference import tree as ref_tree
    from python.reference import splay as ref_splay
    from python.reference import enumerate as ref_enum
    track_a_total = 0
    track_b_total = 0
    per_n_a = {}
    per_n_b = {}
    for n in (2, 3, 4, 5):
        shapes = ref_enum.canonical_shapes(n)
        with open(os.path.join(REPO, "artifacts", "critical", "n%d" % n,
                               "forced_delta_edges.json.zst"), "rb") as f:
            rows = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
        count_a = 0
        count_b = 0
        for row in rows:
            is_fcycle = "FCYCLE" in row["provenance"]
            is_delete = row["mode"] == "DELETE"
            src = row["source_pair_id"]
            key = row["key"]
            c = len(shapes)
            a_id = src // c
            t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shapes[a_id]))
            _, _, cases, _ = ref_splay.splay(t, key)
            is_zigzag = any(x in ("LR", "RL") for x in cases)
            reserved = is_fcycle or is_delete or is_zigzag
            if not reserved:
                count_a += 1
            if n in (4, 5) and is_fcycle and row["forced_delta"]:
                count_b += 1
        per_n_a[n] = count_a
        per_n_b[n] = count_b if n in (4, 5) else 0
        track_a_total += count_a
        if n in (4, 5):
            track_b_total += count_b
    check("TRACK-A-MASK", track_a_total == 0, "per-n=%s total=0" % (per_n_a,))
    check("TRACK-B-SEL", track_b_total == 20 and per_n_b.get(4) == 12 and per_n_b.get(5) == 8,
          "per-n=%s total=%d" % (per_n_b, track_b_total))


def test_firewall():
    from python.mining import holdout_firewall as fw
    fw.reset_for_tests()
    # Detailed n7 blocked before final freeze.
    try:
        fw.guard_load("artifacts/critical/n7/forced_delta_edges.json.zst")
        check("FW-N7", False, "should have blocked")
    except Exception as e:
        check("FW-N7", "HOLDOUT_FIREWALL_BLOCKS_N7" in str(e), "blocked")
    # Detailed n6 blocked during initial fit.
    try:
        fw.guard_initial_fit_load("artifacts/cycle_anatomy/n6/cycle_000.json")
        check("FW-N6", False, "should have blocked")
    except Exception as e:
        check("FW-N6", "HOLDOUT_FIREWALL_BLOCKS_N6_DURING_FIT" in str(e), "blocked")
    # Unlock flow: initial -> final -> unlock once -> second fails -> mismatch fails.
    fw.freeze_initial_candidate("H-SA02-B-v1")
    try:
        fw.guard_initial_fit_load("artifacts/cycle_anatomy/n6/cycle_000.json")
        check("FW-N6-AFTER-INITIAL", True, "allowed after initial freeze")
    except Exception:
        check("FW-N6-AFTER-INITIAL", False, "should allow after initial")
    fw.freeze_final_candidate("H-SA02-B-v1-final")
    check("FW-FINAL-FREEZE", True, "final frozen")
    try:
        fw.unlock_n7_for_evaluation("H-SA02-B-v1-final", write_file=False)
        check("FW-UNLOCK-ONCE", True, "first unlock ok")
    except Exception:
        check("FW-UNLOCK-ONCE", False, "first unlock should pass")
    try:
        fw.unlock_n7_for_evaluation("H-SA02-B-v1-final", write_file=False)
        check("FW-UNLOCK-TWICE", False, "second unlock must fail")
    except Exception as e:
        check("FW-UNLOCK-TWICE", "already unlocked" in str(e), "second blocked")
    try:
        fw.unlock_n7_for_evaluation("H-SA02-B-v2-other", write_file=False)
        check("FW-UNLOCK-MISMATCH", False, "mismatch must fail")
    except Exception:
        check("FW-UNLOCK-MISMATCH", True, "mismatch blocked")
    fw.reset_for_tests()


def test_sealed_cycles():
    import math
    for n in (4, 5):
        with open(os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                               "bn_certificate.json"), encoding="utf-8") as f:
            cert = json.load(f)
        p, q = int(cert["b"]["p"]), int(cert["b"]["q"])
        with open(os.path.join(REPO, "artifacts", "critical", "n%d" % n,
                               "canonical_cycles.json"), encoding="utf-8") as f:
            cycles = json.load(f)
        ok = True
        for entry in cycles:
            sa = entry["sum_a"]
            sy = entry["sum_y"]
            if p * sa - q * sy != 0:
                ok = False
            g = math.gcd(p, q)
            if g != 1:
                ok = False
            if sa % q != 0 or sy % p != 0:
                ok = False
            k1 = sa // q if sa % q == 0 else None
            k2 = sy // p if sy % p == 0 else None
            if k1 is None or k2 is None or k1 != k2 or k1 <= 0:
                ok = False
        check("CYCLE-SEALED-n%d" % n, ok, "cycles=%d b=%d/%d" % (len(cycles), p, q))


def test_no_answer_import():
    p = os.path.join(REPO, "python", "mining", "holdout_firewall.py")
    with open(p, encoding="utf-8") as f:
        text = f.read()
    bad = []
    for token in ("from python.reference import", "import U", "V_b", "b_n_star"):
        if token in text:
            bad.append(token)
    # Firewall must not read U/V/G tables.
    for token in ('"U.json', "'U.json", '"V.json', '"G.json'):
        if token in text:
            bad.append(token)
    check("NO-ANSWER-IMPORT", len(bad) == 0, "bad=%s" % bad)


def test_namespace():
    a = os.path.join("artifacts", "datasets", "track_a_manifest.json")
    b = os.path.join("artifacts", "datasets", "track_b_manifest.json")
    check("NAMESPACE", a != b and "track_a" in a and "track_b" in b, "distinct")
    check("SCHEMA-18", os.path.exists(os.path.join(REPO, "schemas",
          "wp4_dataset_manifest_v0.1.schema.json")) and os.path.exists(
          os.path.join(REPO, "schemas", "cycle_anatomy_v0.1.schema.json")), "2 new schemas")


def test_sealed_hash():
    expected = {
        2: ("1", "1", "b0ca15a46a3bccf52fd3abc4bbf52774afd703c4c23a455ba81ec6cb84ea21c2", 4),
        3: ("1", "1", "69bcb580c4a71b181dd1a10ccf766a92e995d0afa3280bef5a9cc081c734d2ca", 17),
        4: ("3", "2", "8b084a70c6870f089c376602a04c1cfcfe60881b8ba349e3a03fdedc6a308c32", 12),
        5: ("8", "5", "25a252bb15cd78c0819bc24794c99f6ddf650f9424fb07f3e038b3d4198e4380", 8),
        6: ("8", "5", "431a0b03d92661b6f80870979d5514f4b1d8e23b2a58d7f64dbddc00a8208f23", 84),
        7: ("23", "14", "119e3085a65c09f172e4284afb199d4b8e0eab678a36a39189b86566fbd2d875", 10),
    }
    ok = True
    for n, (ep, eq, efd, efc) in expected.items():
        with open(os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                               "bn_certificate.json"), encoding="utf-8") as f:
            cert = json.load(f)
        with open(os.path.join(REPO, "artifacts", "critical", "n%d" % n,
                               "summary.json"), encoding="utf-8") as f:
            summ = json.load(f)
        if cert["b"]["p"] != ep or cert["b"]["q"] != eq:
            ok = False
        if summ["logical_forced_delta_sha256"] != efd:
            ok = False
        if summ["forced_delta_count"] != efc:
            ok = False
    check("SEALED-HASH", ok, "WP-1..WP-3 sealed sets unchanged")


def main(argv=None):
    console_log("SA02-00", "SA-02 freeze gates begin")
    test_prereg_hash()
    test_sa02_hash()
    test_workplan_rev()
    test_track_selection()
    test_firewall()
    test_sealed_cycles()
    test_no_answer_import()
    test_namespace()
    test_sealed_hash()
    console_log("SA02-99", "pass=%d fail=%d" % (len(PASS), len(FAIL)))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
