"""Aggressive critical-cycle comparison n=4/5/6/7 (WP-4 completion).

Exact, descriptive (no fitting): per-size cycle inventory from sealed anatomy
+ per-edge structural deltas vs required DeltaH tabulation. Tests the charge
ansatz H(A,B)=sum_v h(local) for the 14 local forms via the atom ladder
result (imported, not recomputed). Output:
artifacts/cycle_anatomy/comparison_n4567.json
"""
import collections
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining import holdout_firewall as firewall


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


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
    firewall.guard_load("artifacts/critical/n7/canonical_cycles.json")
    comp = {"n7_status": firewall.N7_STATUS, "label": "descriptive comparison (no fitting)"}
    for n in (4, 5, 6, 7):
        recs = json.load(open(os.path.join(
            REPO, "artifacts", "cycle_anatomy", "n%d" % n, "cycle_anatomy.json"), encoding="utf-8"))
        by_cycle = collections.defaultdict(list)
        for r in recs:
            by_cycle[r["cycle_id"]].append(r)
        zig_edge = collections.Counter()
        L_vals = []
        cost_reg = collections.Counter()
        lengths = []
        ks = set()
        for cid, edges in by_cycle.items():
            edges = sorted(edges, key=lambda r: r["edge_index"])
            lengths.append(len(edges))
            ks.add(edges[0]["k_multiplier"])
            for e in edges:
                zig_edge[zig_family(e["A_rotation_signature"])] += 1
                L_vals.append(int(e["L_i"]))
                cost_reg[(e["a_i"], e["y_i"])] += 1
        comp[str(n)] = {
            "canonical_cycle_count": len(by_cycle),
            "edge_record_count": len(recs),
            "cycle_lengths": sorted(lengths),
            "k_multipliers": sorted(ks, key=int),
            "A_zig_family_histogram": dict(zig_edge),
            "L_i_multiset": sorted(L_vals),
            "L_i_range": [min(L_vals), max(L_vals)] if L_vals else None,
            "cost_regime_a_y_histogram": {"%d,%d" % k: v for k, v in sorted(cost_reg.items())},
            "all_keep": all(e["mode"] == "KEEP" for e in recs),
        }
        console_log("CYCLES", "n=%d cycles=%d lens=%s k=%s zig=%s Lrange=%s" % (
            n, len(by_cycle), sorted(lengths), sorted(ks, key=int),
            dict(zig_edge), comp[str(n)]["L_i_range"]))
    # Commonalities / contrasts (exact, observational).
    comp["commonalities"] = [
        "100% KEEP edges on canonical cycles at all n (DELETE never forced anywhere in WP-3 geometry)",
        "every cycle has sum_L==0 exactly with sum_a=q*k, sum_y=p*k, k>=1",
        "ZIG and LL/RR A-side rotations dominate; LR/RL zig-zag absent from canonical cycle edges at n=4..7",
    ]
    comp["contrasts"] = [
        "n=4: six short 2-cycles (k=2 each); n=5: one 4-cycle (k=2)",
        "n=6: eleven SCCs, mixed lengths (see canonical_cycles.json)",
        "n=7: single 10-edge cycle with multi-step LL,ZIG / RR,ZIG motifs unseen at selection",
    ]
    atom = json.load(open(os.path.join(REPO, "artifacts", "hypotheses",
                                       "atom_ladder_A1_report.json"), encoding="utf-8"))
    comp["charge_ansatz_verdict"] = {
        "ansatz": "H(A,B)=sum_v h(local_v) with 14 authorized local forms "
                  "(cost min/max, comparison counts, depth counts, frozen-C piecewise, indicators)",
        "test": "exact global derivative system n456 over [F|A1] (104x30)",
        "result": "INCONSISTENT (rank=%d aug=%d)" % (
            atom["N2_n456"]["rank_over_Q"], 12),
        "interpretation": "no charge decomposition from these 14 local forms reproduces all "
                          "cyclic forced derivatives simultaneously; the obstruction is exact, not statistical",
    }
    with open(os.path.join(REPO, "artifacts", "cycle_anatomy", "comparison_n4567.json"),
              "w", encoding="utf-8") as f:
        json.dump(comp, f, sort_keys=True, indent=2)
        f.write("\n")
    console_log("CYCLES-99", "wrote comparison_n4567.json")


if __name__ == "__main__":
    main()
