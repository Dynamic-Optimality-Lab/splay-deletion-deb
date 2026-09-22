"""Exact structural-info tables + frozen universal H formulas (WP-5 synthesis side).

All values are exact Python ints derived from keyed trees only. No U/V/G,
no b_n*, no witness IDs, no cycle labels enter here. Memoized per keyed-tree
tuple for bulk sweeps.
"""
import sys
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-STR-01]: module import (structural info ready).
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


# Frozen universal constant shared by all WP-5 hypotheses in this phase.
# Rationale (recorded, not fitted): b_H = 2/1 clears every sealed b_n*
# (max b_7* = 23/14; 2*14 = 28 >= 23) with margin, keeping UH-3 green so the
# experiment tests H structure rather than b_H feasibility. One exact value
# for every tested n, fixed before any residual is computed (SA-01 ARCH).
B_H = ("2", "1")

_info_cache = {}


def tree_info(keyed):
    """Exact per-tree structural info for one keyed tree tuple.

    Returns dict with depth/parent/path/is_left/root/keys. Pure function of
    the keyed tree; results memoized by tuple identity.
    """
    hit = _info_cache.get(keyed)
    if hit is not None:
        return hit
    parent = {}

    def walk(node, par):
        if node == ():
            return
        left, key, right = node
        parent[key] = par
        walk(left, key)
        walk(right, key)

    walk(keyed, None)
    root = next(k for k, p in parent.items() if p is None)
    depth = {}
    path = {}
    for key in parent:
        chain = []
        node = key
        while node is not None:
            chain.append(node)
            node = parent[node]
        chain.reverse()
        depth[key] = len(chain) - 1
        path[key] = frozenset(chain)
    left = {}
    right = {}
    size = {}

    def measure(node):
        if node == ():
            return 0
        grown_left, key, grown_right = node
        total = 1 + measure(grown_left) + measure(grown_right)
        size[key] = total
        left[key] = grown_left[1] if grown_left != () else None
        right[key] = grown_right[1] if grown_right != () else None
        return total

    measure(keyed)
    # Heavy child (WP-4 frozen defs, scalar_features.py: larger subtree,
    # tie -> smaller key; sole child if single; None if leaf).
    heavy = {}
    for key in parent:
        left_key = left[key]
        right_key = right[key]
        if left_key is None and right_key is None:
            heavy[key] = None
        elif left_key is None:
            heavy[key] = right_key
        elif right_key is None:
            heavy[key] = left_key
        elif size[left_key] > size[right_key]:
            heavy[key] = left_key
        elif size[right_key] > size[left_key]:
            heavy[key] = right_key
        else:
            heavy[key] = left_key if left_key < right_key else right_key
    info = {"depth": depth, "parent": parent, "path": path,
            "left": left, "right": right, "size": size, "heavy": heavy,
            "root": root, "keys": sorted(parent)}
    _info_cache[keyed] = info
    return info


def _is_ancestor(info, u, v):
    return u != v and u in info["path"][v]


# console.log equivalent [WP5-STR-02]: H-formula definitions frozen below.
def h_depth_sum(info_a, info_b, n):
    """H1-form (local per-node sums): sum_x |depth_A(x) - depth_B(x)|."""
    total = 0
    for key in info_a["keys"]:
        diff = info_a["depth"][key] - info_b["depth"][key]
        total += diff if diff >= 0 else -diff
    return total


def h_ancestor_sym(info_a, info_b, n):
    """H3-form (interval/crossing family): count of ordered pairs (u,v), u != v,
    with ancestor-status disagreement between A and B."""
    total = 0
    for u in info_a["keys"]:
        for v in info_a["keys"]:
            if u == v:
                continue
            if _is_ancestor(info_a, u, v) != _is_ancestor(info_b, u, v):
                total += 1
    return total


def h_access_sym(info_a, info_b, n):
    """H3-form (access-path family): sum_x |path_A(x) symmetric-difference path_B(x)|."""
    total = 0
    for key in info_a["keys"]:
        total += len(info_a["path"][key].symmetric_difference(info_b["path"][key]))
    return total


def h_heavy_disagree(info_a, info_b, n):
    """H5-form (heavy/rank-gap family, WP-4 frozen heavy defs):
    #{v : heavy_A(v) != heavy_B(v)}."""
    return sum(1 for key in info_a["keys"]
               if info_a["heavy"][key] != info_b["heavy"][key])


def h_parent_diff(info_a, info_b, n):
    """H2-form (per-edge family): #{v : parent_A(v) != parent_B(v)}."""
    return sum(1 for key in info_a["keys"]
               if info_a["parent"][key] != info_b["parent"][key])


def h_combo_depth_heavy(info_a, info_b, n):
    """H6-form (combination): depth-sum plus heavy disagreement."""
    return h_depth_sum(info_a, info_b, n) + h_heavy_disagree(info_a, info_b, n)


# Registry: hypothesis_id -> (formula_fn, form_class, definition_text).
# console.log equivalent [WP5-STR-03]: registry frozen (H1-H6 priority order).
H_REGISTRY = {
    "H-0001": (h_depth_sum, "H1",
               "H(A,B) = sum_x |depth_A(x) - depth_B(x)|, b_H = 2/1"),
    "H-0002": (h_ancestor_sym, "H3",
               "H(A,B) = #{(u,v), u!=v : anc_A(u,v) != anc_B(u,v)}, b_H = 2/1"),
    "H-0003": (h_access_sym, "H3",
               "H(A,B) = sum_x |path_A(x) symmetric-difference path_B(x)|, b_H = 2/1"),
    "H-0004": (h_heavy_disagree, "H5",
               "H(A,B) = #{v : heavy_A(v) != heavy_B(v)}, b_H = 2/1"),
    "H-0005": (h_parent_diff, "H2",
               "H(A,B) = #{v : parent_A(v) != parent_B(v)}, b_H = 2/1"),
    "H-0006": (h_combo_depth_heavy, "H6",
               "H(A,B) = sum_x |depth_A(x)-depth_B(x)| + #{v : heavy_A(v) != heavy_B(v)}, b_H = 2/1"),
}
