"""Third Splay implementation: index-array copy-on-write (functional style).

State is a triple of tuples (parent, left, right) indexed by key (index 0
unused, -1/0 = null/root markers) plus a root key. Every rotation copies the
arrays, so values are never mutated in place. This representation is
structurally independent of both the nested-tuple reference implementation
and the pointer-object independent auditor. Used for n<=5 cross-checks.
"""

ROOT_NONE = -1
NULL = -1


def from_keyed_tree(t):
    """Build array state from a keyed tuple tree. Returns (parent, left, right, root)."""
    keys = []

    def collect(node):
        if node == ():
            return
        collect(node[0])
        keys.append(node[1])
        collect(node[2])

    collect(t)
    n = len(keys)
    parent = [NULL] * (n + 1)
    left = [NULL] * (n + 1)
    right = [NULL] * (n + 1)

    def go(node, p):
        if node == ():
            return
        l, k, r = node
        parent[k] = p
        if l != ():
            left[k] = l[1]
            go(l, k)
        if r != ():
            right[k] = r[1]
            go(r, k)

    go(t, ROOT_NONE)
    return (tuple(parent), tuple(left), tuple(right), t[1])


def _as_lists(state):
    parent, left, right, root = state
    return [list(parent), list(left), list(right), root]


def rotate_right(state, p):
    """Copy-on-write right rotation at p. Requires a left child."""
    parent, left, right, root = _as_lists(state)
    q = left[p]
    if q == NULL:
        raise ValueError("rotate_right without left child")
    b = right[q]
    right[q] = p
    left[p] = b
    if b != NULL:
        parent[b] = p
    gp = parent[p]
    parent[q] = gp
    parent[p] = q
    if gp == ROOT_NONE:
        root = q
    elif left[gp] == p:
        left[gp] = q
    else:
        right[gp] = q
    return (tuple(parent), tuple(left), tuple(right), root)


def rotate_left(state, p):
    """Copy-on-write left rotation at p. Requires a right child."""
    parent, left, right, root = _as_lists(state)
    q = right[p]
    if q == NULL:
        raise ValueError("rotate_left without right child")
    b = left[q]
    left[q] = p
    right[p] = b
    if b != NULL:
        parent[b] = p
    gp = parent[p]
    parent[q] = gp
    parent[p] = q
    if gp == ROOT_NONE:
        root = q
    elif left[gp] == p:
        left[gp] = q
    else:
        right[gp] = q
    return (tuple(parent), tuple(left), tuple(right), root)


def _depth(state, x):
    parent, left, right, root = state
    d = 0
    v = x
    while v != root:
        v = parent[v]
        d += 1
    return d


def _check(state, n):
    parent, left, right, root = state
    seen = []

    def go(k):
        if k == NULL:
            return
        go(left[k])
        seen.append(k)
        go(right[k])

    go(root)
    if seen != list(range(1, n + 1)):
        raise AssertionError("BST invalid in functional impl")
    for k in range(1, n + 1):
        for side, arr in ((left[k], left), (right[k], right)):
            _ = (side, arr)
        if left[k] != NULL and parent[left[k]] != k:
            raise AssertionError("parent inconsistency")
        if right[k] != NULL and parent[right[k]] != k:
            raise AssertionError("parent inconsistency")


def splay(state, x, n):
    """Bottom-up splay. Returns (new_state, cost, cases)."""
    parent, left, right, root = state
    path = []
    v = x
    while True:
        path.append(v)
        if v == root:
            break
        v = parent[v]
    path.reverse()
    cost = len(path)
    cases = []
    cur = state
    while True:
        parent, left, right, root = cur
        if x == root:
            break
        p = parent[x]
        gp = parent[p]
        x_left = left[p] == x
        if gp == ROOT_NONE:
            cur = rotate_right(cur, p) if x_left else rotate_left(cur, p)
            cases.append("ZIG")
            continue
        p_left = left[gp] == p
        if x_left and p_left:
            cur = rotate_right(cur, gp)
            cur = rotate_right(cur, p)
            cases.append("LL")
        elif not x_left and not p_left:
            cur = rotate_left(cur, gp)
            cur = rotate_left(cur, p)
            cases.append("RR")
        elif not x_left and p_left:
            cur = rotate_left(cur, p)
            cur = rotate_right(cur, gp)
            cases.append("LR")
        else:
            cur = rotate_right(cur, p)
            cur = rotate_left(cur, gp)
            cases.append("RL")
    if cur[3] != x:
        raise AssertionError("x is not root after functional splay")
    _check(cur, n)
    return cur, cost, cases
