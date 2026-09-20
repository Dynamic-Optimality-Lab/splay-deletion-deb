"""Transparent immutable tuple-based BST model (reference implementation).

Representation: EMPTY = (); node = (left, key, right). All operations are
pure functions returning new trees. Deliberately slow and auditable.
Frozen contract: inorder fixed 1..n, root depth 0, cost = depth + 1.
"""

EMPTY = ()


def parse_shape(s):
    """Parse a canonical shape string into a skeleton of () and (L, R) pairs."""
    node, i = _parse(s, 0)
    if i != len(s):
        raise ValueError("trailing characters in shape: %r" % (s,))
    return node


def _parse(s, i):
    if i >= len(s):
        raise ValueError("unexpected end of shape")
    if s[i] == ".":
        return (), i + 1
    if s[i] != "(":
        raise ValueError("expected '(' or '.' at position %d of %r" % (i, s))
    left, j = _parse(s, i + 1)
    right, k = _parse(s, j)
    if k >= len(s) or s[k] != ")":
        raise ValueError("expected ')' at position %d of %r" % (k, s))
    return (left, right), k + 1


def serialize_shape(skel):
    """Serialize a skeleton back to its canonical shape string."""
    if skel == ():
        return "."
    left, right = skel
    return "(" + serialize_shape(left) + serialize_shape(right) + ")"


def assign_inorder_keys(skel):
    """Label a skeleton by inorder rank 1..n. Returns a keyed tree."""
    counter = [0]

    def go(node):
        if node == ():
            return ()
        left, right = node
        l = go(left)
        counter[0] += 1
        key = counter[0]
        r = go(right)
        return (l, key, r)

    return go(skel)


def tree_size(t):
    """Number of nonempty nodes."""
    if t == ():
        return 0
    return 1 + tree_size(t[0]) + tree_size(t[2])


def inorder_keys(t):
    """Inorder key list."""
    if t == ():
        return []
    return inorder_keys(t[0]) + [t[1]] + inorder_keys(t[2])


def validate_bst(t, n):
    """True iff the inorder traversal is exactly 1..n."""
    return inorder_keys(t) == list(range(1, n + 1))


def find_path(t, x):
    """Key list from root to x. Raises KeyError if x is absent."""
    if t == ():
        raise KeyError(x)
    left, k, right = t
    if x == k:
        return [k]
    if x < k:
        return [k] + find_path(left, x)
    return [k] + find_path(right, x)


def compute_depth(t, x):
    """Number of edges on the root-to-x path (root depth 0)."""
    return len(find_path(t, x)) - 1


def access_cost(t, x):
    """Frozen cost convention: c(T,x) = depth + 1."""
    return compute_depth(t, x) + 1


def subtree(t, key):
    """Subtree rooted at key (navigated by BST comparison)."""
    if t == ():
        raise KeyError(key)
    left, k, right = t
    if key == k:
        return t
    if key < k:
        return subtree(left, key)
    return subtree(right, key)


def replace_node(t, path, new_sub):
    """Return a copy of t with the node at root-to-node key path replaced."""
    if len(path) == 1:
        if t == () or t[1] != path[0]:
            raise KeyError(path[0])
        return new_sub
    if t == ():
        raise KeyError(path[0])
    left, k, right = t
    if k != path[0]:
        raise KeyError(path[0])
    if path[1] < k:
        return (replace_node(left, path[1:], new_sub), k, right)
    return (left, k, replace_node(right, path[1:], new_sub))
