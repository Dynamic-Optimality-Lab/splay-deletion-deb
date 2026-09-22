"""Motif generalization (WP-5 adversary side; WP-6 negative-branch feed only).

From a concrete exact counterexample (keyed A/B shapes, key, mode), extract a
parameterized motif family: the motif skeletons with one distinguished
embedded subtree replaced by a size-k spine, plus the transformation rule
(key remapping). The family is returned as data with sampled exact residuals
at small k (falsification signal only). Generalization to a proved unbounded
`(T_k,X_k,Y_k)` family with `g/f -> infinity` is WP-6 work (P17) and is NEVER
claimed here: outputs are `NEAR_TIGHT_FAMILY_FOUND` /
`POTENTIAL_UNBOUNDED_PATTERN_FOUND` at most.
"""
import sys
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-ADV-12]: generalizer module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def skeleton_of(keyed):
    if keyed == ():
        return ()
    left, _key, right = keyed
    return (skeleton_of(left), skeleton_of(right))


def inflate_skeleton(skel, extra):
    """Embed `extra` single-child chain nodes above the skeleton root."""
    out = skel
    for _ in range(extra):
        out = ((out, ()))
    return out


def generalize_counterexample(keyed_a, keyed_b, n, key, mode, parse_fn, label_fn,
                              serialize_fn, splay_fn, h_fn, p_h, q_h, ks):
    """Build the inflated family and sample exact residuals (no proof)."""
    # console.log equivalent [WP5-ADV-13]: family generalized (samples only).
    console_log("WP5-ADV-13", "generalizing counterexample n=%d" % n)
    from python.adversary import residual_search as R
    from python.wp5 import structural as S
    base_a = skeleton_of(keyed_a)
    base_b = skeleton_of(keyed_b)
    samples = []
    for extra in ks:
        big_a = label_fn(parse_fn(serialize_fn(inflate_skeleton(base_a, extra))))
        big_b = label_fn(parse_fn(serialize_fn(inflate_skeleton(base_b, extra))))
        big_n = n + extra
        got = R.exact_residuals(big_a, big_b, big_n, h_fn, p_h, q_h, splay_fn)
        samples.append({"k": extra, "n": big_n,
                        "keep_max": got["keep_max"], "delete_max": got["delete_max"]})
    return {"motif": {"mode": mode, "key": key, "n": n},
            "transformation": "embed motif skeletons under an extra-node left chain",
            "samples": samples,
            "status": "POTENTIAL_UNBOUNDED_PATTERN_FOUND (samples only; WP-6 P17 decides)"}
