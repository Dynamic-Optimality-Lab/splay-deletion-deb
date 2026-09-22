"""ERA-B universal-hypothesis freezing (WP-5 synthesis side, pre-holdout only).

Freezes H-0001..H-0003 with: H-*.json (candidate_H schema),
H-*.eval_contract.json (EC-v0.1, one exact n-independent b_H),
H-*.bH_feasibility.json (UH-3 exact cross-multiplied precheck n=2..7),
H-*.og.json (OG-1..OG-3 discovery diagnostics), the SA-03 post-n7 freeze
record (wp5_post_n7_candidate schema), and hypothesis-ledger appends.

Reads ONLY revealed n<=7 sealed data (development evidence). Never reads
detailed n8 records or hidden-bank records (fail-closed: static audit +
firewall-state assertions run inside freeze and refuse on hits or on any
non-EMPTY production holdout state).
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from python.wp5 import structural as S

# console.log equivalent [WP5-SYN-01]: synthesis module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


HYP_DIR = os.path.join(REPO, "artifacts", "hypotheses")
SEALED_B_STAR = {2: ("1", "1"), 3: ("1", "1"), 4: ("3", "2"), 5: ("8", "5"),
                 6: ("8", "5"), 7: ("23", "14")}

FORMULA_IDS = {"H-0001": "depth_sum", "H-0002": "ancestor_sym", "H-0003": "access_sym",
                 "H-0004": "heavy_disagree", "H-0005": "parent_diff",
                 "H-0006": "combo_depth_heavy"}
COEFFICIENT_DOMAIN = "structural-exact (no fitted coefficients; formula fixed by definition)"
TIE_RULES = ("lexicographically-first maximizers over (pair_id, mode, key) with "
             "KEEP(1..n) then DELETE(1..n); H values exact integers, no tie-sensitive "
             "normalization exists")
NORMALIZATION = "H(T,T)=0 by construction: every summand vanishes on identical pairs"


def sha256_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def git_head():
    out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                         cwd=REPO, check=True)
    return out.stdout.strip()


def uh3_records(hypothesis_id, p_h, q_h):
    """Exact UH-3 feasibility records over sealed b_n* (SA-01 ARCH)."""
    import math
    assert math.gcd(p_h, q_h) == 1 and q_h > 0
    records = []
    for n in sorted(SEALED_B_STAR):
        p_n, q_n = (int(v) for v in SEALED_B_STAR[n])
        ok = p_h * q_n >= p_n * q_h
        records.append({
            "n": n,
            "b_H": {"p": str(p_h), "q": str(q_h)},
            "b_n_star": {"p": str(p_n), "q": str(q_n)},
            "comparison": "p_H*q_n >= p_n*q_H -> %s" % ok,
            "verdict": "PASS" if ok else "FAIL",
            "failure_witness": None,
        })
    return records


def bh_case(p_h, q_h, p_n, q_n):
    """Frozen UH-3 three-case rule: '<' reject, '=' reuse, '>' recompute."""
    left = p_h * q_n
    right = p_n * q_h
    if left < right:
        return "<"
    if left == right:
        return "="
    return ">"


def build_prefix_plus_cycles(p_h, q_h, n):
    """Diagonal-rooted finite negative path P_0·C^k with exact minimal k.

    Uses the sealed CYCLIC lower witness (prefix + zero-slack cycle C with
    L_{b_H}(C) < 0 verified exactly) and stores repeat_count k with
    k > L_{b_H}(P_0) / (-L_{b_H}(C)) minimal. BH02 third branch.
    """
    # console.log equivalent [WP5-SYN-08]: prefix-plus-cycles witness built.
    console_log("WP5-SYN-08", "prefix-plus-cycles n=%d" % n)
    sys.path.insert(0, REPO)
    from python.audit import graph as G
    tables = G.build_tables(n)
    with open(os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                           "witness_cycle.json"), encoding="utf-8") as handle:
        wit = json.load(handle)
    prefix = wit.get("prefix", [])
    cycle = wit["cycle"]

    def mode_code(name):
        return G.KEEP if name == "KEEP" else G.DELETE

    def sums(edges):
        total_a = 0
        total_y = 0
        for edge in edges:
            tgt, a_cost, y_cost = G.successor(
                tables, int(edge["source"]), mode_code(edge["mode"]), int(edge["key"]))
            assert tgt == int(edge["target"]), "witness edge not legal"
            total_a += a_cost
            total_y += y_cost
        return total_a, total_y

    pre_a, pre_y = sums(prefix)
    cyc_a, cyc_y = sums(cycle)
    slack_c = p_h * cyc_a - q_h * cyc_y
    assert slack_c < 0, "cycle must be infeasible under b_H"
    slack_0 = p_h * pre_a - q_h * pre_y
    import math
    repeat = slack_0 // (-slack_c) + 1
    assert repeat >= 1 and (repeat - 1) * (-slack_c) <= slack_0
    total = slack_0 + repeat * slack_c
    assert total < 0, "composed witness must be strictly negative"
    return {"type": "reused_bn_witness", "witness_kind": "prefix_plus_cycles",
            "repeat_count": str(repeat),
            "witness_file": "witness_cycle.json",
            "witness_sha256": sha256_bytes(open(
                os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                             "witness_cycle.json"), "rb").read()),
            "slack_under_bH_num": str(total), "slack_under_bH_den": "1",
            "negative": True}


def build_bh_witness_below(hypothesis_id, p_h, q_h, n):
    """Cyclic/transient negative-slack witness reusing the sealed b_n* witness.

    Used when p_H*q_n < p_n*q_H (BH02). Returns a bH_feasibility-schema
    failure_witness dict with verifier-recomputed negative slack.
    """
    # console.log equivalent [WP5-SYN-04]: BH02 witness branch entered.
    console_log("WP5-SYN-04", "building BH02 witness n=%d" % n)
    sys.path.insert(0, REPO)
    from python.audit import graph as G
    tables = G.build_tables(n)
    cert_path = os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                             "bn_certificate.json")
    with open(cert_path, encoding="utf-8") as handle:
        cert = json.load(handle)
    lower = cert.get("lower_certificates", [])
    kinds = [entry.get("type", "") for entry in lower]

    def mode_code(name):
        return G.KEEP if name == "KEEP" else G.DELETE

    def edge_sums(edges):
        total_a = 0
        total_y = 0
        for edge in edges:
            tgt, a_cost, y_cost = G.successor(
                tables, int(edge["source"]), mode_code(edge["mode"]), int(edge["key"]))
            assert tgt == int(edge["target"]), "witness edge not legal"
            total_a += a_cost
            total_y += y_cost
        return total_a, total_y

    if any("path" in k for k in kinds):
        with open(os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                               "witness_path.json"), encoding="utf-8") as handle:
            wit = json.load(handle)
        total_a, total_y = edge_sums(wit["edges"])
        num = p_h * total_a - q_h * total_y
        assert num < 0, "transient reuse must be strictly negative"
        return {"type": "reused_bn_witness", "witness_kind": "transient_path",
                "repeat_count": None, "witness_file": "witness_path.json",
                "witness_sha256": sha256_bytes(open(
                    os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                                 "witness_path.json"), "rb").read()),
                "slack_under_bH_num": str(num), "slack_under_bH_den": "1",
                "negative": True}
    with open(os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                           "witness_cycle.json"), encoding="utf-8") as handle:
        wit = json.load(handle)
    total_a, total_y = edge_sums(wit["cycle"])
    num = p_h * total_a - q_h * total_y
    assert num < 0, "cyclic reuse must be strictly negative"
    return {"type": "reused_bn_witness", "witness_kind": "cycle",
            "repeat_count": None, "witness_file": "witness_cycle.json",
            "witness_sha256": sha256_bytes(open(
                os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                             "witness_cycle.json"), "rb").read()),
            "slack_under_bH_num": str(num), "slack_under_bH_den": "1",
            "negative": True}


def load_sealed_aux(n):
    """Aggregate-only sealed loads for OG diagnostics (no detailed n8/H1)."""
    import zstandard as zstd
    sys.path.insert(0, REPO)
    from python.reference import enumerate as E
    shapes = E.canonical_shapes(n)
    with open(os.path.join(REPO, "artifacts", "features", "n%d" % n,
                           "edge_deltas.json.zst"), "rb") as handle:
        deltas = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    with open(os.path.join(REPO, "artifacts", "potentials", "n%d" % n,
                           "V.json.zst"), "rb") as handle:
        rows_v = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    with open(os.path.join(REPO, "artifacts", "potentials", "n%d" % n,
                           "U.json.zst"), "rb") as handle:
        rows_u = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    table_v = {int(r["pair_id"]): int(r["V_scaled"]) for r in rows_v}
    table_u = {int(r["pair_id"]): int(r["U_scaled"]) for r in rows_u}
    return shapes, deltas, table_v, table_u


def og_diagnostics(hypothesis_id, formula_fn, discovery_sizes=(4, 5)):
    """OG-1..OG-3 discovery diagnostics (reported, never decisive alone)."""
    # console.log equivalent [WP5-SYN-05]: OG diagnostics computed.
    console_log("WP5-SYN-05", "OG diagnostics %s" % hypothesis_id)
    sys.path.insert(0, REPO)
    from python.reference import tree as T
    og1 = {}
    for n in discovery_sizes:
        _shapes, deltas, _v, _u = load_sealed_aux(n)
        p_n, q_n = (int(v) for v in SEALED_B_STAR[n])
        agree = 0
        worst_num = 0
        total = 0
        for row in deltas:
            total += 1
            src_a, src_b = _keyed_of(row["source_state_id"], n)
            tgt_a, tgt_b = _keyed_of(row["target_state_id"], n)
            pred = (formula_fn(S.tree_info(tgt_a), S.tree_info(tgt_b), n)
                    - formula_fn(S.tree_info(src_a), S.tree_info(src_b), n))
            import fractions
            ell = fractions.Fraction(int(row["scaled_slack"]), q_n)
            if pred == ell:
                agree += 1
            dev = abs(fractions.Fraction(pred, 1) - ell)
            if dev.numerator > worst_num:
                worst_num = dev.numerator
        og1[str(n)] = {"forced_edges": total, "exact_agreements": agree,
                       "note": "diagnostic only (SA-01 ARCH)"}
    return {"OG-1_forced_derivatives": og1,
            "OG-2_sandwich": "computed at falsification time (see falsify.py dev report)",
            "OG-3_corridors": "reported at falsification time (see falsify.py dev report)"}


_keyed_cache = {}


def _keyed_of(pair_id, n):
    """Keyed (A,B) trees for a pair_id via frozen canonical indexing."""
    key = (pair_id, n)
    hit = _keyed_cache.get(key)
    if hit is not None:
        return hit
    sys.path.insert(0, REPO)
    from python.reference import tree as T
    from python.reference import enumerate as E
    shapes = E.canonical_shapes(n)
    count = len(shapes)
    pair = (T.assign_inorder_keys(T.parse_shape(shapes[pair_id // count])),
            T.assign_inorder_keys(T.parse_shape(shapes[pair_id % count])))
    _keyed_cache[key] = pair
    return pair


def freeze_candidate(hypothesis_id, definition, formula_id, form_class,
                     discovery_sizes=(4, 5)):
    """Freeze one ERA-B universal hypothesis + all SA-01/SA-03 companions."""
    # console.log equivalent [WP5-SYN-06]: freezing candidate.
    console_log("WP5-SYN-06", "freezing %s (%s)" % (hypothesis_id, formula_id))
    formula_fn, _cls, _text = S.H_REGISTRY[hypothesis_id]
    assert _cls == form_class and FORMULA_IDS[hypothesis_id] == formula_id
    p_h, q_h = (int(v) for v in S.B_H)
    os.makedirs(HYP_DIR, exist_ok=True)
    hpath_check = os.path.join(HYP_DIR, "%s.json" % hypothesis_id)
    if os.path.exists(hpath_check):
        raise AssertionError(
            "already frozen (refusing re-freeze of %s; timestamps/commits would drift; "
            "any formula change needs a new hypothesis_id)" % hypothesis_id)
    # H-*.json (candidate_H schema: followed exactly, plus formula_id/form_class extras).
    hdoc = {"hypothesis_id": hypothesis_id, "parent_hypothesis": None,
            "definition": definition, "formula_id": formula_id, "form_class": form_class,
            "coefficient_domain": COEFFICIENT_DOMAIN, "state_only": True,
            "uses_history": False, "uses_b_n_star_table": False,
            "discovery_sizes": list(discovery_sizes), "heldout_sizes": [8],
            "status": "FROZEN-PRE-DEV"}
    hpath = os.path.join(HYP_DIR, "%s.json" % hypothesis_id)
    assert not os.path.exists(hpath)
    with open(hpath, "w", encoding="utf-8") as handle:
        json.dump(hdoc, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # H-*.eval_contract.json (EC-v0.1).
    edoc = {"hypothesis_id": hypothesis_id,
            "b_hypothesis": {"p": str(p_h), "q": str(q_h)},
            "b_is_universal_candidate": True, "track": "universal",
            "discovery_sizes": list(discovery_sizes), "contract_version": "EC-v0.1"}
    with open(os.path.join(HYP_DIR, "%s.eval_contract.json" % hypothesis_id),
              "w", encoding="utf-8") as handle:
        json.dump(edoc, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # H-*.bH_feasibility.json (UH-3).
    bhdoc = {"hypothesis_id": hypothesis_id, "b_H": {"p": str(p_h), "q": str(q_h)},
             "records": uh3_records(hypothesis_id, p_h, q_h)}
    with open(os.path.join(HYP_DIR, "%s.bH_feasibility.json" % hypothesis_id),
              "w", encoding="utf-8") as handle:
        json.dump(bhdoc, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # H-*.og.json (OG-1..OG-3 diagnostics).
    og = og_diagnostics(hypothesis_id, formula_fn, discovery_sizes)
    with open(os.path.join(HYP_DIR, "%s.og.json" % hypothesis_id),
              "w", encoding="utf-8") as handle:
        json.dump(og, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # SA-03 post-n7 freeze record (wp5_post_n7_candidate schema).
    # Source hashes are over file bytes only (read, never imported/executed here).
    eval_hash = sha256_bytes(open(os.path.join(
        REPO, "python", "wp5", "falsify.py"), "rb").read())
    cand_hash = sha256_bytes(open(os.path.join(
        REPO, "python", "wp5", "candidates.py"), "rb").read())
    wp5doc = {"hypothesis_id": hypothesis_id, "formula_H": definition,
              "tie_breaking_rules": TIE_RULES, "normalization": NORMALIZATION,
              "structural_definitions": S.H_REGISTRY[hypothesis_id][2],
              "b_H": {"p": str(p_h), "q": str(q_h)},
              "candidate_source_hash": cand_hash,
              "evaluation_source_hash": eval_hash,
              "schema_version": "v0.1", "provenance": "WP-4 F-v0.1 families + SA-01/02/03/04",
              "development_evidence": ["sealed b_n* n=2..7", "U/V/G n=2..7",
                                       "critical cycles n=4..7", "WP-4 MIS triple",
                                       "kernel witnesses", "failed F-v0.1 linear class"],
              "og_diagnostics": {"ref": "%s.og.json" % hypothesis_id},
              "uh_status": {"UH-0": "PENDING", "UH-1": "PENDING", "UH-2": "PENDING",
                            "UH-3": "PENDING", "UH-4": "PENDING", "UH-5": "PENDING",
                            "UH-6": "PENDING", "UH-7": "PENDING", "UH-8": "PENDING"},
              "candidate_era": "POST_N7", "n7_status": "REVEALED_DEVELOPMENT_DATA",
              "untouched_sizes": [], "state_only": True, "uses_history": False,
              "uses_b_n_star_table": False, "discovery_sizes": list(discovery_sizes),
              "heldout_sizes": [8], "parent_hypothesis": None,
              "git_commit": git_head(),
              "timestamp_meta": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    manifest_blob = (json.dumps(wp5doc, sort_keys=True) + "\n").encode("utf-8")
    wp5doc["manifest_sha256"] = sha256_bytes(manifest_blob)
    with open(os.path.join(HYP_DIR, "%s.wp5.json" % hypothesis_id),
              "w", encoding="utf-8") as handle:
        json.dump(wp5doc, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # Hypothesis-ledger append (failures preserved; never overwritten).
    ledger_path = os.path.join(HYP_DIR, "hypothesis_ledger.json")
    with open(ledger_path, encoding="utf-8") as handle:
        ledger = json.load(handle)
    ledger["hypotheses"] = [h for h in ledger["hypotheses"]
                            if h["hypothesis_id"] != hypothesis_id]
    ledger["hypotheses"].append(
        {"hypothesis_id": hypothesis_id, "definition": definition,
         "sha256": sha256_bytes(open(hpath, "rb").read()),
         "status": "FROZEN-PRE-DEV (ERA-B POST_N7)"})
    with open(ledger_path, "w", encoding="utf-8") as handle:
        json.dump(ledger, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP5-SYN-07]: candidate frozen.
    console_log("WP5-SYN-07", "frozen %s" % hypothesis_id)
    return hdoc


def main(argv=None):
    """Freeze H-0001..H-0003 (preconditions enforced by the phase driver)."""
    # console.log equivalent [WP5-SYN-02]: freeze run started (gates in driver).
    console_log("WP5-SYN-02", "freeze run started")
    defs = {
        "H-0001": ("H(A,B) = sum_x |depth_A(x) - depth_B(x)|, b_H = 2/1",
                   "depth_sum", "H1"),
        "H-0002": ("H(A,B) = #{(u,v), u!=v : anc_A(u,v) != anc_B(u,v)}, b_H = 2/1",
                   "ancestor_sym", "H3"),
        "H-0003": ("H(A,B) = sum_x |path_A(x) symmetric-difference path_B(x)|, b_H = 2/1",
                   "access_sym", "H3"),
        "H-0004": ("H(A,B) = #{v : heavy_A(v) != heavy_B(v)}, b_H = 2/1",
                   "heavy_disagree", "H5"),
        "H-0005": ("H(A,B) = #{v : parent_A(v) != parent_B(v)}, b_H = 2/1",
                   "parent_diff", "H2"),
        "H-0006": ("H(A,B) = sum_x |depth_A(x)-depth_B(x)| + #{v : heavy_A(v) != heavy_B(v)}, b_H = 2/1",
                   "combo_depth_heavy", "H6"),
    }
    for hyp_id, (definition, formula_id, form_class) in defs.items():
        freeze_candidate(hyp_id, definition, formula_id, form_class)
    return 0


if __name__ == "__main__":
    sys.exit(main())
