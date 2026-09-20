"""Independent bottom-up Splay on pointer-object nodes (audit implementation).

Written without importing python/reference. Rotation logic is expressed as
pointer surgery keyed on child-direction queries, a different code path from
both the tuple-rebuild reference and the array-based functional variant.
"""

from .independent_tree import (
    access_cost,
    clone,
    compute_depth,
    find_path,
    locate,
    shape_of,
    tree_size,
    validate_bst,
)


def _side(v):
    """Child direction of v under its parent: 'L', 'R', or None for root."""
    p = v.parent
    if p is None:
        return None
    if p.left is v:
        return "L"
    if p.right is v:
        return "R"
    raise AssertionError("parent/child pointer mismatch")


def _rotate_right_at(root, p):
    """Right rotation at node object p. Returns the (possibly new) root."""
    q = p.left
    if q is None:
        raise ValueError("rotate_right without left child")
    beta = q.right
    q.right = p
    q.parent = p.parent
    if p.parent is not None:
        if p.parent.left is p:
            p.parent.left = q
        else:
            p.parent.right = q
    p.parent = q
    p.left = beta
    if beta is not None:
        beta.parent = p
    return q if q.parent is None else root


def _rotate_left_at(root, p):
    """Left rotation at node object p. Returns the (possibly new) root."""
    q = p.right
    if q is None:
        raise ValueError("rotate_left without right child")
    beta = q.left
    q.left = p
    q.parent = p.parent
    if p.parent is not None:
        if p.parent.left is p:
            p.parent.left = q
        else:
            p.parent.right = q
    p.parent = q
    p.right = beta
    if beta is not None:
        beta.parent = p
    return q if q.parent is None else root


def _check_links(root):
    """Assert mutual parent/child consistency over the whole tree."""
    def go(v):
        if v is None:
            return
        if v.left is not None and v.left.parent is not v:
            raise AssertionError("left link mismatch")
        if v.right is not None and v.right.parent is not v:
            raise AssertionError("right link mismatch")
        go(v.left)
        go(v.right)

    go(root)


def splay(root, x):
    """Bottom-up splay of x on a cloned tree. Returns (root, cost, cases)."""
    work = clone(root)
    n = tree_size(work)
    cost = access_cost(work, x)
    cases = []
    while True:
        v = locate(work, x)
        if v.parent is None:
            break
        p = v.parent
        g = p.parent
        sv, sp = _side(v), _side(p)
        if g is None:
            work = _rotate_right_at(work, p) if sv == "L" else _rotate_left_at(work, p)
            cases.append("ZIG")
        elif sv == "L" and sp == "L":
            work = _rotate_right_at(work, g)
            work = _rotate_right_at(work, p)
            cases.append("LL")
        elif sv == "R" and sp == "R":
            work = _rotate_left_at(work, g)
            work = _rotate_left_at(work, p)
            cases.append("RR")
        elif sv == "R" and sp == "L":
            work = _rotate_left_at(work, p)
            work = _rotate_right_at(work, g)
            cases.append("LR")
        else:
            work = _rotate_right_at(work, p)
            work = _rotate_left_at(work, g)
            cases.append("RL")
        _check_links(work)
    if locate(work, x).parent is not None:
        raise AssertionError("x is not root after independent splay")
    if not validate_bst(work, n):
        raise AssertionError("BST invalid after independent splay")
    _ = (find_path, compute_depth, shape_of)
    return work, cost, cases
