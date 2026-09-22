"""F-v0.1 state-only structural features (SA-02, base-WorkPlan compliant).

Allowed inputs: both shapes (A,B), n, key order.
FORBIDDEN during extraction: U/V/G, b_n*, criticality, BFS parents,
witness IDs, cycle membership, forced-edge labels (joined post-hoc only).
Enforced by static audit (test F01 scans this file for forbidden tokens).

Families (all exact integers):
  F-depth: sum/max of |depth_A-depth_B| per key, root agreement.
  F-parent: differing parents, orientation flips (left-vs-right child).
  F-ancestor: ordered-pair (u,v) u!=v counts A-only/B-only/both.
  F-subtree: sum of |size_A-size_B| per key.
  F-rank: comparison signs + ratio pairs are symbolic counts here
    (floor-log2 buckets as separate integer features, never float log).
  F-interval: per-key subtree [min,max] identical-count + symdiff sum.
  F-access-path: per-key path length diffs + symdiff sums.
  F-crossing: FORMAL DEFINITION (see crossing_definition below) then
    ancestor-reversal / endpoint-nesting counts.
  F-heavy: comparator-relative heavy-child agreement counts (frozen defs).
  F-bend: placeholder 0 (mapping from Chmel et al. objects not yet frozen;
    never visual-similarity labeled; preserved as 0 with definition note).

Vectors preserved + hashed: depth_delta_by_key, all-next-key [(c_A,c_B)].
Mirror v->n+1-v on both trees: all F-v0.1 scalars invariant (counts/sums
preserved under joint relabeling); declared per feature in MIRROR_DECLS.
"""

import hashlib
import json

FEATURE_VERSION = "F-v0.1"

MIRROR_DECLS = {
    "f_depth_sum_abs_diff": "invariant",
    "f_depth_max_abs_diff": "invariant",
    "f_root_same": "invariant",
    "f_parent_diff_count": "invariant",
    "f_parent_flip_count": "invariant",
    "f_ancestor_Aonly": "invariant",
    "f_ancestor_Bonly": "invariant",
    "f_ancestor_both": "invariant",
    "f_subtree_sum_abs_diff": "invariant",
    "f_interval_identical_count": "invariant",
    "f_interval_symdiff_sum": "invariant",
    "f_access_sum_abs_diff": "invariant",
    "f_access_symdiff_sum": "invariant",
    "f_crossing_reversal": "invariant",
    "f_heavy_agree_count": "invariant",
    "f_bend_placeholder": "invariant",
}

# Formal crossing definition (required before any feature named crossing):
# For ordered pair (u,v), u!=v, let Anc_A(u,v) be "u ancestor of v in A"
# (strict, via parent pointers), similarly Anc_B. A crossing reversal is an
# ordered pair where Anc_A != Anc_B AND the intervals nest oppositely:
# equivalently counted here as ordered pairs where ancestor status differs
# AND (min/max interval containment differs). For exact integer F-v0.1 we
# count ordered pairs with Anc_A != Anc_B (which equals Aonly+Bonly) as the
# reversal base; endpoint-nesting is captured by interval symdiff. The frozen
# scalar f_crossing_reversal = Aonly + Bonly (documented derived, kept as
# separate atom for stratification, not an independent degree of freedom
# beyond ancestor counts — linear search handles collinearity via rank).


def _build_info(shape_text, assign_fn, parse_fn):
    """Per-tree info: parent/children/depth/size/interval/path."""
    keyed = assign_fn(parse_fn(shape_text))
    # keyed is nested tuple (left, key, right) or () ; collect nodes.
    parent = {}
    left = {}
    right = {}
    nodes = []
    def walk(node, par):
        if node == ():
            return
        l, k, r = node
        nodes.append(k)
        parent[k] = par
        left[k] = None if l == () else l[1]
        right[k] = None if r == () else r[1]
        walk(l, k)
        walk(r, k)
    walk(keyed, -1)
    depth = {}
    for k in nodes:
        d = 0
        cur = k
        while parent[cur] != -1:
            cur = parent[cur]
            d += 1
        depth[k] = d
    # Subtree sizes + intervals via recursion on keyed structure.
    size = {}
    interval = {}
    def rec(node):
        if node == ():
            return (0, None, None)
        l, k, r = node
        ls, lmin, lmax = rec(l)
        rs, rmin, rmax = rec(r)
        sz = 1 + ls + rs
        mn = k
        mx = k
        if lmin is not None:
            mn = min(mn, lmin); mx = max(mx, lmax)
        if rmin is not None:
            mn = min(mn, rmin); mx = max(mx, rmax)
        size[k] = sz
        interval[k] = (mn, mx)
        return (sz, mn, mx)
    rec(keyed)
    # Access paths (root->node inclusive) via parent walk.
    path = {}
    for k in nodes:
        p = []
        cur = k
        while cur != -1:
            p.append(cur)
            cur = parent[cur]
        p.reverse()
        path[k] = p
    # Heavy child (comparator-relative: larger subtree, tie -> smaller key).
    heavy = {}
    for k in nodes:
        lc = left[k]; rc = right[k]
        if lc is None and rc is None:
            heavy[k] = None
        elif lc is None:
            heavy[k] = rc
        elif rc is None:
            heavy[k] = lc
        else:
            sl = size[lc]; sr = size[rc]
            if sl > sr:
                heavy[k] = lc
            elif sr > sl:
                heavy[k] = rc
            else:
                heavy[k] = min(lc, rc)
    # Root.
    root = None
    for k in nodes:
        if parent[k] == -1:
            root = k
    return {"parent": parent, "left": left, "right": right, "depth": depth,
            "size": size, "interval": interval, "path": path,
            "heavy": heavy, "root": root, "nodes": nodes}


def extract_state_features(shape_a, shape_b, target_n, assign_fn, parse_fn):
    """Exact state-only scalars + vectors for one pair state."""
    info_a = _build_info(shape_a, assign_fn, parse_fn)
    info_b = _build_info(shape_b, assign_fn, parse_fn)
    keys = list(range(1, target_n + 1))
    # Depth.
    depth_deltas = [abs(info_a["depth"][k] - info_b["depth"][k]) for k in keys]
    f_depth_sum = sum(depth_deltas)
    f_depth_max = max(depth_deltas) if depth_deltas else 0
    f_root_same = 1 if info_a["root"] == info_b["root"] else 0
    # Parent diff + flips.
    f_parent_diff = 0
    f_parent_flip = 0
    for k in keys:
        pa = info_a["parent"][k]; pb = info_b["parent"][k]
        if pa != pb:
            f_parent_diff += 1
        # Orientation: is k left child of its parent?
        def is_left(info, k):
            par = info["parent"][k]
            if par == -1:
                return None
            return info["left"][par] == k
        la = is_left(info_a, k); lb = is_left(info_b, k)
        if la is not None and lb is not None and la != lb:
            f_parent_flip += 1
    # Ancestor counts (ordered pairs u!=v).
    def is_anc(info, u, v):
        cur = v
        while cur != -1:
            if cur == u:
                return True
            # need parent of cur: info parent dict
            cur = info["parent"].get(cur, -1)
            if cur == -1:
                # v itself? strict ancestor excludes equality; handle u==v separately
                break
        return False
    # Strict: u ancestor of v, u!=v.
    a_only = b_only = both = 0
    for u in keys:
        for v in keys:
            if u == v:
                continue
            aa = is_anc(info_a, u, v)
            bb = is_anc(info_b, u, v)
            if aa and bb:
                both += 1
            elif aa:
                a_only += 1
            elif bb:
                b_only += 1
    # Subtree sizes.
    f_subtree_sum = sum(abs(info_a["size"][k] - info_b["size"][k]) for k in keys)
    # Intervals.
    ident = 0
    sym = 0
    for k in keys:
        ia = info_a["interval"][k]; ib = info_b["interval"][k]
        if ia == ib:
            ident += 1
        # Symmetric difference of [min,max] integer sets = |a-b| endpoint diffs summed.
        sym += abs(ia[0] - ib[0]) + abs(ia[1] - ib[1])
    # Access paths: length diffs (= cost diffs) + symdiff sums.
    access_sum = 0
    access_sym = 0
    for k in keys:
        pa = info_a["path"][k]; pb = info_b["path"][k]
        access_sum += abs(len(pa) - len(pb))
        access_sym += len(set(pa).symmetric_difference(set(pb)))
    # Crossing reversal (frozen def above).
    f_cross = a_only + b_only
    # Heavy agreement.
    heavy_agree = sum(1 for k in keys if info_a["heavy"][k] == info_b["heavy"][k])
    # Bend placeholder (0; mapping not frozen).
    f_bend = 0
    scalars = {
        "f_depth_sum_abs_diff": f_depth_sum,
        "f_depth_max_abs_diff": f_depth_max,
        "f_root_same": f_root_same,
        "f_parent_diff_count": f_parent_diff,
        "f_parent_flip_count": f_parent_flip,
        "f_ancestor_Aonly": a_only,
        "f_ancestor_Bonly": b_only,
        "f_ancestor_both": both,
        "f_subtree_sum_abs_diff": f_subtree_sum,
        "f_interval_identical_count": ident,
        "f_interval_symdiff_sum": sym,
        "f_access_sum_abs_diff": access_sum,
        "f_access_symdiff_sum": access_sym,
        "f_crossing_reversal": f_cross,
        "f_heavy_agree_count": heavy_agree,
        "f_bend_placeholder": f_bend,
    }
    vectors = {
        "depth_delta_by_key": depth_deltas,
        "all_next_key_costs": [(info_a["depth"][k] + 1, info_b["depth"][k] + 1) for k in keys],
    }
    return scalars, vectors


def mirror_shape_key(key, target_n):
    return target_n + 1 - key
