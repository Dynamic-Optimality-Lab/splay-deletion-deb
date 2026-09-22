"""One-shot HOLDOUT-H1-v0.1 bank generator (SA-04; pre-synthesis infrastructure).

Generates 20,000 legally reachable states per size for n in {9,10,12,16,24,32}
(120,000 total) from diagonal starts via exact KEEP/DELETE histories using the
frozen WP-1 reference Splay. NO candidate H is involved at any point
(generation reads no H, fits nothing, optimizes nothing).

Fail-closed: refuses to run if any bank file already exists (one-shot; a
re-run needs a new amendment). Deterministic given the secret, which is
generated fresh here via secrets.token_hex and stored ONLY in the
quarantined bank_secret.json (never printed, never preregistered, synthesis-
blocked). Independent assurance runs by parse/verify (replay), never by
regeneration.

Strata (exact per-size counts; proportions frozen in prereg/wp5_sa04.yaml):
  randomized 6000 | spine 2000 | opposite-spine drives 2000 | zigzag 1600 |
  balanced 1400 | comb 1000 | DELETE-heavy 1600 | KEEP-heavy 1600 |
  alternating 1000 | inflated motifs 800 | MIS motifs 600 | mirrors 400.
"""
import hashlib
import json
import os
import random
import secrets
import sys

import zstandard as zstd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

BANK_ID = "HOLDOUT-H1-v0.1"
SIZES = [9, 10, 12, 16, 24, 32]
PER_SIZE = 20000
BANK_DIR = os.path.join(REPO, "artifacts", "wp5", "h1_holdout")

STRATA = [
    ("randomized", 6000, {"modes": (0.5, 0.5), "keys": "uniform", "init": "random"}),
    ("spine", 2000, {"modes": (0.5, 0.5), "keys": "uniform", "init": "spine"}),
    ("opp_spine", 2000, {"modes": (0.5, 0.5), "keys": "uniform", "init": "spine_alt"}),
    ("zigzag", 1600, {"modes": (0.5, 0.5), "keys": "uniform", "init": "zigzag"}),
    ("balanced", 1400, {"modes": (0.5, 0.5), "keys": "uniform", "init": "balanced"}),
    ("comb", 1000, {"modes": (0.5, 0.5), "keys": "uniform", "init": "comb"}),
    ("del_heavy", 1600, {"modes": (0.2, 0.8), "keys": "uniform", "init": "random"}),
    ("keep_heavy", 1600, {"modes": (0.8, 0.2), "keys": "uniform", "init": "random"}),
    ("alternating", 1000, {"modes": "alternating", "keys": "uniform", "init": "random"}),
    ("inflated", 800, {"modes": (0.5, 0.5), "keys": "motif123", "init": "random"}),
    ("mis", 600, {"modes": (0.5, 0.5), "keys": "motif123", "init": "random"}),
    ("mirror", 400, {"modes": "mirror", "keys": "mirror", "init": "mirror"}),
]
assert sum(c for _, c, _ in STRATA) == PER_SIZE

KEEP, DELETE = 0, 1

STRATUM_SPEC = {name: spec for name, _count, spec in STRATA}


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def serialize_skeleton(skel):
    if skel == ():
        return "."
    return "(" + serialize_skeleton(skel[0]) + serialize_skeleton(skel[1]) + ")"


def mirror_skeleton(skel):
    if skel == ():
        return ()
    return (mirror_skeleton(skel[1]), mirror_skeleton(skel[0]))


def spine_skeleton(n, side):
    """All-single-child chain leaning `side` ('L' or 'R'). Skeletons are
    () or (left, right) pairs; a leaning chain nests one side only."""
    skel = ()
    for _ in range(n):
        # (skel, ()) and ((), skel) are (left, right) pairs; outer parens group only.
        skel = ((skel, ()) if side == "L" else ((), skel))
    return skel


def zigzag_skeleton(n):
    """Alternating single-child chain (L,R,L,R... from the root down)."""
    skel = ()
    side = "L"
    chain = []
    for _ in range(n):
        chain.append(side)
        side = "R" if side == "L" else "L"
    for s in reversed(chain):
        skel = ((skel, ()) if s == "L" else ((), skel))
    return skel


def balanced_skeleton(keys):
    """Median-root recursive balanced skeleton over `keys` count."""
    if keys <= 0:
        return ()
    left_n = (keys - 1) // 2
    right_n = keys - 1 - left_n
    return (balanced_skeleton(left_n), balanced_skeleton(right_n))


def comb_skeleton(n):
    """Left-toothed caterpillar: path down the left with single right leaves.

    Node count: root(1) + left subtree. Left subtree X is a node with a left
    leaf and the (n-3) remainder on its right: |X| = 1+1+(n-3) = n-1.
    """
    if n <= 0:
        return ()
    if n == 1:
        return ((), ())
    if n == 2:
        return ((((), ()), ()))
    return ((((((), ()), comb_skeleton(n - 3)))), ())


def random_bst_skeleton(rng, n):
    """BST skeleton from a random permutation (random-insertion model).

    Shape randomness comes from the key permutation only (standard BST
    model; documented non-uniform-Catalan approximation, fit for a
    structurally diverse holdout, not for uniform sampling claims).
    """
    perm = list(range(n))
    rng.shuffle(perm)
    tree = ()
    for rank in perm:
        tree = _bst_insert(tree, rank)
    return _erase(tree)


def _bst_insert(tree, key):
    if tree == ():
        return ((), key, ())
    l, k, r = tree
    if key < k:
        return (_bst_insert(l, key), k, r)
    return (l, k, _bst_insert(r, key))


def _erase(tree):
    if tree == ():
        return ()
    return (_erase(tree[0]), _erase(tree[2]))


def mirror_key(key, n):
    return n + 1 - key


def run_history(ref_splay, init_a, init_b, actions):
    """Replay actions from (init_a, init_b); returns (end_a, end_b)."""
    a, b = init_a, init_b
    for mode, key in actions:
        if mode == KEEP:
            a = ref_splay(a, key)[0]
            b = ref_splay(b, key)[0]
        else:
            a = ref_splay(a, key)[0]
    return a, b


def main():
    from python.reference import tree as ref_tree
    from python.reference import splay as ref_splay
    from python.reference import enumerate as ref_enum
    if os.path.exists(os.path.join(BANK_DIR, "bank_manifest.json")):
        raise SystemExit("GENERATION REFUSED: bank already frozen (re-run needs a new amendment)")
    os.makedirs(BANK_DIR, exist_ok=True)
    secret = secrets.token_hex(32)
    rng = random.Random(secret)
    console_log("H1-GEN-01", "secret generated (quarantined, never printed)")
    manifest_sizes = {}
    commitment_parts = []
    for n in SIZES:
        console_log("H1-GEN-02", "generating n=%d" % n)
        seen = set()
        records = []
        fallbacks = 0
        need = {name: count for name, count, _ in STRATA}
        have = {name: 0 for name, _, _ in STRATA}
        # Mirror stratum draws bases from the randomized stream.
        rand_bases = []
        guard = 0
        while any(have[k] < need[k] for k in need) and guard < 2000000:
            guard += 1
            # Pick first unfilled stratum in frozen order (deterministic).
            stratum = next(k for k in need if have[k] < need[k])
            spec = STRATUM_SPEC[stratum]
            if stratum == "mirror":
                if not rand_bases:
                    continue
                base = rand_bases[rng.randrange(len(rand_bases))]
                init_shape = mirror_skeleton(ref_tree.parse_shape(base["init_shape"]))
                init_str = serialize_skeleton(init_shape)
                actions = [(m, mirror_key(k, n)) for m, k in base["actions"]]
                end_a = mirror_skeleton(ref_tree.parse_shape(base["end_A_shape"]))
                end_b = mirror_skeleton(ref_tree.parse_shape(base["end_B_shape"]))
                end_a_s, end_b_s = serialize_skeleton(end_a), serialize_skeleton(end_b)
                rec = {"init_A_shape": init_str, "init_B_shape": init_str,
                       "actions": [["DELETE" if m == DELETE else "KEEP", k] for m, k in actions],
                       "end_A_shape": end_a_s, "end_B_shape": end_b_s,
                       "stratum": stratum, "history_length": len(actions)}
            else:
                init_kind = spec["init"]
                if init_kind == "random":
                    skel = random_bst_skeleton(rng, n)
                elif init_kind == "spine":
                    skel = spine_skeleton(n, "L" if rng.random() < 0.5 else "R")
                elif init_kind == "spine_alt":
                    skel = spine_skeleton(n, "R" if rng.random() < 0.5 else "L")
                elif init_kind == "zigzag":
                    skel = zigzag_skeleton(n)
                elif init_kind == "balanced":
                    skel = balanced_skeleton(n)
                elif init_kind == "comb":
                    skel = comb_skeleton(n)
                else:
                    raise AssertionError("unknown init")
                init_str = serialize_skeleton(skel)
                t0 = ref_tree.assign_inorder_keys(ref_tree.parse_shape(init_str))
                hlen = rng.randint(1, 2 * n)
                actions = []
                for step in range(hlen):
                    mb = spec["modes"]
                    if mb == "alternating":
                        m = KEEP if step % 2 == 0 else DELETE
                    else:
                        m = KEEP if rng.random() < mb[0] else DELETE
                    kb = spec["keys"]
                    if kb == "uniform":
                        k = rng.randint(1, n)
                    else:  # motif123: cycle through keys 1,2,3 (critical-cycle locality motif)
                        k = (step % 3) + 1
                    actions.append((m, k))
                a, b = run_history(lambda t, x: ref_splay.splay(t, x), t0, t0, actions)
                end_a_s = ref_enum.keyed_to_shape(a)
                end_b_s = ref_enum.keyed_to_shape(b)
                rec = {"init_A_shape": init_str, "init_B_shape": init_str,
                       "actions": [["DELETE" if m == DELETE else "KEEP", k] for m, k in actions],
                       "end_A_shape": end_a_s, "end_B_shape": end_b_s,
                       "stratum": stratum, "history_length": hlen}
                if stratum == "randomized":
                    rand_bases.append({"init_shape": init_str, "actions": actions,
                                       "end_A_shape": end_a_s, "end_B_shape": end_b_s})
            key = (rec["end_A_shape"], rec["end_B_shape"])
            if key in seen:
                fallbacks += 1
                continue
            # Fail-closed replay check at generation time (independent of later audits).
            ta = ref_tree.assign_inorder_keys(ref_tree.parse_shape(rec["init_A_shape"]))
            ea, eb = run_history(lambda t, x: ref_splay.splay(t, x), ta, ta,
                                 [(DELETE if m == "DELETE" else KEEP, k) for m, k in rec["actions"]])
            assert ref_enum.keyed_to_shape(ea) == rec["end_A_shape"]
            assert ref_enum.keyed_to_shape(eb) == rec["end_B_shape"]
            seen.add(key)
            records.append(rec)
            have[stratum] += 1
        unfilled = {k: (need[k], have[k]) for k in need if have[k] < need[k]}
        if unfilled:
            raise SystemExit("STRATUM SHORTFALL at n=%d: %s" % (n, unfilled))
        records.sort(key=lambda r: (r["end_A_shape"], r["end_B_shape"], r["stratum"],
                                    json.dumps(r["actions"])))
        blob = (json.dumps({"bank_id": BANK_ID, "n": n, "states": records},
                           sort_keys=True) + "\n").encode("utf-8")
        os.makedirs(os.path.join(BANK_DIR, "n%d" % n), exist_ok=True)
        with open(os.path.join(BANK_DIR, "n%d" % n, "bank.json.zst"), "wb") as f:
            f.write(zstd.ZstdCompressor(level=19).compress(blob))
        logical = hashlib.sha256(blob).hexdigest()
        commitment_parts.append(blob)
        manifest_sizes[str(n)] = {"states": len(records), "strata": dict(have),
                                  "fallbacks": fallbacks, "logical_sha256": logical}
        console_log("H1-GEN-03", "n=%d states=%d fallbacks=%d sha=%s" % (
            n, len(records), fallbacks, logical[:16]))
    import hashlib as _hl
    commitment = _hl.sha256(b"".join(commitment_parts)).hexdigest()
    manifest = {"bank_id": BANK_ID, "sizes": SIZES, "states_per_size": PER_SIZE,
                "total_states": 120000, "future_edge_evaluations_exact": 4120000,
                "serialization": "sorted-keys newline JSON (.zst transport)",
                "strata_proportions": "prereg/wp5_sa04.yaml holdout_bank.strata_per_size_counts",
                "per_size": manifest_sizes, "bank_commitment_sha256": commitment,
                "secret_ref": "bank_secret.json (quarantined, never printed, never preregistered)"}
    with open(os.path.join(BANK_DIR, "bank_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, sort_keys=True, indent=2)
        f.write("\n")
    with open(os.path.join(BANK_DIR, "bank_secret.json"), "w", encoding="utf-8") as f:
        json.dump({"secret_hex": secret}, f, sort_keys=True)
        f.write("\n")
    console_log("H1-GEN-99", "bank frozen commitment=%s" % commitment[:16])
    return commitment


if __name__ == "__main__":
    main()
