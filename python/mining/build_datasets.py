"""Build Track-A / Track-B dataset manifests (immutable, hashed).

Track A: n=2..5 forced edges with reserved_family_holdout==false
  (reserved = FCYCLE or DELETE or zig-zag A-rotation LR/RL).
Track B: n=4,5 all FCYCLE FORCED_DELTA rows (20 equations).
Validation/holdout datasets are separate files (built after freezes).
"""

import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def load_deltas(target_n):
    import zstandard as zstd
    p = os.path.join(REPO, "artifacts", "features", "n%d" % target_n, "edge_deltas.json.zst")
    with open(p, "rb") as f:
        return json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))


def is_zigzag_row(delta_row, shapes_cache, ref_tree, ref_splay):
    src = delta_row["source_state_id"]
    key = delta_row["key"]
    target_n = delta_row["n"]
    shapes = shapes_cache[target_n]
    tree_count = len(shapes)
    a_id = src // tree_count
    t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shapes[a_id]))
    _, _, cases, _ = ref_splay.splay(t, key)
    return any(x in ("LR", "RL") for x in cases)


def build_manifests(outdir):
    from python.reference import tree as ref_tree
    from python.reference import splay as ref_splay
    from python.reference import enumerate as ref_enum
    os.makedirs(outdir, exist_ok=True)
    shapes_cache = {n: ref_enum.canonical_shapes(n) for n in (2, 3, 4, 5)}
    # Track A.
    rows_a = []
    for n in (2, 3, 4, 5):
        for row in load_deltas(n):
            is_fcycle = "FCYCLE" in row["provenance"]
            is_delete = row["mode"] == "DELETE"
            is_zz = is_zigzag_row(row, shapes_cache, ref_tree, ref_splay)
            reserved = is_fcycle or is_delete or is_zz
            if not reserved:
                rows_a.append({
                    "n": row["n"], "source_state_id": row["source_state_id"],
                    "target_state_id": row["target_state_id"], "mode": row["mode"],
                    "key": row["key"], "scaled_slack": row["scaled_slack"],
                    "provenance": row["provenance"],
                    "delta_F": row["delta_F"],
                })
    # Track B: n=4,5 FCYCLE only.
    rows_b = []
    for n in (4, 5):
        for row in load_deltas(n):
            if "FCYCLE" in row["provenance"] and row["n"] in (4, 5):
                rows_b.append({
                    "n": row["n"], "source_state_id": row["source_state_id"],
                    "target_state_id": row["target_state_id"], "mode": row["mode"],
                    "key": row["key"], "scaled_slack": row["scaled_slack"],
                    "provenance": row["provenance"],
                    "delta_F": row["delta_F"],
                })
    # Sort deterministically.
    rows_a.sort(key=lambda r: (r["n"], r["source_state_id"], r["mode"], r["key"]))
    rows_b.sort(key=lambda r: (r["n"], r["source_state_id"], r["mode"], r["key"]))
    manifest_a = {
        "dataset_id": "WP4-TRACK-A-v1",
        "experiment_id": "SPLAY-AM-PD-v0.1",
        "track": "A",
        "amendment_id": "SA-02",
        "selection_sizes": [2, 3, 4, 5],
        "selection_rule": "forced edges with reserved_family_holdout==false (FCYCLE/DELETE/zig-zag excluded)",
        "validation_size": 6,
        "holdout_size": 7,
        "rows": rows_a,
        "validation_rows_separate": True,
    }
    manifest_b = {
        "dataset_id": "WP4-TRACK-B-v1",
        "experiment_id": "SPLAY-AM-PD-v0.1",
        "track": "B",
        "amendment_id": "SA-02",
        "selection_sizes": [4, 5],
        "selection_rule": "all FCYCLE FORCED_DELTA rows at n=4,5",
        "validation_size": 6,
        "holdout_size": 7,
        "rows": rows_b,
        "validation_rows_separate": True,
    }
    for manifest, name in ((manifest_a, "track_a_manifest.json"), (manifest_b, "track_b_manifest.json")):
        # Hash over rows + rule (excluding sha field itself).
        payload = {k: v for k, v in manifest.items() if k != "sha256"}
        blob = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
        manifest["sha256"] = hashlib.sha256(blob).hexdigest()
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as f:
            json.dump(manifest, f, sort_keys=True, indent=2)
            f.write("\n")
        console_log("DATASET", "%s rows=%d sha=%s" % (name, len(manifest["rows"]), manifest["sha256"][:16]))
    return manifest_a, manifest_b


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "artifacts", "datasets"))
    args = ap.parse_args(argv)
    build_manifests(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
