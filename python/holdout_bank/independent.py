"""Clean-room H1 evaluator (SA-04 §SA-04.5/10; independent twin).

Implements tree-shape parsing, inorder key labeling, bottom-up Splay (all 5
cases from the frozen contract text), access cost, KEEP/DELETE transitions,
history replay, and both Pair-Access residuals from scratch. Imports NOTHING
from this repository: only json/zstandard/os/argparse from the environment.
No sys.path manipulation. A static audit (SA04-SEP twin rule) enforces this.
"""
import json
import os

KEEP, DELETE = 0, 1


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def parse_shape(s):
    """Grammar: '.' empty; '(' LEFT RIGHT ')' node. Returns () or (L, R)."""
    node, i = _parse(s, 0)
    if i != len(s):
        raise ValueError("trailing characters in shape")
    return node


def _parse(s, i):
    if s[i] == ".":
        return (), i + 1
    if s[i] != "(":
        raise ValueError("expected '(' or '.'")
    left, j = _parse(s, i + 1)
    right, k = _parse(s, j)
    if s[k] != ")":
        raise ValueError("expected ')'")
    return (left, right), k + 1


def label_inorder(skel):
    """Inorder rank labeling 1..n. Returns () or (left, key, right)."""
    counter = [0]

    def go(node):
        if node == ():
            return ()
        left, right = node
        l = go(left)
        counter[0] += 1
        key = counter[0]  # capture BEFORE right recursion (else keys skew)
        r = go(right)
        return (l, key, r)

    return go(skel)


def to_shape(t):
    """Erase labels: keyed tree -> canonical shape string."""
    if t == ():
        return "."
    return "(" + to_shape(t[0]) + to_shape(t[2]) + ")"


def find_path(t, x):
    """Root-to-x key path (inclusive)."""
    path = []
    node = t
    while node != ():
        l, k, r = node
        path.append(k)
        if x == k:
            return path
        node = l if x < k else r
    raise ValueError("key not found")


def _replace(t, path, new_sub):
    if len(path) == 1:
        return new_sub
    l, k, r = t
    if path[1] < k:
        return (_replace(l, path[1:], new_sub), k, r)
    return (l, k, _replace(r, path[1:], new_sub))


def _subtree(t, keys):
    # keys[0] is the key of t itself; descend on the remainder.
    node = t
    for k in keys[1:]:
        l, kk, r = node
        node = l if k < kk else r
    return node


def rotate_right(t, p):
    path = find_path(t, p)
    left, _pk, right = _subtree(t, path)
    if left == ():
        raise ValueError("rotate_right without left child")
    ll, qk, lr = left
    return _replace(t, path, (ll, qk, (lr, _pk, right)))


def rotate_left(t, p):
    path = find_path(t, p)
    left, _pk, right = _subtree(t, path)
    if right == ():
        raise ValueError("rotate_left without right child")
    rl, qk, rr = right
    return _replace(t, path, ((left, _pk, rl), qk, rr))


def splay(t, x):
    """Bottom-up splay of x. Returns (new_tree, cost). Cost = pre-splay depth+1."""
    first = find_path(t, x)
    cost = len(first)
    cur = t
    while True:
        path = find_path(cur, x)
        if len(path) == 1:
            break
        v = path[-1]
        p = path[-2]
        v_left = v < p
        if len(path) == 2:
            cur = rotate_right(cur, p) if v_left else rotate_left(cur, p)
        else:
            g = path[-3]
            p_left = p < g
            if v_left and p_left:
                cur = rotate_right(cur, g)
                cur = rotate_right(cur, p)
            elif not v_left and not p_left:
                cur = rotate_left(cur, g)
                cur = rotate_left(cur, p)
            elif not v_left and p_left:
                cur = rotate_left(cur, p)
                cur = rotate_right(cur, g)
            else:
                cur = rotate_right(cur, p)
                cur = rotate_left(cur, g)
    return cur, cost


def cost_of(t, x):
    return splay(t, x)[1]


def replay_history_ind(init_a, init_b, actions):
    a = label_inorder(parse_shape(init_a))
    b = label_inorder(parse_shape(init_b))
    for mode_str, key in actions:
        if mode_str == "KEEP":
            a = splay(a, key)[0]
            b = splay(b, key)[0]
        else:
            a = splay(a, key)[0]
    return to_shape(a), to_shape(b)


def evaluate_states_ind(state_shapes, n, h_of, h_den, num_p, den_q):
    """Independent sweep over explicit (A_shape, B_shape) states. h_of(a,b,n)->int."""
    qD = den_q * h_den
    total = 0
    kmax = dmax = None
    karg = darg = None
    for A_shape, B_shape in state_shapes:
        A = label_inorder(parse_shape(A_shape))
        B = label_inorder(parse_shape(B_shape))
        hs = h_of(A, B, n)
        for kk in range(1, n + 1):
            total += 1
            na, ca = splay(A, kk)
            nb, cb = splay(B, kk)
            rk = h_den * (den_q * cb - num_p * ca) + qD * (h_of(na, nb, n) - hs)
            if kmax is None or rk > kmax:
                kmax, karg = rk, [A_shape, B_shape, KEEP, kk]
            total += 1
            rd = qD * (h_of(na, B, n) - hs) - h_den * num_p * ca
            if dmax is None or rd > dmax:
                dmax, darg = rd, [A_shape, B_shape, DELETE, kk]
    return {"edge_count": total, "keep_max": str(kmax), "keep_argmax": karg,
            "delete_max": str(dmax), "delete_argmax": darg}
