"""Independent BST model: pointer-object nodes (audit implementation).

This module shares NOTHING with python/reference except the JSON schemas,
the frozen cost definition, and the canonical shape grammar. Nodes are
mutable objects with parent/left/right pointers; every public operation
deep-copies before mutating, so callers observe pure behavior.
"""

EMPTY_SHAPE = "."


class Node(object):
    """A BST node with parent/left/right object pointers (None = absent)."""

    __slots__ = ("key", "parent", "left", "right")

    def __init__(self, key):
        self.key = key
        self.parent = None
        self.left = None
        self.right = None


def parse_shape(s):
    """Parse a canonical shape string into a skeleton of None/(L, R) pairs."""
    node, i = _parse(s, 0)
    if i != len(s):
        raise ValueError("trailing characters in shape: %r" % (s,))
    return node


def _parse(s, i):
    if s[i] == ".":
        return None, i + 1
    if s[i] != "(":
        raise ValueError("bad shape at %d of %r" % (i, s))
    left, j = _parse(s, i + 1)
    right, k = _parse(s, j)
    if s[k] != ")":
        raise ValueError("bad shape at %d of %r" % (k, s))
    return (left, right), k + 1


def serialize_shape(skel):
    """Serialize a skeleton back to its canonical shape string."""
    if skel is None:
        return "."
    return "(" + serialize_shape(skel[0]) + serialize_shape(skel[1]) + ")"


def build_tree(skel):
    """Build a pointer tree from a skeleton, labeling keys by inorder rank."""
    counter = [0]

    def go(node):
        if node is None:
            return None
        left = go(node[0])
        counter[0] += 1
        here = Node(counter[0])
        here.left = left
        if left is not None:
            left.parent = here
        here.right = go(node[1])
        if here.right is not None:
            here.right.parent = here
        return here

    return go(skel)


def clone(root):
    """Deep-copy a pointer tree."""
    if root is None:
        return None
    table = {}

    def go(node, parent):
        if node is None:
            return None
        new = Node(node.key)
        new.parent = parent
        table[node.key] = new
        new.left = go(node.left, new)
        new.right = go(node.right, new)
        return new

    return go(root, None)


def _inorder(root, out):
    if root is None:
        return
    _inorder(root.left, out)
    out.append(root.key)
    _inorder(root.right, out)


def validate_bst(root, n):
    """True iff the inorder traversal is exactly 1..n."""
    out = []
    _inorder(root, out)
    return out == list(range(1, n + 1))


def locate(root, x):
    """Find the node with key x by BST search. Raises KeyError if absent."""
    v = root
    while v is not None:
        if x == v.key:
            return v
        v = v.left if x < v.key else v.right
    raise KeyError(x)


def find_path(root, x):
    """Key list from root to x. Raises KeyError if x is absent."""
    locate(root, x)
    path = []
    v = locate(root, x)
    while v is not None:
        path.append(v.key)
        v = v.parent
    path.reverse()
    return path


def compute_depth(root, x):
    """Number of edges on the root-to-x path (root depth 0)."""
    return len(find_path(root, x)) - 1


def access_cost(root, x):
    """Frozen cost convention: c(T,x) = depth + 1."""
    return compute_depth(root, x) + 1


def tree_size(root):
    """Number of nodes."""
    if root is None:
        return 0
    return 1 + tree_size(root.left) + tree_size(root.right)


def shape_of(root):
    """Canonical shape string of a pointer tree."""

    def go(node):
        if node is None:
            return "."
        return "(" + go(node.left) + go(node.right) + ")"

    return go(root)
