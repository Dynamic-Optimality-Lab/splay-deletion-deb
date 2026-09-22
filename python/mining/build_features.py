"""Build F-v0.1 feature tables + edge deltas (staged, firewall-gated).

Stage 1 (before initial freeze): n=2,3,4,5 only.
Stage 2 (after initial freeze): n=6 validation.
Stage 3 (after final freeze, unlocked once): n=7 holdout.

State tables depend only on (A,B,n); edge deltas join forced edges post-hoc.
"""

import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from python.mining import holdout_firewall as firewall


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def build_state_table(target_n, outdir):
    from python.reference import tree as ref_tree
    from python.reference import enumerate as ref_enum
    from python.reference import pair_graph as ref_pg
    from python.mining import scalar_features as feat
    if target_n == 6:
        firewall.guard_initial_fit_load("artifacts/features/n6/feature_table.json.zst")
    if target_n == 7:
        firewall.guard_load("artifacts/features/n7/feature_table.json.zst")
    shapes = ref_enum.canonical_shapes(target_n)
    tables = ref_pg.build_tables(target_n)
    reach = ref_pg.build_reachability(tables)
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for pair_id in reach.pair_ids:
        tree_count = len(shapes)
        a_id, b_id = divmod(pair_id, tree_count)
        scalars, vectors = feat.extract_state_features(
            shapes[a_id], shapes[b_id], target_n,
            ref_tree.assign_inorder_keys, ref_tree.parse_shape)
        vec_hashes = {}
        for k, v in vectors.items():
            blob = (json.dumps(v, sort_keys=True)).encode("utf-8")
            vec_hashes[k] = hashlib.sha256(blob).hexdigest()
        rows.append({"pair_id": pair_id, "feature_schema_version": "F-v0.1",
                     "scalar": scalars, "vector_hashes": vec_hashes,
                     "vectors": vectors})
    import zstandard as zstd
    blob = (json.dumps(rows, sort_keys=True) + "\n").encode("utf-8")
    logical = hashlib.sha256(blob).hexdigest()
    with open(os.path.join(outdir, "feature_table.json.zst"), "wb") as f:
        f.write(zstd.ZstdCompressor(level=10).compress(blob))
    with open(os.path.join(outdir, "hashes.json"), "w", encoding="utf-8") as f:
        json.dump({"logical_sha256": logical, "n": target_n,
                   "rows": len(rows), "version": "F-v0.1"}, f, sort_keys=True, indent=2)
        f.write("\n")
    console_log("FEAT", "n=%d rows=%d sha=%s" % (target_n, len(rows), logical[:16]))
    return logical


def build_edge_deltas(target_n, feat_dir, crit_dir, out_path):
    import zstandard as zstd
    if target_n == 6:
        firewall.guard_initial_fit_load("artifacts/features/n6/edge_deltas.json.zst")
    if target_n == 7:
        firewall.guard_load("artifacts/features/n7/edge_deltas.json.zst")
    with open(os.path.join(cert_dir_for(target_n), "bn_certificate.json"), encoding="utf-8") as f:
        cert = json.load(f)
    prime_p, prime_q = int(cert["b"]["p"]), int(cert["b"]["q"])
    # Load feature table.
    with open(os.path.join(feat_dir, "feature_table.json.zst"), "rb") as f:
        feat_rows = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    feat_by_pid = {r["pair_id"]: r["scalar"] for r in feat_rows}
    # Load forced edges.
    with open(os.path.join(crit_dir, "forced_delta_edges.json.zst"), "rb") as f:
        forced = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    deltas = []
    for row in forced:
        src = row["source_pair_id"]; tgt = row["target_pair_id"]
        f_src = feat_by_pid[src]; f_tgt = feat_by_pid[tgt]
        delta = {k: f_tgt[k] - f_src[k] for k in f_src}
        deltas.append({"n": target_n, "source_state_id": src, "target_state_id": tgt,
                       "mode": row["mode"], "key": row["key"],
                       "provenance": row["provenance"],
                       "on_zero_path": row["on_zero_path"],
                       "on_zero_cycle": row["on_zero_cycle"],
                       "a": row["a"], "y": row["y"],
                       "scaled_slack": row["scaled_slack"],
                       "delta_F": delta})
    blob = (json.dumps(deltas, sort_keys=True) + "\n").encode("utf-8")
    logical = hashlib.sha256(blob).hexdigest()
    with open(out_path, "wb") as f:
        f.write(zstd.ZstdCompressor(level=10).compress(blob))
    console_log("DELTA", "n=%d forced=%d sha=%s" % (target_n, len(deltas), logical[:16]))
    return logical


def cert_dir_for(target_n):
    return os.path.join(REPO, "artifacts", "certificates", "n%d" % target_n)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--stage", choices=["state", "deltas"], required=True)
    args = ap.parse_args(argv)
    # Production hydration: load persistent freeze state so post-freeze
    # validation/holdout stages are permitted (tests never hydrate).
    try:
        firewall.hydrate_from_files()
    except Exception:
        pass
    base = os.path.join(REPO, "artifacts")
    if args.stage == "state":
        build_state_table(args.n, os.path.join(base, "features", "n%d" % args.n))
    else:
        build_edge_deltas(args.n,
                          os.path.join(base, "features", "n%d" % args.n),
                          os.path.join(base, "critical", "n%d" % args.n),
                          os.path.join(base, "features", "n%d" % args.n, "edge_deltas.json.zst"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
