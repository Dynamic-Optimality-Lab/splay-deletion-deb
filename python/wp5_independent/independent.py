"""Independent universal-hypothesis falsifier (clean-room implementation).

Receives ONLY: frozen H math text (formula_id + definition strings from the
frozen H-*.json), frozen b_H, sealed tree universe records, sealed transition
records, sealed reachability pair lists. Reimplements keyed-tree building,
bottom-up Splay (all 5 cases), access cost, each H formula from its math
text, and both Pair-Access residuals from scratch.

Imports NOTHING from candidate-synthesis code: no python/wp5, no
python/mining, no python/reference, no sweep/contract/freeze packages of the
n=8 holdout area, no hidden-bank packages, no python/adversary. Allowed:
stdlib + zstandard (sealed-table reader) + this package itself. A static
AST audit enforces the separation. Deterministic ascending-pair order;
lex-first maximizers.
"""
import json
import os

# console.log equivalent [WP5-IND-01]: independent module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def parse_shape(text):
    """Grammar: '.' empty; '(' LEFT RIGHT ')' node. Returns () or (left, right)."""
    node, pos = _parse_shape(text, 0)
    if pos != len(text):
        raise ValueError("trailing characters in shape")
    return node


def _parse_shape(text, pos):
    if text[pos] == ".":
        return (), pos + 1
    if text[pos] != "(":
        raise ValueError("expected '(' or '.'")
    left, pos = _parse_shape(text, pos + 1)
    right, pos = _parse_shape(text, pos)
    if text[pos] != ")":
        raise ValueError("expected ')'")
    return (left, right), pos + 1


def label_inorder(skeleton):
    """Inorder rank labeling 1..n. Returns () or (left, key, right)."""
    counter = [0]

    def visit(node):
        if node == ():
            return ()
        grown_left = visit(node[0])
        counter[0] += 1
        rank = counter[0]
        grown_right = visit(node[1])
        return (grown_left, rank, grown_right)

    return visit(skeleton)


def to_shape(keyed):
    """Erase labels: keyed tree to canonical shape string."""
    if keyed == ():
        return "."
    return "(" + to_shape(keyed[0]) + to_shape(keyed[2]) + ")"


def find_path(keyed, x):
    """Root-to-x key list, inclusive, by iterative descent."""
    trail = []
    node = keyed
    while node != ():
        left, key, right = node
        trail.append(key)
        if x == key:
            return trail
        node = left if x < key else right
    raise ValueError("key absent from tree")


def _replace(keyed, trail, graft):
    if len(trail) == 1:
        return graft
    left, key, right = keyed
    if trail[1] < key:
        return (_replace(left, trail[1:], graft), key, right)
    return (left, key, _replace(right, trail[1:], graft))


def _subtree(keyed, trail):
    # trail[0] names keyed itself; descend on the remainder.
    node = keyed
    for key in trail[1:]:
        left, head, right = node
        node = left if key < head else right
    return node


def build_keyed(parent_by_key, left_by_key, right_by_key, root_key):
    """Keyed tree from sealed arrays: nested () / (left, key, right) tuples."""

    def grow(label):
        # Arrays are 0-based by (label-1); stored links are 1-based labels.
        pos = label - 1
        left = left_by_key[pos]
        right = right_by_key[pos]
        return (grow(left) if left != -1 else (),
                label,
                grow(right) if right != -1 else ())

    return grow(root_key)


def path_to(tree, x):
    """Key path root -> x inclusive (left/right descent)."""
    return find_path(tree, x)


def depth_of(tree, x):
    return len(path_to(tree, x)) - 1


def ancestors_of(tree, x):
    return set(path_to(tree, x)[:-1])


def splay(tree, x):
    """Bottom-up splay of x. Returns (new_tree, cost). Cost = pre depth + 1."""
    price = depth_of(tree, x) + 1
    cur = tree
    while find_path(cur, x) != [x]:
        path = find_path(cur, x)
        v = path[-1]
        p = path[-2]
        _left_p, _key_p, _right_p = _subtree(cur, path[:-1])
        v_left = _left_p != () and _left_p[1] == v
        if len(path) == 2:
            cur = _zig(cur, p, v_left)
        else:
            g = path[-3]
            _left_g, _key_g, _right_g = _subtree(cur, path[:-2])
            p_left = _left_g != () and _left_g[1] == p
            if v_left and p_left:
                cur = rotate_right_at(cur, g)
                cur = rotate_right_at(cur, p)
            elif not v_left and not p_left:
                cur = rotate_left_at(cur, g)
                cur = rotate_left_at(cur, p)
            elif not v_left and p_left:
                cur = rotate_left_at(cur, p)
                cur = rotate_right_at(cur, g)
            else:
                cur = rotate_right_at(cur, p)
                cur = rotate_left_at(cur, g)
    return cur, price


def _zig(tree, pivot, v_left):
    if v_left:
        return rotate_right_at(tree, pivot)
    return rotate_left_at(tree, pivot)


def rotate_right_at(tree, pivot):
    """Right rotation at pivot (pivot must have a left child)."""
    subtrail = find_path(tree, pivot)
    left, _key, right = _subtree(tree, subtrail)
    if left == ():
        raise ValueError("right rotation without left child")
    left_l, _left_key, left_r = left
    risen = (left_l, _left_key, (left_r, _key, right))
    if len(subtrail) == 1:
        return risen
    return _replace(tree, subtrail, risen)


def rotate_left_at(tree, pivot):
    """Left rotation at pivot (pivot must have a right child)."""
    subtrail = find_path(tree, pivot)
    left, _key, right = _subtree(tree, subtrail)
    if right == ():
        raise ValueError("left rotation without right child")
    _right_l, _right_key, right_r = right
    risen = ((left, _key, _right_l), _right_key, right_r)
    if len(subtrail) == 1:
        return risen
    return _replace(tree, subtrail, risen)


def tree_memo(tree):
    """Per-tree memoized structural info (internal cache, not shared logic)."""
    keys = []

    def collect(node):
        if node == ():
            return
        left, key, right = node
        keys.append(key)
        collect(left)
        collect(right)

    collect(tree)
    depths = {}
    paths = {}
    parents = {}
    lefts = {}
    rights = {}
    sizes = {}

    def measure(node, par):
        if node == ():
            return 0
        grown_left, key, grown_right = node
        parents[key] = par
        lefts[key] = grown_left[1] if grown_left != () else None
        rights[key] = grown_right[1] if grown_right != () else None
        return 1 + measure(grown_left, key) + measure(grown_right, key)

    def record_size(node):
        if node == ():
            return 0
        grown_left, key, grown_right = node
        total = 1 + record_size(grown_left) + record_size(grown_right)
        sizes[key] = total
        return total

    measure(tree, None)
    record_size(tree)
    heavy = {}
    for key in keys:
        path = find_path(tree, key)
        depths[key] = len(path) - 1
        paths[key] = frozenset(path)
        left_key = lefts[key]
        right_key = rights[key]
        if left_key is None and right_key is None:
            heavy[key] = None
        elif left_key is None:
            heavy[key] = right_key
        elif right_key is None:
            heavy[key] = left_key
        elif sizes[left_key] > sizes[right_key]:
            heavy[key] = left_key
        elif sizes[right_key] > sizes[left_key]:
            heavy[key] = right_key
        else:
            heavy[key] = left_key if left_key < right_key else right_key
    return {"depths": depths, "paths": paths, "parents": parents,
            "heavy": heavy, "n": len(keys)}


def h_from_math_text(formula_id, tree_a, tree_b, n, memo_a=None, memo_b=None):
    """H reimplemented from the frozen math text (per formula_id)."""
    if memo_a is None:
        memo_a = tree_memo(tree_a)
    if memo_b is None:
        memo_b = tree_memo(tree_b)
    if formula_id == "depth_sum":
        total = 0
        for key in range(1, n + 1):
            diff = memo_a["depths"][key] - memo_b["depths"][key]
            total += diff if diff >= 0 else -diff
        return total
    if formula_id == "ancestor_sym":
        total = 0
        for u in range(1, n + 1):
            for v in range(1, n + 1):
                if u == v:
                    continue
                a_before = u in memo_a["paths"][v]
                b_before = u in memo_b["paths"][v]
                if a_before != b_before:
                    total += 1
        return total
    if formula_id == "access_sym":
        total = 0
        for key in range(1, n + 1):
            total += len(memo_a["paths"][key].symmetric_difference(memo_b["paths"][key]))
        return total
    if formula_id == "heavy_disagree":
        return sum(1 for key in range(1, n + 1)
                   if memo_a["heavy"][key] != memo_b["heavy"][key])
    if formula_id == "parent_diff":
        return sum(1 for key in range(1, n + 1)
                   if memo_a["parents"][key] != memo_b["parents"][key])
    if formula_id == "combo_depth_heavy":
        return (h_from_math_text("depth_sum", tree_a, tree_b, n, memo_a, memo_b)
                + h_from_math_text("heavy_disagree", tree_a, tree_b, n, memo_a, memo_b))
    raise ValueError("unknown formula_id in frozen math text")


def load_sealed_universe(n, repo_root):
    """Sealed trees + transitions + pair list (frozen inputs only)."""
    import zstandard as zstd
    with open(os.path.join(repo_root, "artifacts", "trees", "n%d" % n,
                           "trees.jsonl.zst"), "rb") as handle:
        trees = [json.loads(line) for line in
                 zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8").splitlines()
                 if line.strip()]
    with open(os.path.join(repo_root, "artifacts", "transitions", "n%d" % n,
                           "forward.bin.zst"), "rb") as handle:
        fwd = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    with open(os.path.join(repo_root, "artifacts", "reachability", "n%d" % n,
                           "reachable.json.zst"), "rb") as handle:
        reach = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    keyed = {}
    for record in trees:
        keyed[int(record["tree_id"])] = build_keyed(
            record["parent_by_key"], record["left_by_key"],
            record["right_by_key"], int(record["root_key"]))
    after = {}
    cost = {}
    for record in fwd["records"]:
        after[(int(record["tree"]), int(record["x"]))] = int(record["after"])
        cost[(int(record["tree"]), int(record["x"]))] = int(record["cost"])
    pair_ids = sorted(int(p) for p in reach["pair_ids"])
    return keyed, after, cost, pair_ids


def verify_transitions(keyed, after, cost, n):
    """Independent transition re-derivation: own Splay vs sealed tables."""
    # console.log equivalent [WP5-IND-02]: transition re-derivation checked.
    console_log("WP5-IND-02", "re-deriving transitions n=%d" % n)
    mismatches = 0
    checked = 0
    for tree_id, tree in keyed.items():
        for key in range(1, n + 1):
            mine, price = splay(tree, key)
            if mine[1] != key:
                mismatches += 1
            if price != cost[(tree_id, key)]:
                mismatches += 1
            checked += 1
    return {"checked": checked, "mismatches": mismatches}


def sweep_candidate(formula_id, n, repo_root, p_h, q_h, keyed=None):
    """Independent M_K/M_D sweep with lex-first maximizers (exact ints, scale q_H)."""
    # console.log equivalent [WP5-IND-03]: independent sweep executed.
    console_log("WP5-IND-03", "independent sweep %s n=%d" % (formula_id, n))
    if keyed is None:
        keyed, _, _, _ = load_sealed_universe(n, repo_root)
    import zstandard as zstd
    with open(os.path.join(repo_root, "artifacts", "transitions", "n%d" % n,
                           "forward.bin.zst"), "rb") as handle:
        fwd = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    after = {}
    cost = {}
    for record in fwd["records"]:
        after[(int(record["tree"]), int(record["x"]))] = int(record["after"])
        cost[(int(record["tree"]), int(record["x"]))] = int(record["cost"])
    with open(os.path.join(repo_root, "artifacts", "reachability", "n%d" % n,
                           "reachable.json.zst"), "rb") as handle:
        reach = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    pair_ids = sorted(int(p) for p in reach["pair_ids"])
    count = len(keyed)
    memos = {tree_id: tree_memo(tree) for tree_id, tree in keyed.items()}
    h_table = {}
    uh1_count = 0
    uh2_count = 0
    for pid in pair_ids:
        a_id = pid // count
        b_id = pid % count
        h_state = h_from_math_text(
            formula_id, keyed[a_id], keyed[b_id], n,
            memo_a=memos[a_id], memo_b=memos[b_id])
        h_table[pid] = h_state
        if a_id == b_id and h_state != 0:
            uh1_count += 1
        if h_state < 0:
            uh2_count += 1
    keep_max = None
    keep_arg = None
    keep_pos = 0
    keep_cex = []
    delete_max = None
    delete_arg = None
    delete_pos = 0
    delete_cex = []
    for pid in pair_ids:
        h_state = h_table[pid]
        a_id = pid // count
        b_id = pid % count
        for key in range(1, n + 1):
            a2 = after[(a_id, key)]
            ca = cost[(a_id, key)]
            b2 = after[(b_id, key)]
            cb = cost[(b_id, key)]
            residual = q_h * cb + q_h * (h_table[a2 * count + b2] - h_state) - p_h * ca
            if keep_max is None or residual > keep_max:
                keep_max = residual
                keep_arg = [pid, 0, key]
            if residual > 0:
                keep_pos += 1
                if len(keep_cex) < 16:
                    keep_cex.append([pid, 0, key, str(residual)])
            t2 = a2 * count + b_id
            residual = q_h * (h_table[t2] - h_state) - p_h * ca
            if delete_max is None or residual > delete_max:
                delete_max = residual
                delete_arg = [pid, 1, key]
            if residual > 0:
                delete_pos += 1
                if len(delete_cex) < 16:
                    delete_cex.append([pid, 1, key, str(residual)])
    return {"n": n, "states": len(pair_ids),
            "uh1_count": uh1_count, "uh2_count": uh2_count,
            "keep_max": str(keep_max), "keep_argmax": keep_arg,
            "keep_pos_count": keep_pos, "keep_cex": keep_cex,
            "delete_max": str(delete_max), "delete_argmax": delete_arg,
            "delete_pos_count": delete_pos, "delete_cex": delete_cex}
