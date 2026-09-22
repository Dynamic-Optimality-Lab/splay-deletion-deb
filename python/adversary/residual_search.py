"""Exact residual evaluator + uniform/random proposal engines (WP-5 adversary side).

Heuristics propose; the exact evaluator disposes. Every residual is an exact
integer (scale q_H); no float ever decides a sign. Deterministic: all
randomness flows from explicit integer seeds.
"""
import sys
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from python.wp5 import structural as S

# console.log equivalent [WP5-ADV-03]: residual-search module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def exact_residuals(keyed_a, keyed_b, n, h_fn, p_h, q_h, splay_fn):
    """Exact (E_K, E_D) per (mode, key) as integers scaled by q_H.

    Returns dict with keep/delete maxima, first maximizers in K(1..n)/D(1..n)
    order, positive counts, and lex-first preserved counterexamples.
    """
    info_a = S.tree_info(keyed_a)
    info_b = S.tree_info(keyed_b)
    h_state = h_fn(info_a, info_b, n)
    keep_max = None
    keep_arg = None
    keep_pos = 0
    keep_cex = []
    delete_max = None
    delete_arg = None
    delete_pos = 0
    delete_cex = []
    for key in range(1, n + 1):
        a2 = splay_fn(keyed_a, key)[0]
        info_a2 = S.tree_info(a2)
        ca = len(info_a["path"][key])
        b2 = splay_fn(keyed_b, key)[0]
        info_b2 = S.tree_info(b2)
        cb = len(info_b["path"][key])
        residual = (q_h * cb + q_h * (h_fn(info_a2, info_b2, n) - h_state)
                    - p_h * ca)
        if keep_max is None or residual > keep_max:
            keep_max = residual
            keep_arg = [0, key]
        if residual > 0:
            keep_pos += 1
            if len(keep_cex) < 16:
                keep_cex.append([0, key, str(residual)])
        residual = q_h * (h_fn(info_a2, info_b, n) - h_state) - p_h * ca
        if delete_max is None or residual > delete_max:
            delete_max = residual
            delete_arg = [1, key]
        if residual > 0:
            delete_pos += 1
            if len(delete_cex) < 16:
                delete_cex.append([1, key, str(residual)])
    return {"keep_max": str(keep_max), "keep_argmax": keep_arg,
            "keep_pos_count": keep_pos, "keep_cex": keep_cex,
            "delete_max": str(delete_max), "delete_argmax": delete_arg,
            "delete_pos_count": delete_pos, "delete_cex": delete_cex}


def uniform_engine(rng, count, n, parse_fn, label_fn, init="random"):
    """Uniform proposal engine: random states from one init family."""
    # console.log equivalent [WP5-ADV-04]: uniform proposals generated.
    console_log("WP5-ADV-04", "uniform proposals n=%d count=%d" % (n, count))
    from python.adversary import motif_generator as M
    out = []
    for _ in range(count):
        out.append(M.history_realizable(rng, n, 2 * n, 0.5, parse_fn, label_fn,
                                        _splay_of(), init=init))
    return out


def _splay_of():
    from python.reference import splay as _splay
    return _splay.splay


def random_engine(rng, count, sizes, parse_fn, label_fn):
    """Random proposal engine across sizes and init families."""
    # console.log equivalent [WP5-ADV-05]: random proposals generated.
    console_log("WP5-ADV-05", "random proposals sizes=%s" % (sizes,))
    from python.adversary import motif_generator as M
    families = ("random", "spine", "balanced", "comb", "zigzag")
    out = []
    for index in range(count):
        n = sizes[index % len(sizes)]
        out.append(M.history_realizable(
            rng, n, 2 * n, rng.choice((0.2, 0.5, 0.8)), parse_fn, label_fn,
            _splay_of(), init=families[index % len(families)]))
    return out
