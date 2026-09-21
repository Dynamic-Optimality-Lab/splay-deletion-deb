"""Independent graph builder for audit verifiers (no python/reference imports).

Shares NOTHING with the reference implementation except JSON schemas, the
frozen cost definition, and the canonical shape grammar. Shape generation,
single-tree transitions (via the independent pointer-object Splay), inverse
tables, and BFS reachability are all re-derived here. Used by all three
audit verifiers, which remain independent of python/reference by construction.
"""

from python.audit import independent_splay, independent_tree

KEEP, DELETE = 0, 1


def gen_skeletons(n):
    """Yield all BST skeletons with n nodes (recursive by left size)."""
    if n == 0:
        yield None
        return
    for left_size in range(n):
        for left in gen_skeletons(left_size):
            for right in gen_skeletons(n - 1 - left_size):
                yield (left, right)


def canonical_shapes(n):
    """Sorted canonical shape strings; index is tree_id."""
    return sorted(independent_tree.serialize_shape(s) for s in gen_skeletons(n))


class Tables(object):
    """Independently derived single-tree tables for one n."""

    def __init__(self, n, shapes, after, cost, pred):
        self.n = n
        self.shapes = shapes
        self.after = after
        self.cost = cost
        self.pred = pred
        self.tree_count = len(shapes)


def build_tables(n):
    """Build tables via the independent Splay implementation."""
    shapes = canonical_shapes(n)
    index = {s: i for i, s in enumerate(shapes)}
    after = [[0] * (n + 1) for _ in shapes]
    cost = [[0] * (n + 1) for _ in shapes]
    for tid, shape in enumerate(shapes):
        root = independent_tree.build_tree(independent_tree.parse_shape(shape))
        for x in range(1, n + 1):
            r2, c, _ = independent_splay.splay(root, x)
            if not 1 <= c <= n:
                raise AssertionError("cost out of range")
            after[tid][x] = index[independent_tree.shape_of(r2)]
            cost[tid][x] = c
    pred = [None] + [[[] for _ in shapes] for _ in range(n)]
    for before in range(len(shapes)):
        for x in range(1, n + 1):
            pred[x][after[before][x]].append(before)
    return Tables(n, shapes, after, cost, pred)


def successor(tables, pair_id, mode, key):
    """Deterministic (target, a, y) from (source, mode, key)."""
    c = tables.tree_count
    a_id, b_id = divmod(pair_id, c)
    a2 = tables.after[a_id][key]
    a_cost = tables.cost[a_id][key]
    if mode == KEEP:
        return a2 * c + tables.after[b_id][key], a_cost, tables.cost[b_id][key]
    return a2 * c + b_id, a_cost, 0


class Reachability(object):
    """Independently derived R_n with parent witnesses."""

    def __init__(self, n, tree_count, pair_ids, index_of, parents):
        self.n = n
        self.tree_count = tree_count
        self.pair_ids = pair_ids
        self.index_of = index_of
        self.parents = parents


def build_reachability(tables):
    """BFS from all diagonals in frozen edge order."""
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
                target, _, _ = successor(tables, pair, mode, key)
                if target not in seen:
                    seen.add(target)
                    queue.append(target)
                    parents[target] = (pair, mode, key)
    return Reachability(n, c, sorted(seen), {p: i for i, p in enumerate(sorted(seen))}, parents)
