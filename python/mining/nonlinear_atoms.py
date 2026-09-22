"""Structured nonlinear atom ladder F-v0.1+A1 (WP-4 completion, POST-n7-DEVELOPMENT).

Only authorized atom classes (WorkPlan SPEC 09-11 ladder):
  min/max, exact sign/indicator predicates, local-count predicates,
  sums over nodes, interval/crossing interactions, access-path interactions,
  rank-gap/heavy interactions, frozen-breakpoint piecewise integer functions.
NO unrestricted symbolic regression. NO neural models. NO state/cycle IDs,
NO U/V/G/b*/slack/witness inputs. NO lookup table over n.

All atoms are exact integer functions of stored state-only F-v0.1 vectors
(depth_delta_by_key, all_next_key_costs) and scalars. New g_* namespace and
feature version F-v0.1+A1: F-v0.1 itself is never silently extended.

n=6/n=7 atom data are DEVELOPMENT/FALSIFICATION data only (n7_status =
PREVIOUSLY_REVEALED_AFTER_H-SA02-B-v1-final_FREEZE). No untouched claims.

Outputs:
  artifacts/features/n{N}/atom_table_A1.json.zst        (state atom values)
  artifacts/features/n{N}/edge_atom_deltas.json.zst     (edge atom deltas)
  artifacts/hypotheses/atom_ladder_A1_report.json       (exact search results)
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining import holdout_firewall as firewall

ATOM_VERSION = "F-v0.1+A1"


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


# Frozen atom definitions: name -> (class, pure function of (scalars, vectors)).
# Each definition is answer-independent (uses only stored state-only data).
def _atoms():
    def costs(v):
        return v["all_next_key_costs"]

    def depths(v):
        return v["depth_delta_by_key"]

    return {
        # -- sums over nodes of min/max local costs (min/max + per-node sums) --
        "g_cost_min_sum": ("minmax+nodesum",
                           lambda s, v: sum(min(a, b) for a, b in costs(v))),
        "g_cost_max_sum": ("minmax+nodesum",
                           lambda s, v: sum(max(a, b) for a, b in costs(v))),
        # -- local-count predicates on cost comparisons --
        "g_cost_A_gt_B": ("local-count",
                          lambda s, v: sum(1 for a, b in costs(v) if a > b)),
        "g_cost_A_lt_B": ("local-count",
                          lambda s, v: sum(1 for a, b in costs(v) if a < b)),
        # -- local-count predicates on depth disagreement --
        "g_depth_nonzero": ("local-count",
                            lambda s, v: sum(1 for d in depths(v) if d > 0)),
        "g_depth_ge2": ("local-count",
                        lambda s, v: sum(1 for d in depths(v) if d >= 2)),
        # -- frozen-breakpoint piecewise (breakpoints C=1 and C=2, frozen) --
        "g_depth_sum_cap2": ("piecewise-C2",
                             lambda s, v: min(s["f_depth_sum_abs_diff"], 2)),
        "g_depth_sum_excess2": ("piecewise-C2",
                                lambda s, v: max(0, s["f_depth_sum_abs_diff"] - 2)),
        "g_access_sum_cap2": ("piecewise-C2",
                              lambda s, v: min(s["f_access_sum_abs_diff"], 2)),
        "g_access_sum_excess2": ("piecewise-C2",
                                 lambda s, v: max(0, s["f_access_sum_abs_diff"] - 2)),
        # -- exact sign/indicator predicates on scalars --
        "g_sign_depth_sum": ("indicator",
                             lambda s, v: 1 if s["f_depth_sum_abs_diff"] > 0 else 0),
        "g_sign_access_sum": ("indicator",
                              lambda s, v: 1 if s["f_access_sum_abs_diff"] > 0 else 0),
        "g_sign_ancestor_Aonly": ("indicator",
                                  lambda s, v: 1 if s["f_ancestor_Aonly"] > 0 else 0),
        "g_sign_crossing": ("indicator",
                            lambda s, v: 1 if s["f_crossing_reversal"] > 0 else 0),
    }


ATOM_NAMES = sorted(_atoms().keys())
# Mirror behavior: every atom is a count/sum/min/max over all keys or a
# predicate of an invariant scalar -> invariant under joint key mirror.
MIRROR_A1 = {name: "invariant" for name in ATOM_NAMES}


def atom_state_values(scalars, vectors):
    defs = _atoms()
    return {name: int(fn(scalars, vectors)) for name, (_cls, fn) in defs.items()}


def build_atom_tables(sizes):
    import zstandard as zstd
    import hashlib
    for n in sorted(sizes):
        firewall.guard_initial_fit_load("artifacts/features/n%d/edge_deltas.json.zst" % n)
        firewall.guard_load("artifacts/features/n%d/edge_deltas.json.zst" % n)
        with open(os.path.join(REPO, "artifacts", "features", "n%d" % n,
                               "feature_table.json.zst"), "rb") as f:
            states = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
        by_pid = {}
        for st in states:
            by_pid[st["pair_id"]] = atom_state_values(st["scalar"], st["vectors"])
        blob = (json.dumps([{"pair_id": pid, "atom_version": ATOM_VERSION,
                             "atoms": by_pid[pid]} for pid in sorted(by_pid)],
                           sort_keys=True) + "\n").encode("utf-8")
        out = os.path.join(REPO, "artifacts", "features", "n%d" % n, "atom_table_A1.json.zst")
        with open(out, "wb") as f:
            f.write(zstd.ZstdCompressor(level=10).compress(blob))
        console_log("ATOM", "n=%d states=%d sha=%s" % (n, len(by_pid), hashlib.sha256(blob).hexdigest()[:16]))
    return True


def build_edge_atom_deltas(sizes):
    import zstandard as zstd
    for n in sorted(sizes):
        firewall.guard_initial_fit_load("artifacts/features/n%d/edge_deltas.json.zst" % n)
        firewall.guard_load("artifacts/features/n%d/edge_deltas.json.zst" % n)
        with open(os.path.join(REPO, "artifacts", "features", "n%d" % n,
                               "atom_table_A1.json.zst"), "rb") as f:
            atoms = {r["pair_id"]: r["atoms"] for r in json.loads(
                zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))}
        with open(os.path.join(REPO, "artifacts", "features", "n%d" % n,
                               "edge_deltas.json.zst"), "rb") as f:
            deltas = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
        out_rows = []
        for r in deltas:
            if "FCYCLE" not in r["provenance"]:
                continue
            a = atoms[r["source_state_id"]]
            b = atoms[r["target_state_id"]]
            out_rows.append({
                "n": n, "source_state_id": r["source_state_id"],
                "target_state_id": r["target_state_id"], "mode": r["mode"], "key": r["key"],
                "delta_G": {k: b[k] - a[k] for k in ATOM_NAMES},
            })
        out_rows.sort(key=lambda r: (r["n"], r["source_state_id"], r["mode"], r["key"]))
        blob = (json.dumps(out_rows, sort_keys=True) + "\n").encode("utf-8")
        out = os.path.join(REPO, "artifacts", "features", "n%d" % n, "edge_atom_deltas.json.zst")
        with open(out, "wb") as f:
            f.write(zstd.ZstdCompressor(level=10).compress(blob))
        console_log("ATOM-DELTA", "n=%d FCYCLE edges=%d" % (n, len(out_rows)))
    return True


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="4 5")
    ap.add_argument("--stage", choices=["states", "deltas"], required=True)
    args = ap.parse_args(argv)
    firewall.hydrate_from_files()
    sizes = [int(s) for s in args.sizes.split()]
    if args.stage == "states":
        build_atom_tables(sizes)
    else:
        build_edge_atom_deltas(sizes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
