"""Exact single-tree tables + diagonal-reachable pair graph (reference side).

Single-tree table: for each (T, x): cost, after-tree id, access path,
rotation signature. Inverse tables with conservation. Reachability: BFS from
all diagonals in frozen edge order, parent witnesses, closure sweep.
All artifact writes are deterministic (sorted keys, canonical JSON).
"""

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.reference import enumerate as enum  # noqa: E402
from python.reference import splay as ref_splay  # noqa: E402
from python.reference import tree as ref_tree  # noqa: E402

KEEP, DELETE = 0, 1


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def keyed_shape(t):
    """Erase labels from a reference keyed tree."""
    if t == ():
        return "."
    return "(" + keyed_shape(t[0]) + keyed_shape(t[2]) + ")"


class Tables(object):
    """Single-tree transition + inverse tables for one n."""

    def __init__(self, n, shapes, after, cost, pred):
        self.n = n
        self.shapes = shapes
        self.after = after
        self.cost = cost
        self.pred = pred
        self.tree_count = len(shapes)


def build_tables(n):
    """Build exact single-tree tables. Returns Tables."""
    # console.log equivalent [WP2-TR-01]: single-tree table build begin.
    console_log("WP2-TR-01", "building single-tree tables n=%d" % n)
    shapes = enum.canonical_shapes(n)
    index = {s: i for i, s in enumerate(shapes)}
    after = [[0] * (n + 1) for _ in shapes]
    cost = [[0] * (n + 1) for _ in shapes]
    for tid, shape in enumerate(shapes):
        t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shape))
        for x in range(1, n + 1):
            t2, c, cases, path0 = ref_splay.splay(t, x)
            if not 1 <= c <= n:
                raise AssertionError("cost out of range")
            after_shape = keyed_shape(t2)
            after[tid][x] = index[after_shape]
            cost[tid][x] = c
    pred = [None] + [[[] for _ in shapes] for _ in range(n)]
    for before, _ in enumerate(shapes):
        for x in range(1, n + 1):
            pred[x][after[before][x]].append(before)
    for x in range(1, n + 1):
        if sum(len(v) for v in pred[x]) != len(shapes):
            raise AssertionError("inverse conservation failed")
    # console.log equivalent [WP2-TR-02]: tables verified.
    console_log("WP2-TR-02", "n=%d records=%d conservation ok" % (n, n * len(shapes)))
    return Tables(n, shapes, after, cost, pred)


def pair_successor(tables, pair_id, mode, key):
    """Deterministic (target, a, y) from (source, mode, key)."""
    c = tables.tree_count
    a_id, b_id = divmod(pair_id, c)
    a2 = tables.after[a_id][key]
    a_cost = tables.cost[a_id][key]
    if mode == KEEP:
        b2 = tables.after[b_id][key]
        y = tables.cost[b_id][key]
    else:
        b2 = b_id
        y = 0
    return a2 * c + b2, a_cost, y


class Reachability(object):
    """Diagonal-reachable pair set R_n with parent witnesses."""

    def __init__(self, n, tree_count, pair_ids, index_of, parents):
        self.n = n
        self.tree_count = tree_count
        self.pair_ids = pair_ids
        self.index_of = index_of
        self.parents = parents


def build_reachability(tables):
    """BFS from all diagonals in frozen edge order. Returns Reachability."""
    # console.log equivalent [WP2-RE-01]: reachability BFS begin.
    console_log("WP2-RE-01", "BFS R_%d begin" % tables.n)
    n, c = tables.n, tables.tree_count
    seen = set()
    parents = {}
    queue = []
    for t in range(c):
        d = t * c + t
        seen.add(d)
        queue.append(d)
    head = 0
    while head < len(queue):
        pair = queue[head]
        head += 1
        for mode in (KEEP, DELETE):
            for key in range(1, n + 1):
                target, _, _ = pair_successor(tables, pair, mode, key)
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
                    parents[target] = (pair, mode, key)
    pair_ids = sorted(seen)
    index_of = {p: i for i, p in enumerate(pair_ids)}
    # console.log equivalent [WP2-RE-02]: closure sweep.
    console_log("WP2-RE-02", "closure sweep over %d states" % len(pair_ids))
    for pair in pair_ids:
        for mode in (KEEP, DELETE):
            for key in range(1, n + 1):
                target, _, _ = pair_successor(tables, pair, mode, key)
                if target not in seen:
                    raise AssertionError("forward closure violated")
    # console.log equivalent [WP2-RE-03]: reachability sealed in memory.
    console_log("WP2-RE-03", "R_%d size=%d all_pairs=%s" % (n, len(pair_ids), len(pair_ids) == c * c))
    return Reachability(n, c, pair_ids, index_of, parents)


def _dump_zst(path, obj):
    import zstandard as zstd
    blob = (json.dumps(obj, sort_keys=True) + "\n").encode("utf-8")
    logical = hashlib.sha256(blob).hexdigest()
    with open(path, "wb") as f:
        f.write(zstd.ZstdCompressor(level=19).compress(blob))
    return logical


def write_transitions(tables, outdir):
    """Write forward.bin.zst + inverse.bin.zst + summary.json (exact names)."""
    os.makedirs(outdir, exist_ok=True)
    n = tables.n
    fwd = {"n": n,
           "records": [{"after": tables.after[t][x], "cost": tables.cost[t][x],
                        "tree": t, "x": x}
                       for t in range(tables.tree_count) for x in range(1, n + 1)]}
    inv = {"n": n, "pred": {str(x): tables.pred[x] for x in range(1, n + 1)}}
    h1 = _dump_zst(os.path.join(outdir, "forward.bin.zst"), fwd)
    h2 = _dump_zst(os.path.join(outdir, "inverse.bin.zst"), inv)
    summary = {"cost_in_range": True, "inverse_conservation": True,
               "logical_forward_sha256": h1, "logical_inverse_sha256": h2,
               "n": n, "record_count": n * tables.tree_count,
               "tree_count": tables.tree_count}
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, sort_keys=True, indent=2)
        f.write("\n")
    return summary


def write_reachability(reach, outdir):
    """Write reachable.json.zst + summary.json (exact names)."""
    os.makedirs(outdir, exist_ok=True)
    obj = {"n": reach.n, "pair_ids": reach.pair_ids,
           "parents": {str(p): list(v) for p, v in reach.parents.items()}}
    h = _dump_zst(os.path.join(outdir, "reachable.json.zst"), obj)
    summary = {"all_pairs_reachable_observed": len(reach.pair_ids) == reach.tree_count ** 2,
               "all_pairs_reachable_theorem_used": False,
               "catalan_tree_count": reach.tree_count,
               "forward_closure": True,
               "logical_reachable_sha256": h,
               "n": reach.n,
               "raw_pair_count": reach.tree_count ** 2,
               "reachable_pair_count": len(reach.pair_ids),
               "source_diagonal_count": reach.tree_count}
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, sort_keys=True, indent=2)
        f.write("\n")
    return summary


def main(argv=None):
    """CLI: build transition + reachability artifacts for one n."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--transitions-out", required=True)
    ap.add_argument("--reachability-out", required=True)
    args = ap.parse_args(argv)
    tables = build_tables(args.n)
    write_transitions(tables, args.transitions_out)
    reach = build_reachability(tables)
    write_reachability(reach, args.reachability_out)
    # console.log equivalent [WP2-TR-03]: artifacts written.
    console_log("WP2-TR-03", "n=%d transition+reachability artifacts written" % args.n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
