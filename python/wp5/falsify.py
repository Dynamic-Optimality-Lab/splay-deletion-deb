"""Development exhaustive falsifier (WP-5 synthesis side, revealed n<=7 only).

For each frozen candidate: H over every R_n state (n=2..7), UH-1 diagonal
zeros, UH-2 nonnegativity, exact KEEP/DELETE residuals with maxima +
lexicographically-first maximizers + preserved counterexamples, OG-2/OG-3
diagnostic material, mirror-invariance discovery probe, and an
out-of-domain panel on unreachable pairs (labeled, never decisive).

Exact integer-scaled residuals (scale q_H); no floats anywhere. Never reads
detailed n8 records or hidden-bank records (static audit + firewall-state
assertions enforced at entry).
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from python.wp5 import structural as S

# console.log equivalent [WP5-FAL-01]: falsifier module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


FALS_DIR = os.path.join(REPO, "artifacts", "falsification")
PRESERVED_PER_MODE = 16


def load_domain_tables(n):
    """Sealed single-tree transitions + reachability pair list + shapes."""
    # console.log equivalent [WP5-FAL-04]: domain tables loaded.
    console_log("WP5-FAL-04", "loading sealed domain n=%d" % n)
    import zstandard as zstd
    sys.path.insert(0, REPO)
    from python.reference import enumerate as E
    shapes = E.canonical_shapes(n)
    count = len(shapes)
    with open(os.path.join(REPO, "artifacts", "transitions", "n%d" % n,
                           "forward.bin.zst"), "rb") as handle:
        fwd = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    after = [[0] * count for _ in range(n + 1)]
    cost = [[0] * count for _ in range(n + 1)]
    for record in fwd["records"]:
        after[int(record["x"])][int(record["tree"])] = int(record["after"])
        cost[int(record["x"])][int(record["tree"])] = int(record["cost"])
    with open(os.path.join(REPO, "artifacts", "reachability", "n%d" % n,
                           "reachable.json.zst"), "rb") as handle:
        reach = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    pair_ids = sorted(int(p) for p in reach["pair_ids"])
    assert all(0 <= p < count * count for p in pair_ids)
    return shapes, count, after, cost, pair_ids


def build_h_table(hypothesis_id, n, shapes, count, pair_ids):
    """Exact H over R_n (memoized per-tree structural info)."""
    # console.log equivalent [WP5-FAL-05]: H-table built.
    console_log("WP5-FAL-05", "H-table %s n=%d (%d states)" % (hypothesis_id, n, len(pair_ids)))
    sys.path.insert(0, REPO)
    from python.reference import tree as T
    formula_fn, _cls, _text = S.H_REGISTRY[hypothesis_id]
    tree_info = [None] * count
    for tree_id, shape in enumerate(shapes):
        tree_info[tree_id] = S.tree_info(
            T.assign_inorder_keys(T.parse_shape(shape)))
    table = {}
    for pid in pair_ids:
        table[pid] = formula_fn(tree_info[pid // count], tree_info[pid % count], n)
    return table


def sweep_candidate(hypothesis_id, n, shapes, count, after, cost, pair_ids, h_table,
                    p_h, q_h):
    """Exact M_K/M_D sweep with maxima, first maximizers, counterexamples.

    Preserved counterexamples carry the full WorkPlan artifact payload:
    [pair_id, mode, key, a, y, h_before, h_after, residual_num, residual_den,
    A_shape, B_shape, succ_A_shape, succ_B_shape_or_null, formula_id].
    Residuals are exact integers at scale q_H (den = q_H).
    """
    # console.log equivalent [WP5-FAL-06]: residual sweep executed.
    console_log("WP5-FAL-06", "sweep %s n=%d" % (hypothesis_id, n))
    from python.wp5 import candidates as C
    formula_id = C.FORMULA_IDS[hypothesis_id]
    keep_max = None
    keep_arg = None
    keep_pos = 0
    keep_cex = []
    delete_max = None
    delete_arg = None
    delete_pos = 0
    delete_cex = []
    uh1_bad = []
    uh2_bad = []
    for pid in pair_ids:
        h_state = h_table[pid]
        a_id = pid // count
        b_id = pid % count
        if a_id == b_id and h_state != 0:
            uh1_bad.append(pid)
        if h_state < 0:
            uh2_bad.append(pid)
        for key in range(1, n + 1):
            a2 = after[key][a_id]
            ca = cost[key][a_id]
            # KEEP branch (forward-closure: successor must be tabled).
            b2 = after[key][b_id]
            cb = cost[key][b_id]
            succ = a2 * count + b2
            assert succ in h_table, "R_n forward-closure violated at n=%d" % n
            residual = q_h * cb + q_h * (h_table[succ] - h_state) - p_h * ca
            if keep_max is None or residual > keep_max:
                keep_max = residual
                keep_arg = [pid, 0, key]
            if residual > 0:
                keep_pos += 1
                if len(keep_cex) < PRESERVED_PER_MODE:
                    keep_cex.append([pid, 0, key, ca, cb, h_state,
                                     h_table[succ], str(residual), str(q_h),
                                     shapes[a_id], shapes[b_id],
                                     shapes[a2], shapes[b2], formula_id])
            # DELETE branch (y = 0, B frozen).
            t2 = a2 * count + b_id
            assert t2 in h_table, "R_n forward-closure violated at n=%d" % n
            residual = q_h * (h_table[t2] - h_state) - p_h * ca
            if delete_max is None or residual > delete_max:
                delete_max = residual
                delete_arg = [pid, 1, key]
            if residual > 0:
                delete_pos += 1
                if len(delete_cex) < PRESERVED_PER_MODE:
                    delete_cex.append([pid, 1, key, ca, 0, h_state,
                                       h_table[t2], str(residual), str(q_h),
                                       shapes[a_id], shapes[b_id],
                                       shapes[a2], shapes[b_id], formula_id])
    return {"n": n, "states": len(pair_ids),
            "uh1_violations": uh1_bad[:PRESERVED_PER_MODE],
            "uh1_count": len(uh1_bad),
            "uh2_violations": uh2_bad[:PRESERVED_PER_MODE],
            "uh2_count": len(uh2_bad),
            "keep_max": str(keep_max), "keep_argmax": keep_arg,
            "keep_pos_count": keep_pos, "keep_cex": keep_cex,
            "delete_max": str(delete_max), "delete_argmax": delete_arg,
            "delete_pos_count": delete_pos, "delete_cex": delete_cex}


def out_of_domain_panel(hypothesis_id, n, shapes, count, after, cost, h_table, p_h, q_h):
    """Unreachable-pair panel (OUT_OF_DOMAIN_NOT_LOGICALLY_REQUIRED)."""
    # console.log equivalent [WP5-FAL-07]: out-of-domain panel evaluated.
    console_log("WP5-FAL-07", "out-of-domain panel %s n=%d" % (hypothesis_id, n))
    sys.path.insert(0, REPO)
    from python.reference import tree as T
    with open(os.path.join(REPO, "artifacts", "reachability", "n%d" % n,
                           "reachable.json.zst"), "rb") as handle:
        import zstandard as zstd
        reachable = set(int(p) for p in json.loads(
            zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))["pair_ids"])
    formula_fn, _cls, _text = S.H_REGISTRY[hypothesis_id]
    tree_info = [None] * count
    for tree_id, shape in enumerate(shapes):
        tree_info[tree_id] = S.tree_info(
            T.assign_inorder_keys(T.parse_shape(shape)))
    worst = None
    worst_at = None
    checked = 0
    for pid in range(count * count):
        if pid in reachable:
            continue
        checked += 1
        h_state = formula_fn(tree_info[pid // count], tree_info[pid % count], n)
        for key in range(1, n + 1):
            a2 = after[key][pid // count]
            ca = cost[key][pid // count]
            b2 = after[key][pid % count]
            cb = cost[key][pid % count]
            t2 = a2 * count + b2
            ht2 = formula_fn(tree_info[t2 // count], tree_info[t2 % count], n)
            residual = q_h * cb + q_h * (ht2 - h_state) - p_h * ca
            if worst is None or residual > worst:
                worst = residual
                worst_at = [pid, 0, key]
    return {"n": n, "unreachable_states": checked, "keep_worst": str(worst),
            "keep_worst_at": worst_at,
            "label": "OUT_OF_DOMAIN_NOT_LOGICALLY_REQUIRED"}


def mirror_probe(hypothesis_id, n, shapes, count, pair_ids):
    """Symmetry discovery probe (recorded, never a gate)."""
    # console.log equivalent [WP5-FAL-08]: mirror probe recorded.
    console_log("WP5-FAL-08", "mirror probe %s n=%d" % (hypothesis_id, n))
    import random
    sys.path.insert(0, REPO)
    from python.reference import tree as T
    formula_fn, _cls, _text = S.H_REGISTRY[hypothesis_id]
    rng = random.Random(1000 + n)
    sample = [pair_ids[rng.randrange(len(pair_ids))] for _ in range(min(200, len(pair_ids)))]
    checked = 0
    mismatches = 0
    for pid in sample:
        a_id = pid // count
        b_id = pid % count
        keyed_a = T.assign_inorder_keys(T.parse_shape(shapes[a_id]))
        keyed_b = T.assign_inorder_keys(T.parse_shape(shapes[b_id]))
        mirrored_a = _mirror_keyed(keyed_a, n)
        mirrored_b = _mirror_keyed(keyed_b, n)
        before = formula_fn(S.tree_info(keyed_a), S.tree_info(keyed_b), n)
        after = formula_fn(S.tree_info(mirrored_a), S.tree_info(mirrored_b), n)
        checked += 1
        if before != after:
            mismatches += 1
    return {"n": n, "checked": checked, "mismatches": mismatches,
            "note": "discovery only (symmetry not required)"}


def _mirror_keyed(keyed, n):
    if keyed == ():
        return ()
    left, key, right = keyed
    return (_mirror_keyed(right, n), n + 1 - key, _mirror_keyed(left, n))


def og2_og3_material(hypothesis_id, n, h_table):
    """OG-2 sandwich counts + OG-3 corridor values from sealed tables (diagnostic)."""
    # console.log equivalent [WP5-FAL-09]: OG-2/OG-3 material recorded.
    console_log("WP5-FAL-09", "OG material %s n=%d" % (hypothesis_id, n))
    import zstandard as zstd
    with open(os.path.join(REPO, "artifacts", "potentials", "n%d" % n,
                           "V.json.zst"), "rb") as handle:
        rows_v = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    with open(os.path.join(REPO, "artifacts", "potentials", "n%d" % n,
                           "U.json.zst"), "rb") as handle:
        rows_u = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    table_v = {int(r["pair_id"]): int(r["V_scaled"]) for r in rows_v}
    table_u = {int(r["pair_id"]): int(r["U_scaled"]) for r in rows_u}
    below = sum(1 for pid, h in h_table.items() if h < table_v[pid])
    above = sum(1 for pid, h in h_table.items() if h > table_u[pid])
    # OG-3: H values along sealed canonical paths/cycles (explanation only).
    import glob
    corridors = []
    for cand in sorted(glob.glob(os.path.join(
            REPO, "artifacts", "critical", "n%d" % n, "canonical_paths.json"))):
        with open(cand, encoding="utf-8") as handle:
            paths = json.load(handle)
        for pid_str in sorted(paths, key=int):
            edges = paths[pid_str].get("edges", [])
            states = []
            for edge in edges:
                states.append(edge["source"])
            if edges:
                states.append(edges[-1]["target"])
            corridors.append({"path_to": int(pid_str), "length": paths[pid_str].get("length"),
                              "H_along_states": [h_table.get(s) for s in states]})
    cycles = []
    for cand in sorted(glob.glob(os.path.join(
            REPO, "artifacts", "critical", "n%d" % n, "canonical_cycles.json"))):
        with open(cand, encoding="utf-8") as handle:
            for entry in json.load(handle)[:4]:
                edges = entry.get("canonical_cycle", {}).get("edges", entry.get("edges", []))
                states = [e["source"] for e in edges]
                cycles.append({"scc_id": entry.get("scc_id"),
                               "H_along_states": [h_table.get(s) for s in states]})
    return {"n": n, "states_below_V": below, "states_above_U": above,
            "H_range": [min(h_table.values()), max(h_table.values())],
            "corridor_H": corridors, "cycle_H": cycles,
            "note": "diagnostic only (b_n* geometry vs universal candidate)"}
