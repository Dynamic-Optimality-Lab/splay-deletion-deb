"""Rotation hill-climb + annealing proposal engines (WP-5 adversary side).

Both engines walk keyed-pair space proposing single-key accesses; the exact
residual evaluator (residual_search) disposes. Deterministic via seeds.
"""
import sys
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-ADV-06]: hill-climb module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def hill_climb(rng, starts, steps_per_start, n, h_fn, p_h, q_h, splay_fn):
    """Rotation hill-climb: greedy single-access residual ascent on exact ints."""
    # console.log equivalent [WP5-ADV-07]: hill-climb executed.
    console_log("WP5-ADV-07", "hill-climb n=%d starts=%d" % (n, len(starts)))
    from python.adversary import residual_search as R
    best = None
    for start_a, start_b, _n in starts:
        cur_a, cur_b = start_a, start_b
        cur = R.exact_residuals(cur_a, cur_b, n, h_fn, p_h, q_h, splay_fn)
        cur_best = max(int(cur["keep_max"]), int(cur["delete_max"]))
        for step_no in range(steps_per_start):
            key = rng.randint(1, n)
            if step_no % 2 == 0:
                cand_a = splay_fn(cur_a, key)[0]
                cand_b = cur_b
            else:
                cand_a = cur_a
                cand_b = splay_fn(cur_b, key)[0]
            got = R.exact_residuals(cand_a, cand_b, n, h_fn, p_h, q_h, splay_fn)
            score = max(int(got["keep_max"]), int(got["delete_max"]))
            if score > cur_best:
                cur_best = score
                cur_a, cur_b = cand_a, cand_b
        if best is None or cur_best > best[0]:
            best = (cur_best, cur_a, cur_b)
    return {"best": best[0] if best else None, "n": n}


def anneal(rng, start, rounds, n, h_fn, p_h, q_h, splay_fn):
    """Deterministic annealing proposer: exact-residual ascent with cooling
    acceptance over integer scores (no floats)."""
    # console.log equivalent [WP5-ADV-08]: annealing executed.
    console_log("WP5-ADV-08", "annealing n=%d rounds=%d" % (n, rounds))
    from python.adversary import residual_search as R
    cur_a, cur_b, _n = start
    cur = R.exact_residuals(cur_a, cur_b, n, h_fn, p_h, q_h, splay_fn)
    cur_best = max(int(cur["keep_max"]), int(cur["delete_max"]))
    for round_no in range(rounds):
        temperature = (rounds - round_no) // 16 + 1
        key = rng.randint(1, n)
        if rng.random() < 0.5:
            cand_a = splay_fn(cur_a, key)[0]
            cand_b = cur_b
        else:
            cand_a = cur_a
            cand_b = splay_fn(cur_b, key)[0]
        got = R.exact_residuals(cand_a, cand_b, n, h_fn, p_h, q_h, splay_fn)
        score = max(int(got["keep_max"]), int(got["delete_max"]))
        if score >= cur_best - temperature and rng.random() < 0.75:
            cur_best = score
            cur_a, cur_b = cand_a, cand_b
    return {"best": cur_best, "n": n}
