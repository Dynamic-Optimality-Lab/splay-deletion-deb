"""Stratify the minimum obstruction witness (regimes, SCCs, cost splits).

Joins MIS rows with cycle-anatomy rotation signatures / SCC ids where the
edge lies on a canonical cycle; otherwise computes the A-side rotation
signature via the frozen reference Splay (state-only, same pattern as
build_datasets.is_zigzag_row). Appends a 'stratification' block to
artifacts/hypotheses/mis_n456.json (own new artifact, not sealed).
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining import holdout_firewall as firewall


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def anatomy_index(n):
    firewall.guard_load("artifacts/critical/n%d/canonical_cycles.json" % n)
    recs = json.load(open(os.path.join(
        REPO, "artifacts", "cycle_anatomy", "n%d" % n, "cycle_anatomy.json"), encoding="utf-8"))
    idx = {}
    for r in recs:
        idx[(r["source_state_id"], r["mode"], r["key"])] = r
    return idx


def zig_family(sig):
    s = list(sig)
    if s == ["ZIG"]:
        return "ZIG"
    if s in (["LL"], ["RR"]):
        return "LL/RR"
    if any(x in ("LR", "RL") for x in s):
        return "LR/RL"
    return "MULTI:" + ",".join(s)


def main():
    firewall.hydrate_from_files()
    firewall.guard_load("artifacts/features/n7/edge_deltas.json.zst")
    from python.reference import tree as ref_tree
    from python.reference import splay as ref_splay
    from python.reference import enumerate as ref_enum
    shapes_cache = {}
    p = os.path.join(REPO, "artifacts", "hypotheses", "mis_n456.json")
    mis = json.load(open(p, encoding="utf-8"))
    anat_cache = {}
    enriched = []
    for r in mis["rows"]:
        n = r["n"]
        if n not in anat_cache:
            anat_cache[n] = anatomy_index(n)
        if n not in shapes_cache:
            shapes_cache[n] = ref_enum.canonical_shapes(n)
        key = (r["source_state_id"], r["mode"], r["key"])
        rec = anat_cache[n].get(key)
        if rec is not None:
            a_sig = rec["A_rotation_signature"]
            scc = rec["scc_id"]
            cyc = rec["cycle_id"]
            src = "canonical-anatomy"
        else:
            # State-only recompute of the A-side signature (frozen Splay).
            from python.reference import pair_graph as ref_pg
            tables = ref_pg.build_tables(n)
            reach = ref_pg.build_reachability(tables)
            tc = len(shapes_cache[n])
            a_id = r["source_state_id"] // tc
            t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shapes_cache[n][a_id]))
            _t2, _c, cases, _p = ref_splay.splay(t, r["key"])
            a_sig = list(cases)
            scc = None
            cyc = None
            src = "recomputed-A-side-only"
        enriched.append(dict(r, A_rotation_signature=a_sig,
                             zig_family=zig_family(a_sig),
                             scc_id=scc, cycle_id=cyc, rotation_source=src))
    # Regime summary.
    import collections
    by_n = collections.Counter(r["n"] for r in enriched)
    by_mode = collections.Counter(r["mode"] for r in enriched)
    by_zig = collections.Counter(r["zig_family"] for r in enriched)
    by_cost = collections.Counter((r["a"], r["y"]) for r in enriched)
    mis["stratified_rows"] = enriched
    mis["stratification"] = {
        "by_n": dict(by_n),
        "by_mode": dict(by_mode),
        "by_zig_family_A_side": dict(by_zig),
        "by_cost_a_y": {"%d,%d" % k: v for k, v in by_cost.items()},
        "requires_n7": any(r["n"] == 7 for r in enriched),
        "keep_only": all(r["mode"] == "KEEP" for r in enriched),
        "scc_ids": sorted(set(r["scc_id"] for r in enriched if r["scc_id"] is not None)),
    }
    json.dump(mis, open(p, "w", encoding="utf-8"), sort_keys=True, indent=2)
    open(p, "a", encoding="utf-8").write("\n")
    console_log("MIS-STRAT", "by_n=%s by_zig=%s requires_n7=%s" % (
        dict(by_n), dict(by_zig), mis["stratification"]["requires_n7"]))
    for r in enriched:
        console_log("MIS-ROW", "n=%d %s k=%d %s a=%d y=%d L=%s scc=%s" % (
            r["n"], r["mode"], r["key"], r["zig_family"], r["a"], r["y"],
            r["scaled_slack"], r["scc_id"]))


if __name__ == "__main__":
    main()
