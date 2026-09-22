"""Independent UH-4 sandwich check (clean-room side, WP-5 compliance repair).

Reimplements NOTHING from candidate-synthesis code: uses only this package's
own keyed-tree building, H-from-math-text evaluation, and the sealed tree /
transition / reachability records, plus the independently-verified b=2
canonical U_2/V_2 tables. Compares V_2(s) <= H(s) <= U_2(s) exactly over
every reachable state in ascending pair order.

Allowed imports: stdlib + zstandard + this package (python.wp5_independent).
"""
import json
import os

from python.wp5_independent import independent as I


# console.log equivalent [WP5-UH4-17]: independent UH-4 module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def load_uv2(n, repo_root):
    """Load independently-verified U_2/V_2 tables (exact ints)."""
    import zstandard as zstd
    base = os.path.join(repo_root, "artifacts", "potentials", "n%d" % n, "hypothesis_bH")
    with open(os.path.join(base, "bH_geometry.v1.json"), encoding="utf-8") as handle:
        companion = json.load(handle)
    if companion.get("b_H") != {"p": "2", "q": "1"}:
        raise AssertionError("independent UH-4 refuses non-b=2 geometry")
    with open(os.path.join(base, "U.json.zst"), "rb") as handle:
        u_rows = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    with open(os.path.join(base, "V.json.zst"), "rb") as handle:
        v_rows = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    return ({r["pair_id"]: int(r["U_scaled"]) for r in u_rows},
            {r["pair_id"]: int(r["V_scaled"]) for r in v_rows})


def independent_uh4(hypothesis_id, formula_id, n, repo_root):
    """Independent UH-4 matrix for one candidate/size. Exact integers only."""
    # console.log equivalent [WP5-UH4-18]: independent UH-4 evaluation per H/n.
    console_log("WP5-UH4-18", "independent UH-4 %s n=%d" % (hypothesis_id, n))
    keyed, _after, _cost, pair_ids = I.load_sealed_universe(n, repo_root)
    count = len(keyed)
    memos = {tree_id: I.tree_memo(tree) for tree_id, tree in keyed.items()}
    U, V = load_uv2(n, repo_root)
    assert set(U) == set(pair_ids) and set(V) == set(pair_ids)
    lower = 0
    upper = 0
    max_lower_margin = 0
    max_upper_margin = 0
    first = None
    for pid in pair_ids:
        a_id = pid // count
        b_id = pid % count
        h = I.h_from_math_text(formula_id, keyed[a_id], keyed[b_id], n,
                               memo_a=memos[a_id], memo_b=memos[b_id])
        u = U[pid]
        v = V[pid]
        if h < v:
            lower += 1
            margin = v - h
            if margin > max_lower_margin:
                max_lower_margin = margin
            if first is None:
                first = {"pair_id": pid, "kind": "LOWER", "H": h,
                         "U_2": u, "V_2": v, "signed_diff": h - v}
        if h > u:
            upper += 1
            margin = h - u
            if margin > max_upper_margin:
                max_upper_margin = margin
            if first is None:
                first = {"pair_id": pid, "kind": "UPPER", "H": h,
                         "U_2": u, "V_2": v, "signed_diff": h - u}
    status = "PASS" if (lower == 0 and upper == 0) else "FAIL"
    return {"hypothesis_id": hypothesis_id, "n": n, "states_checked": len(pair_ids),
            "lower_violations": lower, "upper_violations": upper,
            "max_lower_margin": max_lower_margin,
            "max_upper_margin": max_upper_margin,
            "first_violation": first, "status": status}
