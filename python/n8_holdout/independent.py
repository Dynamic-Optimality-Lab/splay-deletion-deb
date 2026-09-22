"""Independent n=8 Pair-Access evaluator (SA-03 §SA-03.11 clean-room).

Receives ONLY: frozen H math text (here: the H=0 test-vector definition),
frozen b_H, tree grammar parameters, action contract, candidate/test ID.
Reimplements pair decoding, transition walk, access cost, both residuals
from scratch. Imports NOTHING from candidate-synthesis code and nothing else
from this repository: only the standard library plus zstandard (for reading
the sealed compressed tables). No sys.path manipulation. A static audit
(SA03-SEP) enforces this separation.

Residual arrangement is deliberately reordered vs the primary sweep
((q*cB - p*cA) + q*dH instead of q*cB + q*dH - p*cA) so agreement also
covers operation-order independence. Results are mathematically identical
exact integers.
"""
import json
import os

KEEP, DELETE = 0, 1


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def load_domain_ind(tables_dir, reach_dir):
    """Own sealed-table loader: (n, ntrees, ascending pair_ids, after, cost)."""
    import zstandard as zstd
    with open(os.path.join(tables_dir, "forward.bin.zst"), "rb") as f:
        fwd = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    n = int(fwd["n"])
    top = 0
    for rec in fwd["records"]:
        if int(rec["tree"]) + 1 > top:
            top = int(rec["tree"]) + 1
    nxt = [[0] * top for _ in range(n + 1)]
    pay = [[0] * top for _ in range(n + 1)]
    for rec in fwd["records"]:
        nxt[int(rec["x"])][int(rec["tree"])] = int(rec["after"])
        pay[int(rec["x"])][int(rec["tree"])] = int(rec["cost"])
    with open(os.path.join(reach_dir, "reachable.json.zst"), "rb") as f:
        reach = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    pids = sorted(int(p) for p in reach["pair_ids"])
    return n, top, pids, nxt, pay


def sweep_ind(pids, trees, n, nxt, pay, h_of, h_den, num_p, den_q):
    """Independent full sweep. h_of(pid)->int. Returns result dict."""
    C = trees
    qD = den_q * h_den
    total = 0
    bad_diag = []
    bad_nn = []
    ndiag = 0
    nneg = 0
    kmax = None
    karg = None
    kpos = 0
    kex = []
    dmax = None
    darg = None
    dpos = 0
    dex = []
    for pid in pids:
        at = pid // C
        bt = pid - at * C
        hs = h_of(pid)
        if at == bt and hs != 0:
            ndiag += 1
            if len(bad_diag) < 16:
                bad_diag.append(pid)
        if hs < 0:
            nneg += 1
            if len(bad_nn) < 16:
                bad_nn.append(pid)
        # KEEP keys 1..n, then DELETE keys 1..n (frozen edge order).
        for kk in range(1, n + 1):
            total += 1
            na = nxt[kk][at]
            ca = pay[kk][at]
            nb = nxt[kk][bt]
            cb = pay[kk][bt]
            tgt = na * C + nb
            rk = (den_q * cb - num_p * ca) * h_den + qD * (h_of(tgt) - hs)
            if kmax is None or rk > kmax or (rk == kmax and [pid, KEEP, kk] < karg):
                kmax = rk
                karg = [pid, KEEP, kk]
            if rk > 0:
                kpos += 1
                if len(kex) < 16:
                    kex.append([pid, KEEP, kk, str(rk)])
        for kk in range(1, n + 1):
            total += 1
            na = nxt[kk][at]
            ca = pay[kk][at]
            tgt = na * C + bt
            rd = qD * (h_of(tgt) - hs) - h_den * num_p * ca
            if dmax is None or rd > dmax or (rd == dmax and [pid, DELETE, kk] < darg):
                dmax = rd
                darg = [pid, DELETE, kk]
            if rd > 0:
                dpos += 1
                if len(dex) < 16:
                    dex.append([pid, DELETE, kk, str(rd)])
    return {"edge_count": total, "norm_count": ndiag, "norm_bad": bad_diag,
            "nonneg_count": nneg, "nonneg_bad": bad_nn,
            "keep_max": str(kmax), "keep_argmax": karg, "keep_pos_count": kpos,
            "keep_cex": kex, "delete_max": str(dmax), "delete_argmax": darg,
            "delete_pos_count": dpos, "delete_cex": dex}


def main(argv=None):
    """CLI: full sweep with the H=0 test vector (machinery self-test helper)."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables-dir", required=True)
    ap.add_argument("--reach-dir", required=True)
    ap.add_argument("--p", type=int, default=23)
    ap.add_argument("--q", type=int, default=14)
    args = ap.parse_args(argv)
    console_log("N8-IND-01", "independent sweep start")
    n, trees, pids, nxt, pay = load_domain_ind(args.tables_dir, args.reach_dir)
    out = sweep_ind(pids, trees, n, nxt, pay, lambda _p: 0, 1, args.p, args.q)
    console_log("N8-IND-02", "edges=%d keep_max=%s delete_max=%s" % (
        out["edge_count"], out["keep_max"], out["delete_max"]))
    print(json.dumps({k: out[k] for k in ("edge_count", "keep_max", "delete_max",
                                         "keep_pos_count", "delete_pos_count")}))
    return 0


if __name__ == "__main__":
    main()
