"""Post-freeze holdout orchestration (WP-5 evaluation side ONLY).

Runs exclusively AFTER the final candidate set is frozen: n8 unlock, EV-8
(contaminated exhaustive validation) with independent twin, H1 unlock, H1
fresh evaluation with independent twin, UH-6 composition, and sealed
per-candidate reports. All bank/n8 imports are deferred inside post-unlock
functions (module import never touches quarantined namespaces); every entry
point re-checks firewall states fail-closed first.

No synthesis here: H formulas arrive frozen via hypothesis IDs.
"""
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-HLD-01]: holdout module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def _sha256_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def frozen_set_hash():
    """Current frozen-set hash from the production n8 candidate-set file."""
    from python.n8_holdout import n8_firewall as N8FW
    st = N8FW.read_state()
    return st.get("set_sha256")


def freeze_final_set(hypothesis_ids):
    """Freeze the COMPLETE survivor set (refuses empty; SA-03/SA-04 multiplicity)."""
    # console.log equivalent [WP5-HLD-02]: final set frozen.
    console_log("WP5-HLD-02", "freezing final set %s" % (hypothesis_ids,))
    if not hypothesis_ids:
        raise AssertionError("cannot freeze an empty final candidate set")
    from python.n8_holdout import n8_firewall as N8FW
    with open(os.path.join(REPO, "artifacts", "hypotheses", "hypothesis_ledger.json"),
              encoding="utf-8") as handle:
        ledger = json.load(handle)
    by_id = {h["hypothesis_id"]: h for h in ledger["hypotheses"]}
    entries = []
    for hyp_id in sorted(hypothesis_ids):
        if hyp_id not in by_id:
            raise AssertionError("unknown hypothesis_id in ledger: %s" % hyp_id)
        with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.json" % hyp_id),
                  encoding="utf-8") as handle:
            doc = json.load(handle)
        blob = (json.dumps(doc, sort_keys=True) + "\n").encode("utf-8")
        entries.append({"hypothesis_id": hyp_id, "sha256": _sha256_bytes(blob)})
    set_hash = N8FW.freeze_candidate_set(entries)
    # console.log equivalent [WP5-HLD-03]: set hash recorded.
    console_log("WP5-HLD-03", "set hash %s" % set_hash[:16])
    return set_hash


def unlock_n8(candidate_id):
    """Unlock n8 exactly once for one frozen-set member."""
    # console.log equivalent [WP5-HLD-04]: n8 unlock requested.
    console_log("WP5-HLD-04", "unlock n8 for %s" % candidate_id)
    from python.n8_holdout import n8_firewall as N8FW
    return N8FW.unlock(candidate_id)


def run_ev8(hypothesis_id):
    """EV-8: full exact n8 sweep + independent twin (requires UNLOCKED)."""
    # console.log equivalent [WP5-HLD-05]: EV-8 executed.
    console_log("WP5-HLD-05", "EV-8 %s" % hypothesis_id)
    from python.n8_holdout import n8_firewall as N8FW
    from python.n8_holdout import sweep as SW
    from python.n8_holdout import independent as IND
    from python.wp5 import structural as S
    N8FW.guard_n8_read("artifacts/transitions/n8/forward.bin.zst")
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.eval_contract.json" % hypothesis_id),
              encoding="utf-8") as handle:
        contract = json.load(handle)
    p_h = int(contract["b_hypothesis"]["p"])
    q_h = int(contract["b_hypothesis"]["q"])
    formula_fn, _cls, _text = S.H_REGISTRY[hypothesis_id]
    n, count, pair_ids, after, cost = SW.load_domain(
        os.path.join(REPO, "artifacts", "transitions", "n8"),
        os.path.join(REPO, "artifacts", "reachability", "n8"))
    import zstandard as zstd
    sys.path.insert(0, REPO)
    from python.reference import enumerate as E
    from python.reference import tree as T
    shapes = E.canonical_shapes(n)
    infos = [S.tree_info(T.assign_inorder_keys(T.parse_shape(s))) for s in shapes]
    h_table = {pid: formula_fn(infos[pid // count], infos[pid % count], n)
               for pid in pair_ids}
    primary = SW.sweep_pair_access(pair_ids, count, n, after, cost,
                                   h_table.__getitem__, 1, p_h, q_h)
    keyed, after_i, cost_i, pairs_i = IND.load_sealed_universe(n, REPO)
    formula_id = _formula_id_of(hypothesis_id)
    indep_max = _independent_n8_maxima(formula_id, n, REPO, p_h, q_h)
    agree = (primary["keep_max"] == indep_max["keep_max"]
             and primary["delete_max"] == indep_max["delete_max"]
             and primary["keep_argmax"] == indep_max["keep_argmax"]
             and primary["delete_argmax"] == indep_max["delete_argmax"])
    verdict = ("REJECTED" if int(primary["keep_max"]) > 0 or int(primary["delete_max"]) > 0
               or primary["norm_count"] > 0 or primary["nonneg_count"] > 0
               else "UH-6_PASS_FINITE_N8")
    report = {"candidate_id": hypothesis_id, "n": 8, "edge_count": primary["edge_count"],
              "norm_count": primary["norm_count"], "norm_bad": primary["norm_bad"],
              "nonneg_count": primary["nonneg_count"], "nonneg_bad": primary["nonneg_bad"],
              "keep_max_scaled": primary["keep_max"], "keep_argmax": primary["keep_argmax"],
              "keep_pos_count": primary["keep_pos_count"],
              "keep_preserved_counterexamples": primary["keep_cex"],
              "delete_max_scaled": primary["delete_max"], "delete_argmax": primary["delete_argmax"],
              "delete_pos_count": primary["delete_pos_count"],
              "delete_preserved_counterexamples": primary["delete_cex"],
              "independent_agreement": agree, "independent_maxima_match": agree,
              "unlock_record": "n8_firewall UNLOCKED_ONCE", "verdict": verdict,
              "label": "EV-8 N8_CONTAMINATED_EXHAUSTIVE_VALIDATION (never fresh holdout)"}
    outdir = os.path.join(REPO, "artifacts", "wp5", "sa03", "holdout", hypothesis_id)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "n8_ev8.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP5-HLD-06]: EV-8 sealed.
    console_log("WP5-HLD-06", "EV-8 %s verdict=%s" % (hypothesis_id, verdict))
    return report


def _formula_id_of(hypothesis_id):
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.json" % hypothesis_id),
              encoding="utf-8") as handle:
        return json.load(handle)["formula_id"]


def _independent_n8_maxima(formula_id, n, repo_root, p_h, q_h):
    from python.n8_holdout import independent as IND
    keyed, _after, _cost, _pairs = IND.load_sealed_universe(n, repo_root)
    return IND.sweep_candidate(formula_id, n, repo_root, p_h, q_h, keyed=keyed)


def unlock_h1(expected_set_hash):
    """Unlock the H1 bank once against the frozen set hash (multiplicity)."""
    # console.log equivalent [WP5-HLD-07]: H1 unlock requested.
    console_log("WP5-HLD-07", "unlock H1")
    from python.holdout_bank import h1_firewall as H1FW
    st = H1FW.read_state()
    if st.get("state") != H1FW.EMPTY:
        raise AssertionError("H1 already unlocked (state=%s)" % st.get("state"))
    if frozen_set_hash() != expected_set_hash:
        raise AssertionError("frozen set hash mismatch at H1 unlock")
    doc = {"state": H1FW.UNLOCKED, "candidate_set_hash": expected_set_hash,
           "unlock": {"unlock_count": 1},
           "note": "H1 revealed once for the frozen set; descendants take new IDs"}
    blob = (json.dumps(doc, sort_keys=True) + "\n").encode("utf-8")
    with open(H1FW.STATE_FILE, "wb") as handle:
        handle.write(blob)
    # console.log equivalent [WP5-HLD-08]: H1 unlock recorded.
    console_log("WP5-HLD-08", "H1 UNLOCKED_ONCE")
    return True


def run_h1(hypothesis_id, expected_set_hash):
    """H1 fresh evaluation + independent twin (requires H1 UNLOCKED)."""
    # console.log equivalent [WP5-HLD-09]: H1 evaluation executed.
    console_log("WP5-HLD-09", "H1 %s" % hypothesis_id)
    from python.holdout_bank import h1_firewall as H1FW
    from python.holdout_bank import evaluate as EV
    from python.holdout_bank import independent as IND
    from python.wp5 import structural as S
    st = H1FW.read_state()
    if st.get("state") != H1FW.UNLOCKED:
        raise AssertionError("H1 evaluation requires UNLOCKED firewall")
    if st.get("candidate_set_hash") != expected_set_hash:
        raise AssertionError("H1 set hash mismatch")
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.eval_contract.json" % hypothesis_id),
              encoding="utf-8") as handle:
        contract = json.load(handle)
    p_h = int(contract["b_hypothesis"]["p"])
    q_h = int(contract["b_hypothesis"]["q"])
    formula_fn, _cls, _text = S.H_REGISTRY[hypothesis_id]

    def h_fn(keyed_a, keyed_b, n):
        return formula_fn(S.tree_info(keyed_a), S.tree_info(keyed_b), n)

    primary = EV.evaluate_bank(os.path.join(REPO, "artifacts", "wp5", "h1_holdout"),
                               h_fn, 1, p_h, q_h)
    formula_id = _formula_id_of(hypothesis_id)
    sys.path.insert(0, REPO)
    from python.reference import enumerate as E
    indep = _independent_h1(formula_id, p_h, q_h)
    agree = (primary["keep_max"] == indep["keep_max"]
             and primary["delete_max"] == indep["delete_max"])
    verdict = ("REJECTED" if int(primary["keep_max"]) > 0 or int(primary["delete_max"]) > 0
               or primary["norm_count"] > 0 or primary["nonneg_count"] > 0
               else "UH-6_PASS_FRESH_H1")
    with open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout", "bank_manifest.json"),
              encoding="utf-8") as handle:
        commitment = json.load(handle)["bank_commitment_sha256"]
    report = {"candidate_id": hypothesis_id, "candidate_sha256": _file_sha(hypothesis_id),
              "n_sizes": [9, 10, 12, 16, 24, 32], "edge_count": primary["edge_count"],
              "per_size": primary["per_size"],
              "norm_count": primary["norm_count"], "norm_bad": primary["norm_bad"],
              "nonneg_count": primary["nonneg_count"], "nonneg_bad": primary["nonneg_bad"],
              "keep_max_scaled": primary["keep_max"], "keep_argmax": primary["keep_argmax"],
              "keep_pos_count": primary["keep_pos_count"],
              "keep_preserved_counterexamples": primary["keep_cex"],
              "delete_max_scaled": primary["delete_max"],
              "delete_argmax": primary["delete_argmax"],
              "delete_pos_count": primary["delete_pos_count"],
              "delete_preserved_counterexamples": primary["delete_cex"],
              "bank_commitment_sha256": commitment,
              "independent_agreement": agree, "independent_maxima_match": agree,
              "unlock_record": "H1 UNLOCKED_ONCE", "verdict": verdict}
    outdir = os.path.join(REPO, "artifacts", "wp5", "h1_holdout", hypothesis_id)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "h1_report.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP5-HLD-10]: H1 report sealed.
    console_log("WP5-HLD-10", "H1 %s verdict=%s" % (hypothesis_id, verdict))
    return report


def _file_sha(hypothesis_id):
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.json" % hypothesis_id),
              "rb") as handle:
        data = handle.read()
    return hashlib.sha256(data).hexdigest()


def _ind_h_of(formula_id):
    """H from frozen math text on the independent twin's keyed trees."""
    from python.holdout_bank import independent as IND

    def path_set(keyed, x):
        return set(IND.find_path(keyed, x))

    def h_of(keyed_a, keyed_b, n):
        keys = list(range(1, n + 1))
        if formula_id == "depth_sum":
            return sum(abs(len(IND.find_path(keyed_a, k)) - len(IND.find_path(keyed_b, k)))
                       for k in keys)
        if formula_id == "ancestor_sym":
            total = 0
            paths_a = {v: path_set(keyed_a, v) for v in keys}
            paths_b = {v: path_set(keyed_b, v) for v in keys}
            for u in keys:
                for v in keys:
                    if u != v and ((u in paths_a[v]) != (u in paths_b[v])):
                        total += 1
            return total
        if formula_id == "access_sym":
            total = 0
            for k in keys:
                total += len(path_set(keyed_a, k).symmetric_difference(path_set(keyed_b, k)))
            return total
        raise ValueError("unknown formula_id")
    return h_of


def _independent_h1(formula_id, p_h, q_h):
    import zstandard as zstd
    from python.holdout_bank import independent as IND
    h_of = _ind_h_of(formula_id)
    keep_max = None
    keep_arg = None
    delete_max = None
    delete_arg = None
    for n in (9, 10, 12, 16, 24, 32):
        with open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout", "n%d" % n,
                               "bank.json.zst"), "rb") as handle:
            recs = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))["states"]
        states = [(r["end_A_shape"], r["end_B_shape"]) for r in recs]
        out = IND.evaluate_states_ind(states, n, h_of, 1, p_h, q_h)
        if keep_max is None or int(out["keep_max"]) > int(keep_max):
            keep_max, keep_arg = out["keep_max"], out["keep_argmax"]
        if delete_max is None or int(out["delete_max"]) > int(delete_max):
            delete_max, delete_arg = out["delete_max"], out["delete_argmax"]
    return {"keep_max": keep_max, "keep_argmax": keep_arg,
            "delete_max": delete_max, "delete_argmax": delete_arg}
