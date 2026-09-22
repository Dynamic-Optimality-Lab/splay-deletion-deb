"""WP-5 stage 14: adversarial falsification, UH-8 verdicts, holdout consumption.

Adversarial campaigns run for every frozen candidate (supplementary where the
candidate is already REJECTED; decisive UH-8 only for UH-0..UH-7 survivors).
If survivors exist: freeze the complete final set (multiplicity), unlock n8,
run EV-8 + independent twin, unlock H1, run H1 fresh evaluation + twin,
compose UH-6, and record. If none exist: both holdouts stay pristine and the
stage records NO-SUBJECTS honestly.
"""
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-ADV-20]: adversarial stage started.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


BUDGETS = {"uniform": 60, "random": 60, "hill_starts": 8, "hill_steps": 12,
           "anneal_rounds": 120, "gen_pop": 12, "gen_gens": 6,
           "motif_sizes": (16, 24), "genome_len": 10}


def run_campaigns(hypothesis_id):
    """All adversary engines against one frozen candidate (exact residuals)."""
    # console.log equivalent [WP5-ADV-21]: campaign executed.
    console_log("WP5-ADV-21", "adversarial campaign %s" % hypothesis_id)
    sys.path.insert(0, REPO)
    from python.reference import tree as T
    from python.reference import splay as SP
    from python.reference import enumerate as E
    from python.wp5 import structural as S
    from python.adversary import motif_generator as M
    from python.adversary import residual_search as R
    from python.adversary import hill_climb as H
    from python.adversary import genetic_search as G
    from python.adversary import witness_generalizer as W
    formula_fn, _cls, _text = S.H_REGISTRY[hypothesis_id]
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.eval_contract.json" % hypothesis_id),
              encoding="utf-8") as handle:
        contract = json.load(handle)
    p_h = int(contract["b_hypothesis"]["p"])
    q_h = int(contract["b_hypothesis"]["q"])
    parse_fn, label_fn, splay_fn = T.parse_shape, T.assign_inorder_keys, SP.splay
    h_fn = (lambda info_a, info_b, n: formula_fn(info_a, info_b, n))
    rng = random.Random(20260922)
    runs = []
    counters = []

    def attempt(state_a, state_b, n, engine):
        got = R.exact_residuals(state_a, state_b, n, h_fn, p_h, q_h, splay_fn)
        best = max(int(got["keep_max"]), int(got["delete_max"]))
        runs.append({"engine": engine, "n": n, "best": str(best)})
        if best > 0:
            which = got["keep_cex"] + got["delete_cex"]
            counters.append({"engine": engine, "n": n,
                             "counterexample": which[0] if which else None})

    for n in BUDGETS["motif_sizes"]:
        for state in R.uniform_engine(rng, BUDGETS["uniform"], n, parse_fn, label_fn):
            attempt(state[0], state[1], n, "uniform")
    for state in R.random_engine(rng, BUDGETS["random"], BUDGETS["motif_sizes"],
                                 parse_fn, label_fn):
        attempt(state[0], state[1], state[2], "random")
    for n in BUDGETS["motif_sizes"]:
        starts = R.uniform_engine(rng, BUDGETS["hill_starts"], n, parse_fn, label_fn)
        out = H.hill_climb(rng, starts, BUDGETS["hill_steps"], n, h_fn, p_h, q_h, splay_fn)
        runs.append({"engine": "hill-climb", "n": n, "best": str(out["best"])})
        start = M.history_realizable(rng, n, 2 * n, 0.5, parse_fn, label_fn, splay_fn)
        out = H.anneal(rng, start, BUDGETS["anneal_rounds"], n, h_fn, p_h, q_h, splay_fn)
        runs.append({"engine": "annealing", "n": n, "best": str(out["best"])})
        pop = [tuple((rng.randrange(2), rng.randint(1, n)) for _ in range(BUDGETS["genome_len"]))
               for _ in range(BUDGETS["gen_pop"])]
        out = G.genetic_search(rng, pop, BUDGETS["gen_gens"], n, h_fn, p_h, q_h,
                               splay_fn, parse_fn, label_fn)
        runs.append({"engine": "genetic", "n": n, "best": str(out["best"])})
        for row in G.motif_inflation([[1, 2], [1, 3], [2, 1]], (n,), h_fn, p_h, q_h,
                                     splay_fn, parse_fn, label_fn, rng):
            runs.append({"engine": "motif-inflation", "n": row["n"],
                         "best": str(max(int(row["keep_max"]), int(row["delete_max"])))})
    # Spines / opposite spines / mirrors / root splits / interval extremes.
    for n in BUDGETS["motif_sizes"]:
        specials = [M.spine_pair(n, True, parse_fn, label_fn),
                    M.spine_pair(n, False, parse_fn, label_fn),
                    M.root_split_pair(n, True, parse_fn, label_fn),
                    M.root_split_pair(n, False, parse_fn, label_fn),
                    M.interval_extreme_pair(n, parse_fn, label_fn)]
        for state_a, state_b, size in specials:
            attempt(state_a, state_b, size, "structured")
            mirror = (M.mirror_keyed(state_a, size), M.mirror_keyed(state_b, size), size)
            attempt(mirror[0], mirror[1], size, "mirror")
    out = {"hypothesis_id": hypothesis_id,
           "engines": sorted(set(r["engine"] for r in runs)),
           "runs": runs, "counterexamples": counters,
           "near_tight_families": []}
    # console.log equivalent [WP5-ADV-22]: campaign sealed (no proof claimed).
    console_log("WP5-ADV-22", "campaign %s CEs=%d" % (hypothesis_id, len(counters)))
    return out


def generalize_sharpest(hypothesis_ids, adv_dir):
    """Motif generalization of each candidate's sharpest development KEEP
    counterexample (samples only; WP-6 P17 decides proof)."""
    # console.log equivalent [WP5-ADV-28]: sharpest counterexamples generalized.
    console_log("WP5-ADV-28", "generalizing sharpest counterexamples")
    sys.path.insert(0, REPO)
    from python.reference import tree as T
    from python.reference import splay as SP
    from python.reference import enumerate as E
    from python.wp5 import structural as S
    from python.adversary import witness_generalizer as W
    families = []
    for hyp_id in hypothesis_ids:
        with open(os.path.join(REPO, "artifacts", "falsification", hyp_id,
                               "dev_summary.json"), encoding="utf-8") as handle:
            dev = json.load(handle)
        best = None
        for n_str, rep in dev["sizes"].items():
            if best is None or int(rep["keep_max"]) > int(best[1]["keep_max"]):
                best = (int(n_str), rep)
        n, rep = best
        pid, mode, key = rep["keep_argmax"]
        shapes = E.canonical_shapes(n)
        count = len(shapes)
        keyed_a = T.assign_inorder_keys(T.parse_shape(shapes[pid // count]))
        keyed_b = T.assign_inorder_keys(T.parse_shape(shapes[pid % count]))
        formula_fn, _cls, _text = S.H_REGISTRY[hyp_id]
        fam = W.generalize_counterexample(
            keyed_a, keyed_b, n, key, mode, T.parse_shape, T.assign_inorder_keys,
            T.serialize_shape, SP.splay,
            lambda ia, ib, nn: formula_fn(ia, ib, nn), 2, 1, (0, 1, 2))
        fam["hypothesis_id"] = hyp_id
        fam["source"] = {"n": n, "pid": pid, "mode": mode, "key": key,
                         "keep_max": rep["keep_max"]}
        with open(os.path.join(adv_dir, "family_%s.json" % hyp_id),
                  "w", encoding="utf-8") as handle:
            json.dump(fam, handle, sort_keys=True, indent=2)
            handle.write("\n")
        families.append(fam)
    with open(os.path.join(adv_dir, "near_tight_families.json"), "w", encoding="utf-8") as handle:
        json.dump(families, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP5-ADV-29]: families sealed (samples only).
    console_log("WP5-ADV-29", "families=%d" % len(families))


def stage14(sizes=(2, 3, 4, 5, 6, 7)):
    """UH-8 verdicts; holdout consumption only with survivors."""
    from python.wp5.run_phase import CANDIDATES, read_uh, write_uh, set_ledger_status
    from python.wp5 import holdout as HLD
    adv_dir = os.path.join(REPO, "artifacts", "falsification", "adversarial")
    os.makedirs(adv_dir, exist_ok=True)
    all_runs, all_cex, all_fam = [], [], []
    for hyp_id in CANDIDATES:
        out = run_campaigns(hyp_id)
        all_runs.extend([{**r, "hypothesis_id": hyp_id} for r in out["runs"]])
        all_cex.extend([{**c, "hypothesis_id": hyp_id} for c in out["counterexamples"]])
        gates = read_uh(hyp_id)
        subject = all(gates[k] == "PASS" for k in
                      ("UH-0", "UH-1", "UH-2", "UH-3", "UH-4", "UH-5", "UH-7"))
        if not subject:
            gates["UH-8"] = "NOT_APPLICABLE (already REJECTED; adversarial runs supplementary)"
        elif any(c["hypothesis_id"] == hyp_id for c in all_cex):
            gates["UH-8"] = "REJECTED"
        else:
            gates["UH-8"] = "PASS"
        write_uh(hyp_id, gates)
        if gates["UH-8"] == "REJECTED" and "(already REJECTED" not in gates.get("UH-8", ""):
            set_ledger_status(hyp_id, "REJECTED at UH-8 (adversarial counterexample)")
        # console.log equivalent [WP5-ADV-23]: UH-8 verdict recorded.
        console_log("WP5-ADV-23", "UH-8 %s %s" % (hyp_id, gates["UH-8"]))
    with open(os.path.join(adv_dir, "runs.json"), "w", encoding="utf-8") as handle:
        json.dump(all_runs, handle, sort_keys=True, indent=2)
        handle.write("\n")
    with open(os.path.join(adv_dir, "counterexamples.json"), "w", encoding="utf-8") as handle:
        json.dump(all_cex, handle, sort_keys=True, indent=2)
        handle.write("\n")
    with open(os.path.join(adv_dir, "near_tight_families.json"), "w", encoding="utf-8") as handle:
        json.dump(all_fam, handle, sort_keys=True, indent=2)
        handle.write("\n")
    generalize_sharpest(CANDIDATES, adv_dir)
    survivors = [h for h in CANDIDATES
                 if all(read_uh(h)[k] == "PASS" for k in
                        ("UH-0", "UH-1", "UH-2", "UH-3", "UH-4", "UH-5", "UH-7", "UH-8"))]
    # console.log equivalent [WP5-ADV-24]: survivor set recorded.
    console_log("WP5-ADV-24", "UH-8 survivors=%s" % (survivors,))
    if not survivors:
        # console.log equivalent [WP5-ADV-25]: no-subject branch recorded.
        console_log("WP5-ADV-25", "NO-SUBJECTS: holdouts stay pristine (no consumption)")
        with open(os.path.join(adv_dir, "holdout_decision.json"), "w", encoding="utf-8") as handle:
            json.dump({"survivors": [], "n8_consumed": False, "h1_consumed": False,
                       "reason": "no UH-8 survivor; EV-8/H1 unconsumed by design"}, handle,
                      sort_keys=True, indent=2)
            handle.write("\n")
        return survivors
    set_hash = HLD.freeze_final_set(survivors)
    HLD.unlock_n8(survivors[0])
    ev8_passers = []
    for hyp_id in survivors:
        ev8 = HLD.run_ev8(hyp_id)
        if ev8["verdict"] == "REJECTED":
            gates = read_uh(hyp_id)
            gates["UH-6"] = "REJECTED"
            write_uh(hyp_id, gates)
            set_ledger_status(hyp_id, "REJECTED at EV-8 (n8 exact counterexample)")
        else:
            ev8_passers.append(hyp_id)
    if not ev8_passers:
        # console.log equivalent [WP5-ADV-26]: EV-8 sweep recorded.
        console_log("WP5-ADV-26", "no EV-8 passer; H1 stays pristine")
        with open(os.path.join(adv_dir, "holdout_decision.json"), "w", encoding="utf-8") as handle:
            json.dump({"survivors": survivors, "ev8_passers": [],
                       "n8_consumed": True, "h1_consumed": False,
                       "reason": "all survivors failed EV-8; H1 unconsumed by design"},
                      handle, sort_keys=True, indent=2)
            handle.write("\n")
        return survivors
    HLD.unlock_h1(set_hash)
    for hyp_id in ev8_passers:
        h1rep = HLD.run_h1(hyp_id, set_hash)
        gates = read_uh(hyp_id)
        gates["UH-6"] = "REJECTED" if h1rep["verdict"] == "REJECTED" else "UH-6_PASS_FRESH_H1"
        write_uh(hyp_id, gates)
        set_ledger_status(hyp_id, "UH-6 %s (EV-8 + H1 + twins)" % gates["UH-6"])
    with open(os.path.join(adv_dir, "holdout_decision.json"), "w", encoding="utf-8") as handle:
        json.dump({"survivors": survivors, "ev8_passers": ev8_passers,
                   "n8_consumed": True, "h1_consumed": True}, handle,
                  sort_keys=True, indent=2)
        handle.write("\n")
    return survivors
