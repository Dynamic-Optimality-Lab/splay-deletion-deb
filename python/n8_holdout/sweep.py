"""Primary exact n=8 Pair-Access sweep (SA-03 §SA-03.3/8; general in n).

Loads sealed transition tables + reachable pair list, evaluates a frozen
(H, b_H) candidate with exact integer-scaled residuals:

  q_H*D*E_K = D*(q_H*c(B,x) - p_H*c(A,x)) + D*q_H*(H2-H1)
  q_H*D*E_D = D*q_H*(H2-H1) - D*p_H*c(A,x)

H_fn(pid) returns an exact int; H_den=D pre-scales rational potentials
(recorded in the freeze manifest; D=1 for integer potentials and for the
H=0 machinery test vector). Deterministic ascending-pid order, edge order
KEEP(1..n) then DELETE(1..n); lexicographically first maximizers.
Supports deterministic sharding with exact reduction (combine_partials).
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KEEP, DELETE = 0, 1
EDGE_MODES = ((KEEP, "KEEP"), (DELETE, "DELETE"))
MAX_PRESERVED_CEX_PER_MODE = 16


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def load_domain(tables_dir, reach_dir):
    """Returns (n, C_n, pair_ids ascending, after[x][tree], cost[x][tree])."""
    import zstandard as zstd
    with open(os.path.join(tables_dir, "forward.bin.zst"), "rb") as f:
        fwd = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    n = int(fwd["n"])
    ntrees = 0
    for r in fwd["records"]:
        if r["tree"] + 1 > ntrees:
            ntrees = r["tree"] + 1
    after = [[0] * ntrees for _ in range(n + 1)]
    cost = [[0] * ntrees for _ in range(n + 1)]
    for r in fwd["records"]:
        after[int(r["x"])][int(r["tree"])] = int(r["after"])
        cost[int(r["x"])][int(r["tree"])] = int(r["cost"])
    with open(os.path.join(reach_dir, "reachable.json.zst"), "rb") as f:
        reach = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    pair_ids = [int(p) for p in reach["pair_ids"]]
    if pair_ids != sorted(pair_ids):
        raise AssertionError("pair_ids not ascending (determinism requires sort)")
    return n, ntrees, pair_ids, after, cost


def sweep_shard(pair_ids, ntrees, n, after, cost, H_fn, H_den, p_H, q_H):
    """Exact sweep over a pid subsequence. Returns partial result dict."""
    qD = q_H * H_den
    edge_count = 0
    norm_bad = []
    nonneg_bad = []
    keep_max = None
    keep_arg = None
    keep_pos = 0
    keep_cex = []
    del_max = None
    del_arg = None
    del_pos = 0
    del_cex = []
    C = ntrees
    for pid in pair_ids:
        A_id = pid // C
        B_id = pid - A_id * C
        Hs = H_fn(pid)
        for mode, _mname in EDGE_MODES:
            for key in range(1, n + 1):
                edge_count += 1
                a2 = after[key][A_id]
                ca = cost[key][A_id]
                if mode == KEEP:
                    b2 = after[key][B_id]
                    cb = cost[key][B_id]
                    t2 = a2 * C + b2
                    r = H_den * (q_H * cb - p_H * ca) + qD * (H_fn(t2) - Hs)
                    if keep_max is None or r > keep_max:
                        keep_max = r
                        keep_arg = [pid, mode, key]
                    if r > 0:
                        keep_pos += 1
                        if len(keep_cex) < MAX_PRESERVED_CEX_PER_MODE:
                            keep_cex.append([pid, mode, key, str(r)])
                else:
                    t2 = a2 * C + B_id
                    r = qD * (H_fn(t2) - Hs) - H_den * p_H * ca
                    if del_max is None or r > del_max:
                        del_max = r
                        del_arg = [pid, mode, key]
                    if r > 0:
                        del_pos += 1
                        if len(del_cex) < MAX_PRESERVED_CEX_PER_MODE:
                            del_cex.append([pid, mode, key, str(r)])
    # Exact diagonal/nonnegativity totals are computed in finalize_counts
    # (separate cheap pass without transitions); lists here stay truncated.
    return {"edge_count": edge_count,
            "norm_bad": norm_bad, "nonneg_bad": nonneg_bad,
            "keep_max": str(keep_max), "keep_argmax": keep_arg, "keep_pos_count": keep_pos,
            "keep_cex": keep_cex,
            "delete_max": str(del_max), "delete_argmax": del_arg, "delete_pos_count": del_pos,
            "delete_cex": del_cex}


def finalize_counts(pair_ids, ntrees, H_fn, partial):
    """Exact diagonal/nonnegativity totals (separate cheap pass)."""
    C = ntrees
    norm_count = 0
    norm_list = list(partial["norm_bad"])
    nonneg_count = 0
    nonneg_list = list(partial["nonneg_bad"])
    for pid in pair_ids:
        Hs = H_fn(pid)
        A_id = pid // C
        if pid - A_id * C == A_id and Hs != 0:
            norm_count += 1
            if len(norm_list) < MAX_PRESERVED_CEX_PER_MODE:
                norm_list.append(pid)
        if Hs < 0:
            nonneg_count += 1
            if len(nonneg_list) < MAX_PRESERVED_CEX_PER_MODE:
                nonneg_list.append(pid)
    partial["norm_count"] = norm_count
    partial["norm_bad"] = sorted(set(norm_list))[:MAX_PRESERVED_CEX_PER_MODE]
    partial["nonneg_count"] = nonneg_count
    partial["nonneg_bad"] = sorted(set(nonneg_list))[:MAX_PRESERVED_CEX_PER_MODE]
    return partial


def _better(cur_max, cur_arg, new_max, new_arg):
    """Higher residual wins; ties break to lexicographically first argmax."""
    if cur_max is None:
        return new_max, new_arg
    if new_max is None:
        return cur_max, cur_arg
    if int(new_max) > int(cur_max):
        return new_max, new_arg
    if int(new_max) == int(cur_max) and list(new_arg) < list(cur_arg):
        return new_max, new_arg
    return cur_max, cur_arg


def combine_partials(parts):
    """Deterministic exact reduction over shard partials."""
    out = {"edge_count": 0, "keep_pos_count": 0, "delete_pos_count": 0,
           "norm_count": 0, "nonneg_count": 0,
           "keep_max": None, "keep_argmax": None, "delete_max": None, "delete_argmax": None,
           "keep_cex": [], "delete_cex": [], "norm_bad": [], "nonneg_bad": []}
    for p in parts:
        out["edge_count"] += p["edge_count"]
        out["keep_pos_count"] += p["keep_pos_count"]
        out["delete_pos_count"] += p["delete_pos_count"]
        out["norm_count"] += p.get("norm_count", 0)
        out["nonneg_count"] += p.get("nonneg_count", 0)
        out["keep_max"], out["keep_argmax"] = _better(
            out["keep_max"], out["keep_argmax"], p["keep_max"], p["keep_argmax"])
        out["delete_max"], out["delete_argmax"] = _better(
            out["delete_max"], out["delete_argmax"], p["delete_max"], p["delete_argmax"])
    # Counterexample merge: global lex-first 16 per mode.
    for key, ck in (("keep_cex", None), ("delete_cex", None)):
        merged = []
        for p in parts:
            merged.extend(p[key])
        merged.sort(key=lambda e: (e[0], e[1], e[2]))
        out[key] = merged[:MAX_PRESERVED_CEX_PER_MODE]
    nb = []
    nnb = []
    for p in parts:
        nb.extend(p.get("norm_bad", []))
        nnb.extend(p.get("nonneg_bad", []))
    out["norm_bad"] = sorted(set(nb))[:MAX_PRESERVED_CEX_PER_MODE]
    out["nonneg_bad"] = sorted(set(nnb))[:MAX_PRESERVED_CEX_PER_MODE]
    return out


def sweep_pair_access(pair_ids, ntrees, n, after, cost, H_fn, H_den, p_H, q_H,
                      shards=1):
    """Full deterministic sweep (sharded with exact reduction)."""
    if shards == 1:
        part = sweep_shard(pair_ids, ntrees, n, after, cost, H_fn, H_den, p_H, q_H)
        return finalize_counts(pair_ids, ntrees, H_fn, part)
    k = len(pair_ids)
    bounds = [i * k // shards for i in range(shards + 1)]
    parts = []
    for i in range(shards):
        sub = pair_ids[bounds[i]:bounds[i + 1]]
        part = sweep_shard(sub, ntrees, n, after, cost, H_fn, H_den, p_H, q_H)
        parts.append(finalize_counts(sub, ntrees, H_fn, part))
    return combine_partials(parts)
