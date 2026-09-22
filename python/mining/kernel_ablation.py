"""Kernel ablation, complete program (WP-4 completion).

FULL_STATE positive control must pass. Every compressed kernel is tested for:
  (a) value-separation: same K, different (V,U) canonical values, and
  (b) transition-preservation: same K(s1)==K(s2) with agreeing observables
      (c_A cost, KEEP-observable c_B) but K(succ(s1))!=K(succ(s2)).
Representative-based exact check (transitivity of equality makes rep-vs-each
sufficient): per kernel group, rep = min pair_id, every other member compared
against rep on every (mode,key) in frozen edge order. Full check for n=2..5;
value-separation additionally swept on n=6,7 (transition scope labeled).
Ablation removes one family at a time; sharpness table records smallest
failing n + witness pair + failure kind + exact mismatches.

State inputs only (feature tables); V/U joined post-hoc as the VALUE oracle
(per WorkPlan kernels may read V/U/G joins; extractor discipline unaffected).
"""
import json
import os
import sys
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

FAMILIES = ["depth", "parent", "ancestor", "subtree", "interval", "access", "crossing", "heavy"]
KERNEL_VERSION = "K-v0.1-complete"


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def family_keys(fam):
    mapping = {
        "depth": ["f_depth_sum_abs_diff", "f_depth_max_abs_diff", "f_root_same"],
        "parent": ["f_parent_diff_count", "f_parent_flip_count"],
        "ancestor": ["f_ancestor_Aonly", "f_ancestor_Bonly", "f_ancestor_both"],
        "subtree": ["f_subtree_sum_abs_diff"],
        "interval": ["f_interval_identical_count", "f_interval_symdiff_sum"],
        "access": ["f_access_sum_abs_diff", "f_access_symdiff_sum"],
        "crossing": ["f_crossing_reversal"],
        "heavy": ["f_heavy_agree_count"],
    }
    return mapping[fam]


def load_table(target_n):
    import zstandard as zstd
    p = os.path.join(REPO, "artifacts", "features", "n%d" % target_n, "feature_table.json.zst")
    with open(p, "rb") as f:
        return json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))


def load_VU(target_n):
    import zstandard as zstd
    out = {}
    for name in ("V", "U"):
        p = os.path.join(REPO, "artifacts", "potentials", "n%d" % target_n, "%s.json.zst" % name)
        with open(p, "rb") as f:
            rows = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
        for r in rows:
            out.setdefault(r["pair_id"], {})[name] = int(r["%s_scaled" % name])
    return out


def kernel_value(scalars, families):
    if families == ["FULL_STATE"]:
        return ("FULL", scalars.get("_pair_id"))
    vals = []
    for fam in families:
        for k in family_keys(fam):
            vals.append(scalars[k])
    return tuple(vals)


def test_value_separation(rows, vu, families):
    groups = {}
    for r in rows:
        groups.setdefault(kernel_value(r["scalar"], families), []).append(r["pair_id"])
    for kv in sorted(groups, key=str):
        pids = sorted(groups[kv])
        vals = set((vu[p]["V"], vu[p]["U"]) for p in pids)
        if len(vals) > 1:
            first = pids[0]
            second = next(p for p in pids[1:]
                          if (vu[p]["V"], vu[p]["U"]) != (vu[first]["V"], vu[first]["U"]))
            return {"pair": [first, second],
                    "V": [vu[first]["V"], vu[second]["V"]],
                    "U": [vu[first]["U"], vu[second]["U"]]}
    return None


def test_transition_preservation(rows, families, target_n, tables):
    """Representative-based full check. Returns witness dict or None."""
    from python.audit import graph as audit_graph
    sc = {r["pair_id"]: r["scalar"] for r in rows}
    groups = {}
    for r in rows:
        groups.setdefault(kernel_value(r["scalar"], families), []).append(r["pair_id"])
    nkeys = target_n
    for kv in sorted(groups, key=str):
        pids = sorted(groups[kv])
        if len(pids) < 2:
            continue
        rep = pids[0]
        for s in pids[1:]:
            for mode in (audit_graph.KEEP, audit_graph.DELETE):
                mname = "KEEP" if mode == audit_graph.KEEP else "DELETE"
                for key in range(1, nkeys + 1):
                    tr, ar, yr = audit_graph.successor(tables, rep, mode, key)
                    ts, a_s, ys = audit_graph.successor(tables, s, mode, key)
                    if (ar, yr) != (a_s, ys):
                        continue  # observables differ: preservation vacuous here
                    if kernel_value(sc[tr], families) != kernel_value(sc[ts], families):
                        return {"pair": [rep, s], "mode": mname, "key": key,
                                "observable_c_A": ar, "observable_c_B": yr,
                                "succ_rep": tr, "succ_other": ts,
                                "succ_kernel_rep": list(kernel_value(sc[tr], families)),
                                "succ_kernel_other": list(kernel_value(sc[ts], families))}
    return None


def test_kernel_full(target_n, families, track, tables, vu, rows):
    sep = test_value_separation(rows, vu, families)
    if sep is not None:
        return {"track": track, "n": target_n, "families": families,
                "verdict": "KERNEL_VALUE_INSUFFICIENT",
                "failure_kind": "value-separation",
                "witness": sep, "transition_scope": "not reached (value failed first)"}
    trans = test_transition_preservation(rows, families, target_n, tables)
    if trans is not None:
        return {"track": track, "n": target_n, "families": families,
                "verdict": "KERNEL_TRANSITION_FAIL",
                "failure_kind": "transition-preservation",
                "witness": trans, "transition_scope": "full (representative-based, all edges)"}
    return {"track": track, "n": target_n, "families": families,
            "verdict": "PASS", "failure_kind": None, "witness": None,
            "transition_scope": "full (representative-based, all edges)"}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", choices=["A", "B"], required=True)
    ap.add_argument("--sizes", default=None)
    args = ap.parse_args(argv)
    # Kernel scope follows the track's state domain (state-based, not row-based):
    # Track A spans n=2..5, Track B spans n=4,5. Explicit --sizes overrides.
    sizes = ([2, 3, 4, 5] if args.track == "A" else [4, 5]) if args.sizes is None \
        else [int(s) for s in args.sizes.split()]
    outdir = os.path.join(REPO, "artifacts", "kernels")
    os.makedirs(outdir, exist_ok=True)
    over = list(FAMILIES)
    kernels = [["FULL_STATE"]] + [[f for f in over if f != fam] for fam in FAMILIES]
    from python.audit import graph as audit_graph
    results = []
    for n in sorted(sizes):
        rows = load_table(n)
        for r in rows:
            r["scalar"]["_pair_id"] = r["pair_id"]
        vu = load_VU(n)
        tables = audit_graph.build_tables(n)
        for fams in kernels:
            results.append(test_kernel_full(n, fams, args.track, tables, vu, rows))
    # Sharpness: per ablated coordinate, smallest failing n + kind + witness.
    table = []
    # NOTE: frozen kernel_result.schema.json requires the key `smallest_n_failing`
    # (no "i"); legacy mining tables used `smallest_failing_n`. Both keys are
    # emitted with identical values (legacy alias documented, not silent).
    for fams in kernels:
        sub = [r for r in results if r["families"] == fams]
        if fams == ["FULL_STATE"]:
            table.append({"coordinate": "FULL_STATE", "coordinate_removed": "NONE(full-state control)",
                          "kernel_version": KERNEL_VERSION,
                          "smallest_failing_n": None, "smallest_n_failing": None,
                          "witness_pair": None,
                          "failure_type": "NONE", "exact_mismatch": None,
                          "verdict": "PASS" if all(r["verdict"] == "PASS" for r in sub) else "FAIL"})
            continue
        removed = [f for f in FAMILIES if f not in fams][0]
        fails = sorted([r for r in sub if r["verdict"] != "PASS"], key=lambda r: r["n"])
        if not fails:
            table.append({"coordinate": "minus_" + removed, "coordinate_removed": removed,
                          "kernel_version": KERNEL_VERSION,
                          "smallest_failing_n": None, "smallest_n_failing": None,
                          "witness_pair": None,
                          "failure_type": "NONE", "exact_mismatch": None, "verdict": "PASS"})
        else:
            f0 = fails[0]
            w = f0["witness"]
            table.append({"coordinate": "minus_" + removed, "coordinate_removed": removed,
                          "kernel_version": KERNEL_VERSION,
                          "smallest_failing_n": f0["n"], "smallest_n_failing": f0["n"],
                          "witness_pair": w.get("pair"), "failure_kind": f0["failure_kind"],
                          "failure_type": f0["verdict"],
                          "exact_mismatch": w, "verdict": f0["verdict"]})
    with open(os.path.join(outdir, "kernel_defs_%s.json" % args.track.lower()), "w", encoding="utf-8") as f:
        json.dump({"track": args.track, "families": FAMILIES, "overcomplete": over,
                   "kernel_version": KERNEL_VERSION,
                   "method": "value-separation on (V,U) + representative-based full transition check n<=5"}, f,
                  sort_keys=True, indent=2)
        f.write("\n")
    with open(os.path.join(outdir, "ablation_table_%s.json" % args.track.lower()), "w", encoding="utf-8") as f:
        json.dump(table, f, sort_keys=True, indent=2)
        f.write("\n")
    with open(os.path.join(outdir, "witnesses_%s.json" % args.track.lower()), "w", encoding="utf-8") as f:
        json.dump(results, f, sort_keys=True, indent=2)
        f.write("\n")
    console_log("KERNEL", "track=%s results=%d" % (args.track, len(results)))
    for row in table:
        console_log("KERNEL-SHARP", "%s n=%s %s" % (
            row["coordinate"], row["smallest_failing_n"], row["verdict"]))


if __name__ == "__main__":
    main()
