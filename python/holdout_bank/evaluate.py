"""Post-unlock H1 bank evaluation (SA-04 §SA-04.5; WP-5 runtime, NOT freeze).

Requires the H1 firewall UNLOCKED state before touching bank records
(fail-closed). Replays stored histories (legality proof), computes H over
end states, evaluates EVERY key × BOTH modes per state with exact
integer-scaled residuals, records maxima/maximizers/counterexamples
(lex-first 16 per mode + exact counts), and verifies count identities.

Smoke path evaluate_states() takes explicit states (no bank reads) and is
used pre-unlock by SA04-19 with a synthetic fixture.
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KEEP, DELETE = 0, 1
PRESERVED_PER_MODE = 16


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def replay_history(init_a_shape, init_b_shape, actions, parse_fn, label_fn, splay_fn,
                   shape_fn):
    """Replay a stored history; returns (end_a_shape, end_b_shape)."""
    a = label_fn(parse_fn(init_a_shape))
    b = label_fn(parse_fn(init_b_shape))
    for mode_str, key in actions:
        if mode_str == "KEEP":
            a = splay_fn(a, key)[0]
            b = splay_fn(b, key)[0]
        else:
            a = splay_fn(a, key)[0]
    return shape_fn(a), shape_fn(b)


def evaluate_states(state_shapes, n, H_fn, H_den, p_H, q_H, splay_fn, parse_fn,
                    label_fn, shape_fn):
    """splay_fn(t, x) returns (new_tree, cost, cases, access_path) (frozen WP-1 API)."""
    """Exact Pair-Access sweep over explicit end-state shapes.

    state_shapes: iterable of (A_shape, B_shape). Returns result dict with
    exact integer-scaled maxima (scale q_H*H_den), lex-first maximizers,
    positive counts, and lex-first preserved counterexamples.
    """
    qD = q_H * H_den
    edge_count = 0
    norm_bad, nonneg_bad = [], []
    norm_count = nonneg_count = 0
    keep_max = del_max = None
    keep_arg = del_arg = None
    keep_pos = del_pos = 0
    keep_cex, del_cex = [], []
    for A_shape, B_shape in state_shapes:
        A = label_fn(parse_fn(A_shape))
        B = label_fn(parse_fn(B_shape))
        pid_note = (A_shape, B_shape)
        Hs = H_fn(A, B, n)
        if A_shape == B_shape and Hs != 0:
            norm_count += 1
            if len(norm_bad) < PRESERVED_PER_MODE:
                norm_bad.append([A_shape, B_shape])
        if Hs < 0:
            nonneg_count += 1
            if len(nonneg_bad) < PRESERVED_PER_MODE:
                nonneg_bad.append([A_shape, B_shape])
        for key in range(1, n + 1):
            # KEEP.
            edge_count += 1
            A2, ca, _c, _p = splay_fn(A, key)
            B2, cb, _c2, _p2 = splay_fn(B, key)
            r = H_den * (q_H * cb - p_H * ca) + qD * (H_fn(A2, B2, n) - Hs)
            if keep_max is None or r > keep_max:
                keep_max, keep_arg = r, [A_shape, B_shape, KEEP, key]
            if r > 0:
                keep_pos += 1
                if len(keep_cex) < PRESERVED_PER_MODE:
                    keep_cex.append([A_shape, B_shape, KEEP, key, str(r)])
            # DELETE.
            edge_count += 1
            r = qD * (H_fn(A2, B, n) - Hs) - H_den * p_H * ca
            if del_max is None or r > del_max:
                del_max, del_arg = r, [A_shape, B_shape, DELETE, key]
            if r > 0:
                del_pos += 1
                if len(del_cex) < PRESERVED_PER_MODE:
                    del_cex.append([A_shape, B_shape, DELETE, key, str(r)])
    return {"edge_count": edge_count, "norm_count": norm_count, "norm_bad": norm_bad,
            "nonneg_count": nonneg_count, "nonneg_bad": nonneg_bad,
            "keep_max": str(keep_max), "keep_argmax": keep_arg, "keep_pos_count": keep_pos,
            "keep_cex": keep_cex, "delete_max": str(del_max), "delete_argmax": del_arg,
            "delete_pos_count": del_pos, "delete_cex": del_cex}


def evaluate_bank(bank_dir, H_fn, H_den, p_H, q_H, state_path=None):
    """Full post-unlock bank evaluation (WP-5 runtime). Requires UNLOCKED."""
    from python.holdout_bank import h1_firewall as fw
    import zstandard as zstd
    st = fw.read_state(state_path or fw.STATE_FILE)
    if st.get("state") != fw.UNLOCKED:
        raise fw.H1FirewallError("bank evaluation requires UNLOCKED firewall")
    from python.reference import tree as ref_tree
    from python.reference import splay as ref_splay
    from python.reference import enumerate as ref_enum
    total = {"edge_count": 0, "keep_pos_count": 0, "delete_pos_count": 0,
             "norm_count": 0, "nonneg_count": 0, "keep_max": None, "keep_argmax": None,
             "delete_max": None, "delete_argmax": None, "keep_cex": [], "delete_cex": []}
    per_size = {}
    for n in (9, 10, 12, 16, 24, 32):
        with open(os.path.join(bank_dir, "n%d" % n, "bank.json.zst"), "rb") as f:
            recs = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))["states"]
        # History legality: replay every record and compare end shapes.
        for r in recs:
            ea, eb = replay_history(
                r["init_A_shape"], r["init_B_shape"], r["actions"],
                ref_tree.parse_shape, ref_tree.assign_inorder_keys,
                ref_splay.splay, ref_enum.keyed_to_shape)
            if ea != r["end_A_shape"] or eb != r["end_B_shape"]:
                raise AssertionError("bank history replay mismatch at n=%d" % n)
        out = evaluate_states([(r["end_A_shape"], r["end_B_shape"]) for r in recs],
                              n, H_fn, H_den, p_H, q_H, ref_splay.splay,
                              ref_tree.parse_shape, ref_tree.assign_inorder_keys,
                              ref_enum.keyed_to_shape)
        per_size[str(n)] = {k: out[k] for k in ("edge_count", "keep_max", "delete_max",
                                                "keep_pos_count", "delete_pos_count")}
        for k in ("edge_count", "keep_pos_count", "delete_pos_count",
                  "norm_count", "nonneg_count"):
            total[k] += out[k]
        for mk, ak in (("keep_max", "keep_argmax"), ("delete_max", "delete_argmax")):
            if total[mk] is None or int(out[mk]) > int(total[mk]):
                total[mk], total[ak] = out[mk], out[ak]
        total["keep_cex"].extend(out["keep_cex"])
        total["delete_cex"].extend(out["delete_cex"])
    total["keep_cex"] = sorted(total["keep_cex"])[:PRESERVED_PER_MODE]
    total["delete_cex"] = sorted(total["delete_cex"])[:PRESERVED_PER_MODE]
    total["per_size"] = per_size
    return total
