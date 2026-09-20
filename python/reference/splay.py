"""Bottom-up Splay, exactly the five frozen cases (reference implementation).

Cases: ZIG, ZIG-ZIG LL, ZIG-ZIG RR, ZIG-ZAG LR, ZIG-ZAG RL.
Post-condition of splay: x is root, tree is a valid BST on the same keys.
"""

from .tree import EMPTY, find_path, replace_node, subtree, tree_size, validate_bst


def rotate_right(t, p):
    """Right rotation at node p. Requires a left child (else ValueError)."""
    path = find_path(t, p)
    left, pk, right = subtree(t, p)
    if left == ():
        raise ValueError("rotate_right without left child at %r" % (p,))
    ll, qk, lr = left
    new_sub = (ll, qk, (lr, pk, right))
    return replace_node(t, path, new_sub)


def rotate_left(t, p):
    """Left rotation at node p. Requires a right child (else ValueError)."""
    path = find_path(t, p)
    left, pk, right = subtree(t, p)
    if right == ():
        raise ValueError("rotate_left without right child at %r" % (p,))
    rl, qk, rr = right
    new_sub = ((left, pk, rl), qk, rr)
    return replace_node(t, path, new_sub)


def splay(t, x):
    """Bottom-up splay of x. Returns (new_tree, cost, cases, access_path)."""
    n = tree_size(t)
    path0 = find_path(t, x)
    cost = len(path0)
    cases = []
    cur = t
    while True:
        path = find_path(cur, x)
        if len(path) == 1:
            break
        v = path[-1]
        p = path[-2]
        v_is_left = v < p
        if len(path) == 2:
            cur = rotate_right(cur, p) if v_is_left else rotate_left(cur, p)
            cases.append("ZIG")
        else:
            g = path[-3]
            p_is_left = p < g
            if v_is_left and p_is_left:
                cur = rotate_right(cur, g)
                cur = rotate_right(cur, p)
                cases.append("LL")
            elif not v_is_left and not p_is_left:
                cur = rotate_left(cur, g)
                cur = rotate_left(cur, p)
                cases.append("RR")
            elif not v_is_left and p_is_left:
                cur = rotate_left(cur, p)
                cur = rotate_right(cur, g)
                cases.append("LR")
            else:
                cur = rotate_right(cur, p)
                cur = rotate_left(cur, g)
                cases.append("RL")
    if find_path(cur, x) != [x]:
        raise AssertionError("x is not root after splay")
    if not validate_bst(cur, n):
        raise AssertionError("BST invalid after splay")
    return cur, cost, cases, path0
