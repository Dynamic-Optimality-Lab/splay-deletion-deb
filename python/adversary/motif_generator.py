"""Adversarial tree/pair generators (WP-5 falsification only; exact inputs).

Every generator yields keyed pair states (A, B, n) built ONLY from frozen
WP-1 tree primitives. No candidate information enters generation
(generation runs before/without residuals; exact evaluator disposes).
Deterministic: every stochastic choice flows from an explicit integer seed.
"""
import random
import sys
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-ADV-01]: generator module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def chain_skeleton(n, side):
    """Single-child chain skeleton leaning `side` ('L'/'R')."""
    skel = ()
    for _ in range(n):
        if side == "L":
            skel = ((skel, ()))
        else:
            skel = (((), skel))
    return skel


def _serialize(skel):
    if skel == ():
        return "."
    return "(" + _serialize(skel[0]) + _serialize(skel[1]) + ")"


def balanced_skeleton(count):
    """Median-root balanced skeleton over `count` nodes."""
    if count <= 0:
        return ()
    left_n = (count - 1) // 2
    return (balanced_skeleton(left_n), balanced_skeleton(count - 1 - left_n))


def comb_skeleton(n):
    """Left-toothed caterpillar skeleton over exactly n nodes."""
    if n <= 0:
        return ()
    if n == 1:
        return ((), ())
    if n == 2:
        return ((((), ()), ()))
    return ((((((), ()), comb_skeleton(n - 3)))), ())


def zigzag_skeleton(n):
    """Alternating single-child chain skeleton."""
    skel = ()
    side = "L"
    chain = []
    for _ in range(n):
        chain.append(side)
        side = "R" if side == "L" else "L"
    for side in reversed(chain):
        if side == "L":
            skel = ((skel, ()))
        else:
            skel = (((), skel))
    return skel


def random_insertion_keyed(rng, n, parse_fn, label_fn):
    """Random-Catalan keyed tree (random insertion order; documented approx)."""
    perm = list(range(n))
    rng.shuffle(perm)
    tree = ()
    for rank in perm:
        tree = _bst_insert(tree, rank)
    return label_fn(_erase(tree))


def _bst_insert(tree, key):
    if tree == ():
        return ((), key, ())
    left, k, right = tree
    if key < k:
        return (_bst_insert(left, key), k, right)
    return (left, k, _bst_insert(right, key))


def _erase(tree):
    if tree == ():
        return ()
    return (_erase(tree[0]), _erase(tree[2]))


def mirror_keyed(keyed, n):
    """Mirror image: swap children, relabel v -> n+1-v (both trees together)."""
    if keyed == ():
        return ()
    left, key, right = keyed
    return (mirror_keyed(right, n), n + 1 - key, mirror_keyed(left, n))


def spine_pair(n, same_side, parse_fn, label_fn):
    """Spine-vs-spine pair (same or opposite lean)."""
    left = label_fn(parse_fn(_serialize(chain_skeleton(n, "L"))))
    if same_side:
        return left, label_fn(parse_fn(_serialize(chain_skeleton(n, "L")))), n
    return left, label_fn(parse_fn(_serialize(chain_skeleton(n, "R")))), n


def history_realizable(rng, n, steps, keep_bias, parse_fn, label_fn, splay_fn,
                       init="random"):
    """Legal KEEP/DELETE walk from a diagonal (history-realizable stream)."""
    if init == "random":
        start = random_insertion_keyed(rng, n, parse_fn, label_fn)
    elif init == "spine":
        start = label_fn(parse_fn(_serialize(chain_skeleton(n, "L"))))
    elif init == "balanced":
        start = label_fn(parse_fn(_serialize(balanced_skeleton(n))))
    elif init == "comb":
        start = label_fn(parse_fn(_serialize(comb_skeleton(n))))
    elif init == "zigzag":
        start = label_fn(parse_fn(_serialize(zigzag_skeleton(n))))
    else:
        raise ValueError("unknown init family")
    first_key = rng.randint(1, n)
    # console.log equivalent [WP5-ADV-02]: history stream generated.
    a_tree, b_tree = start, start
    a_tree = splay_fn(a_tree, first_key)[0]
    b_tree = splay_fn(b_tree, first_key)[0]
    for _ in range(steps):
        key = rng.randint(1, n)
        if rng.random() < keep_bias:
            a_tree = splay_fn(a_tree, key)[0]
            b_tree = splay_fn(b_tree, key)[0]
        else:
            a_tree = splay_fn(a_tree, key)[0]
    return a_tree, b_tree, n


def replay_actions(start, actions, splay_fn):
    """Replay an action genome [(mode, key)] from a diagonal start.

    mode 0 = KEEP (both trees splay), mode 1 = DELETE (A tree only).
    Returns (a_tree, b_tree). Genome form shared by genetic/annealing drivers.
    """
    a_tree, b_tree = start, start
    for mode, key in actions:
        if mode == 0:
            a_tree = splay_fn(a_tree, key)[0]
            b_tree = splay_fn(b_tree, key)[0]
        else:
            a_tree = splay_fn(a_tree, key)[0]
    return a_tree, b_tree


def root_split_pair(n, agree, parse_fn, label_fn):
    """Pair whose roots agree (same key) or disagree.

    Built directly from skeletons (never by enumerating Catalan shapes,
    which is infeasible for large n).
    """
    if agree:
        shape = _serialize(balanced_skeleton(n))
        return (label_fn(parse_fn(shape)), label_fn(parse_fn(shape)), n)
    return (label_fn(parse_fn(_serialize(chain_skeleton(n, "L")))),
            label_fn(parse_fn(_serialize(chain_skeleton(n, "R")))), n)


def interval_extreme_pair(n, parse_fn, label_fn):
    """Nested-interval disagreement: spine vs balanced."""
    return (label_fn(parse_fn(_serialize(chain_skeleton(n, "L")))),
            label_fn(parse_fn(_serialize(balanced_skeleton(n)))), n)


def inflated_motif_pair(n, motif_keys, parse_fn, label_fn, splay_fn, rng):
    """Inflated extremal motif: motif key pattern replayed on a large spine."""
    start = label_fn(parse_fn(_serialize(chain_skeleton(n, "L"))))
    a_tree, b_tree = start, start
    pattern = list(motif_keys)
    step = 0
    while step < 2 * n:
        key = pattern[step % len(pattern)]
        key = min(max(key, 1), n)
        if step % 3 == 2:
            # DELETE-diverged step: only the A tree splays.
            a_tree = splay_fn(a_tree, key)[0]
        else:
            # KEEP step: both trees splay together.
            a_tree = splay_fn(a_tree, key)[0]
            b_tree = splay_fn(b_tree, key)[0]
        step += 1
    return a_tree, b_tree, n
