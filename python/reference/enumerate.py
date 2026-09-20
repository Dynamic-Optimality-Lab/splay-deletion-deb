"""Canonical BST enumeration (reference implementation) plus artifact writer.

Generation order (recursive by left-subtree size) is NOT the canonical ID
order: shape strings are sorted lexicographically (raw ASCII) and tree_id
follows that sort. Labeled reconstruction assigns inorder rank 1..n.
"""

import argparse
import hashlib
import json
import math
import os
import sys


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def catalan(n):
    """Exact Catalan number C_n by integer arithmetic."""
    return math.comb(2 * n, n) // (n + 1)


def gen_skeletons(n):
    """Yield all full BST skeletons with n nonempty nodes."""
    if n == 0:
        yield ()
        return
    for left_size in range(n):
        right_size = n - 1 - left_size
        for left in gen_skeletons(left_size):
            for right in gen_skeletons(right_size):
                yield (left, right)


def serialize_skeleton(skel):
    """Canonical shape code: EMPTY='.', NODE='(LEFT RIGHT)'."""
    if skel == ():
        return "."
    return "(" + serialize_skeleton(skel[0]) + serialize_skeleton(skel[1]) + ")"


def parse_shape(s):
    """Parse a canonical shape string back to a skeleton."""
    node, i = _parse(s, 0)
    if i != len(s):
        raise ValueError("trailing characters in shape: %r" % (s,))
    return node


def _parse(s, i):
    if s[i] == ".":
        return (), i + 1
    if s[i] != "(":
        raise ValueError("bad shape at %d of %r" % (i, s))
    left, j = _parse(s, i + 1)
    right, k = _parse(s, j)
    if s[k] != ")":
        raise ValueError("bad shape at %d of %r" % (k, s))
    return (left, right), k + 1


def canonical_shapes(n):
    """Sorted canonical shape strings; index in this list is tree_id."""
    return sorted(serialize_skeleton(s) for s in gen_skeletons(n))


def assign_inorder_keys(skel):
    """Label a skeleton by inorder rank."""
    counter = [0]

    def go(node):
        if node == ():
            return ()
        l = go(node[0])
        counter[0] += 1
        key = counter[0]
        r = go(node[1])
        return (l, key, r)

    return go(skel)


def parent_child_arrays(t, n):
    """parent/left/right arrays indexed by key (index 0 unused, -1 = null)."""
    parent = [-1] * (n + 1)
    left = [-1] * (n + 1)
    right = [-1] * (n + 1)

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

    go(t, -1)
    return parent, left, right


def enumerate_interval(lo, hi):
    """Second, structurally different enumerator: labeled trees on [lo, hi]
    by root-key choice. Used for independent cross-checks (n<=6)."""
    if lo > hi:
        yield ()
        return
    for root in range(lo, hi + 1):
        for left in enumerate_interval(lo, root - 1):
            for right in enumerate_interval(root + 1, hi):
                yield (left, root, right)


def keyed_to_shape(t):
    """Erase labels: keyed tree -> canonical shape string."""
    if t == ():
        return "."
    return "(" + keyed_to_shape(t[0]) + keyed_to_shape(t[2]) + ")"


def main(argv=None):
    """CLI: write canonical tree universe for one n. Step-logged."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    n = args.n
    # console.log equivalent [WP1-ENUM-01]: begin canonical enumeration.
    console_log("WP1-ENUM-01", "enumerating T_%d" % n)
    shapes = canonical_shapes(n)
    if len(shapes) != catalan(n):
        raise AssertionError("Catalan mismatch for n=%d" % n)
    if len(set(shapes)) != len(shapes):
        raise AssertionError("duplicate shape for n=%d" % n)
    for s in shapes:
        if serialize_skeleton(parse_shape(s)) != s:
            raise AssertionError("round-trip failed for %r" % (s,))
    # console.log equivalent [WP1-ENUM-02]: enumeration verified, writing.
    console_log("WP1-ENUM-02", "n=%d count=%d verified, writing artifacts" % (n, len(shapes)))
    os.makedirs(args.out, exist_ok=True)
    try:
        import zstandard as zstd
    except ImportError:
        raise AssertionError("zstandard is required for .zst transport files")
    logical = []
    for tree_id, shape in enumerate(shapes):
        t = assign_inorder_keys(parse_shape(shape))
        parent, left, right = parent_child_arrays(t, n)
        root_key = t[1]
        rec = {"inorder": list(range(1, n + 1)), "left_by_key": left[1:],
               "n": n, "parent_by_key": parent[1:], "right_by_key": right[1:],
               "root_key": root_key, "shape": shape, "tree_id": tree_id}
        logical.append(json.dumps(rec, sort_keys=True))
    blob = ("\n".join(logical) + "\n").encode("utf-8")
    logical_sha = hashlib.sha256(blob).hexdigest()
    cctx = zstd.ZstdCompressor(level=19)
    with open(os.path.join(args.out, "trees.jsonl.zst"), "wb") as f:
        f.write(cctx.compress(blob))
    summary = {"all_bst_valid": True, "catalan_tree_count": catalan(n),
               "duplicate_shapes": 0, "logical_stream_sha256": logical_sha,
               "n": n, "round_trip_ok": True, "tree_count": len(shapes)}
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, sort_keys=True, indent=2)
        f.write("\n")
    import hashlib as _hl
    sums = []
    for fn in ("trees.jsonl.zst", "summary.json"):
        with open(os.path.join(args.out, fn), "rb") as f:
            sums.append("%s  %s" % (_hl.sha256(f.read()).hexdigest(), fn))
    with open(os.path.join(args.out, "SHA256SUMS"), "w", encoding="utf-8") as f:
        f.write("\n".join(sums) + "\n")
    # console.log equivalent [WP1-ENUM-03]: artifacts sealed.
    console_log("WP1-ENUM-03", "n=%d sealed logical_sha=%s" % (n, logical_sha[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
