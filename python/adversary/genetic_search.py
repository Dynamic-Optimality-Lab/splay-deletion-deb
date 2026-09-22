"""Genetic + motif-inflation drivers (WP-5 adversary side).

Tiny deterministic populations over keyed-pair genomes (action-history
genes); fitness is the exact integer residual maximum. SMT/MIP backends are
supported structurally: the driver accepts any exact proposer honoring the
(fitness_fn, seed) interface, but only the implemented exact engines run in
this phase (no external solvers invoked; recorded as such).
"""
import sys
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-ADV-09]: genetic module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def genetic_search(rng, population, generations, n, h_fn, p_h, q_h, splay_fn,
                   parse_fn, label_fn):
    """Genetic driver: action-history genomes, exact-residual fitness."""
    # console.log equivalent [WP5-ADV-10]: genetic search executed.
    console_log("WP5-ADV-10", "genetic n=%d pop=%d gens=%d" % (n, len(population), generations))
    from python.adversary import residual_search as R
    from python.adversary import motif_generator as M
    start = M.random_insertion_keyed(rng, n, parse_fn, label_fn)
    pop = list(population)
    best = None
    for _ in range(generations):
        scored = []
        for genome in pop:
            a_tree, b_tree = M.replay_actions(start, genome, splay_fn)
            got = R.exact_residuals(a_tree, b_tree, n, h_fn, p_h, q_h, splay_fn)
            score = max(int(got["keep_max"]), int(got["delete_max"]))
            scored.append((score, genome, a_tree, b_tree))
        scored.sort(key=lambda entry: entry[0], reverse=True)
        if best is None or scored[0][0] > best[0]:
            best = (scored[0][0], scored[0][2], scored[0][3])
        survivors = [entry[1] for entry in scored[: max(1, len(scored) // 2)]]
        children = []
        while len(survivors) + len(children) < len(pop):
            mom = survivors[rng.randrange(len(survivors))]
            dad = survivors[rng.randrange(len(survivors))]
            cut = rng.randrange(min(len(mom), len(dad)) + 1)
            child = mom[:cut] + dad[cut:]
            if child and rng.random() < 0.3:
                child = list(child)
                pos = rng.randrange(len(child))
                child[pos] = (1 - child[pos][0], rng.randint(1, n))
            children.append(tuple(child))
        pop = survivors + children
    return {"best": best[0] if best else None, "n": n}


def motif_inflation(motif_keys_list, sizes, h_fn, p_h, q_h, splay_fn, parse_fn,
                    label_fn, rng):
    """Motif-inflation driver: WP-4 canonical key patterns replayed large."""
    # console.log equivalent [WP5-ADV-11]: motif inflation executed.
    console_log("WP5-ADV-11", "motif inflation sizes=%s" % (sizes,))
    from python.adversary import residual_search as R
    from python.adversary import motif_generator as M
    out = []
    for n in sizes:
        for pattern in motif_keys_list:
            a_tree, b_tree, _n = M.inflated_motif_pair(
                n, pattern, parse_fn, label_fn, splay_fn, rng)
            got = R.exact_residuals(a_tree, b_tree, n, h_fn, p_h, q_h, splay_fn)
            out.append({"n": n, "pattern": list(pattern),
                        "keep_max": got["keep_max"], "delete_max": got["delete_max"]})
    return out
