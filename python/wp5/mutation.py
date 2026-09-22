"""Mutation controls (WP-5 falsifier feature): sign-perturbation detection.

For each frozen candidate, sign-flip mutants of the formula definition are
evaluated on small sizes (n<=4 exhaustive R_n) under fresh mutation IDs
(MUT-<hypothesis_id>-<k>). A mutant that still passes would expose an
insensitive gate; a mutant that fails with a preserved exact counterexample
proves the gate bites. Mutants never overwrite the parent hypothesis
(T18/STOP-16). Exact integer arithmetic throughout.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-MUT-01]: mutation module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def sign_flip_global(formula_fn):
    """Global sign flip: valid for every formula (exact, state-only)."""
    def mutant(info_a, info_b, n):
        return -formula_fn(info_a, info_b, n)
    return mutant


def run_mutation_suite(hypothesis_id, formula_fn, p_h, q_h, out_dir):
    """Evaluate global sign-flip mutant on n=2..4 exhaustive R_n."""
    # console.log equivalent [WP5-MUT-02]: mutation suite executed.
    console_log("WP5-MUT-02", "mutation suite %s" % hypothesis_id)
    sys.path.insert(0, REPO)
    from python.wp5 import falsify as F
    mutant = sign_flip_global(formula_fn)
    results = {"parent": hypothesis_id, "mutants": []}
    for n in (2, 3, 4):
        shapes, count, after, cost, pair_ids = F.load_domain_tables(n)
        sys.path.insert(0, REPO)
        from python.reference import tree as T
        tree_info = [None] * count
        for tree_id, shape in enumerate(shapes):
            tree_info[tree_id] = F.S.tree_info(
                T.assign_inorder_keys(T.parse_shape(shape)))
        table = {pid: mutant(tree_info[pid // count], tree_info[pid % count], n)
                 for pid in pair_ids}
        worst = None
        worst_at = None
        for pid in pair_ids:
            h_state = table[pid]
            a_id = pid // count
            b_id = pid % count
            for key in range(1, n + 1):
                a2 = after[key][a_id]
                ca = cost[key][a_id]
                b2 = after[key][b_id]
                cb = cost[key][b_id]
                residual = q_h * cb + q_h * (table[a2 * count + b2] - h_state) - p_h * ca
                if worst is None or residual > worst:
                    worst = residual
                    worst_at = [pid, 0, key]
        results["mutants"].append(
            {"mutation_id": "MUT-%s-global-sign-flip" % hypothesis_id, "n": n,
             "keep_worst": str(worst), "keep_worst_at": worst_at,
             "caught": worst is not None and worst > 0})
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "mutations_%s.json" % hypothesis_id),
              "w", encoding="utf-8") as handle:
        json.dump(results, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP5-MUT-03]: mutation verdicts recorded.
    console_log("WP5-MUT-03", "mutants recorded %s" % hypothesis_id)
    return results
