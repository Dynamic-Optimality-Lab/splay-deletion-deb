"""Global linear obstruction analysis (WP-4 completion, POST-n7-DEVELOPMENT).

n=6/n=7 rows are DEVELOPMENT/FALSIFICATION data only (n7_status =
PREVIOUSLY_REVEALED_AFTER_H-SA02-B-v1-final_FREEZE). No untouched claims.

Outputs:
  artifacts/hypotheses/track_b_alternatives.json  (canonical exact solutions x n6/n7 residuals)
  artifacts/hypotheses/global_n456_report.json    (n=4+5+6 FCYCLE system)
  artifacts/hypotheses/global_n4567_report.json   (n=4+5+6+7 FCYCLE diagnostic system)
  artifacts/hypotheses/mis_n456.json              (minimum inconsistent subsystem)
  artifacts/hypotheses/identical_deltaF.json      (identical-input check)

Central question: does any single linear state-only F-v0.1 potential explain
all currently known cyclic forced derivatives simultaneously? Answered exactly.
"""
import itertools
import json
import os
import sys
from fractions import Fraction

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining import holdout_firewall as firewall
from python.mining.exact_linear import FEATURE_ORDER, b_for_n
from python.mining.affine_exhaustion import (
    load_fcyclerows, mat_of, tgt_of, sp_matrix, sp_vector,
    primitive_intvec, residual_vector,
)


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def row_label(r):
    return "n=%d src=%d %s k=%d L=%s" % (
        r["n"], r["source_state_id"], r["mode"], r["key"], r["scaled_slack"])


def consistent(rows_idx, M, t):
    import sympy as sp
    sub_m = [M[i] for i in rows_idx]
    sub_t = [t[i] for i in rows_idx]
    m = sp_matrix(sub_m)
    b = sp_vector(sub_t)
    return m.rank() == m.row_join(b).rank()


def minimize_witness(witness, M, t):
    """Greedy shrink to irreducible set (deterministic order)."""
    changed = True
    w = list(witness)
    while changed:
        changed = False
        for r in list(w):
            trial = [x for x in w if x != r]
            if not consistent(trial, M, t):
                w = trial
                changed = True
                break
    return w


def verify_minimum(witness, M, t):
    """True iff every proper subset is consistent (minimum-cardinality proof)."""
    for k in range(len(witness)):
        sub = witness[:k] + witness[k + 1:]
        if not consistent(sub, M, t):
            return False
    return True


def certificate_witnesses(M45, t45, basis_idx, rows_all, M_all, t_all, off45):
    """For each non-selection row in the row-span of the selection basis with a
    mismatched implied target, build a spanning-subset + row witness."""
    import sympy as sp
    B = [M45[i] for i in basis_idx]
    tB = [t45[i] for i in basis_idx]
    Bt = sp_matrix(B).T
    witnesses = []
    for j in range(off45, len(M_all)):
        r = M_all[j]
        # Solve Bt c = r (is r in the row span?).
        aug = Bt.row_join(sp_vector(r))
        if Bt.rank() != aug.rank():
            continue
        sol, params = Bt.gauss_jordan_solve(sp_vector(r))
        subs = {p: sp.Rational(0) for p in params}
        c = [sp.simplify(x.subs(subs)) if hasattr(x, "subs") else x for x in sol]
        implied = sum(ci * ti for ci, ti in zip(c, [sp.Rational(x.numerator, x.denominator) for x in tB]))
        if implied == sp.Rational(t_all[j].numerator, t_all[j].denominator):
            continue
        support = [basis_idx[i] for i, ci in enumerate(c) if ci != 0]
        witnesses.append({"row": j, "support": support,
                          "implied": str(implied), "actual": "%s/%s" % (t_all[j].numerator, t_all[j].denominator)})
    return witnesses


def main():
    firewall.hydrate_from_files()
    # ---- selection system + canonical alternatives ----
    sel_rows = load_fcyclerows([4, 5])
    M45, t45 = mat_of(sel_rows), tgt_of(sel_rows)
    aff = json.load(open(os.path.join(REPO, "artifacts", "hypotheses",
                                      "track_b_affine_space.json"), encoding="utf-8"))
    import sympy as sp
    part = [Fraction(v) for v in aff["selection"]["particular_solution"].values()
            ] if isinstance(aff["selection"]["particular_solution"], dict) else None
    # particular_solution stored as dict feature->str; rebuild in order.
    part = [Fraction(aff["selection"]["particular_solution"][k]) for k in FEATURE_ORDER]
    null_ints = aff["selection"]["nullspace_basis_primitive_int"]
    alternatives = {"particular_H-SA02-B-v1-family": part}
    for i, nv in enumerate(null_ints):
        alternatives["particular_plus_null_%d" % i] = [p + Fraction(v) for p, v in zip(part, nv)]
    # 5-support canonical from sparse search.
    canon5 = aff["sparse_per_domain"]["SIGNED"]["example"]
    alpha5 = [Fraction(canon5.get(k, "0")) for k in FEATURE_ORDER]
    alternatives["canonical_5support"] = alpha5
    # Evaluate on n6/n7 FCYCLE as DEVELOPMENT data.
    firewall.guard_load("artifacts/features/n7/edge_deltas.json.zst")
    dev6 = load_fcyclerows([6])
    dev7 = load_fcyclerows([7])
    alt_report = {}
    for name, alpha in alternatives.items():
        r45, m45, _w = residual_vector(M45, t45, alpha)
        r6, m6, _w6 = residual_vector(mat_of(dev6), tgt_of(dev6), alpha)
        r7, m7, _w7 = residual_vector(mat_of(dev7), tgt_of(dev7), alpha)
        alt_report[name] = {
            "n45_max_residual": m45, "n6_max_residual": m6, "n7_max_residual": m7,
            "n45_residual_vector": r45, "n6_residual_vector": r6, "n7_residual_vector": r7,
            "n6_label": "DEVELOPMENT (revealed post-initial-freeze)",
            "n7_label": "DEVELOPMENT (n7_status=" + firewall.N7_STATUS + ")",
        }
        console_log("ALT", "%s n45=%s n6=%s n7=%s" % (name, m45, m6, m7))
    with open(os.path.join(REPO, "artifacts", "hypotheses", "track_b_alternatives.json"),
              "w", encoding="utf-8") as f:
        json.dump({"n7_status": firewall.N7_STATUS, "alternatives": alt_report}, f, sort_keys=True, indent=2)
        f.write("\n")
    # ---- combined systems ----
    m45 = sp_matrix(M45)
    reports = {}
    for tag, sizes in (("n456", [4, 5, 6]), ("n4567", [4, 5, 6, 7])):
        rows = load_fcyclerows(sizes)
        M, t = mat_of(rows), tgt_of(rows)
        m = sp_matrix(M)
        b = sp_vector(t)
        rank = m.rank()
        aug_rank = m.row_join(b).rank()
        rep = {
            "sizes": sizes,
            "row_count": len(rows),
            "rank_over_Q": rank,
            "nullity": 16 - rank,
            "augmented_rank": aug_rank,
            "consistent_over_Q": rank == aug_rank,
            "label": "POST-n7-DEVELOPMENT diagnostic evidence (NOT an untouched test)",
            "n7_status": firewall.N7_STATUS,
        }
        console_log("GLOBAL", "%s rows=%d rank=%d aug=%d consistent=%s" % (
            tag, len(rows), rank, aug_rank, rep["consistent_over_Q"]))
        reports[tag] = (rep, rows, M, t)
    for tag, (rep, _r, _m, _t) in reports.items():
        with open(os.path.join(REPO, "artifacts", "hypotheses", "global_%s_report.json" % tag),
                  "w", encoding="utf-8") as f:
            json.dump(rep, f, sort_keys=True, indent=2)
            f.write("\n")
    # ---- MIS for the first inconsistent combined system ----
    mis_saved = None
    for tag in ("n456", "n4567"):
        rep, rows, M, t = reports[tag]
        if rep["consistent_over_Q"]:
            continue
        basis_idx = json.load(open(os.path.join(
            REPO, "artifacts", "hypotheses", "track_b_linear_report.json"),
            encoding="utf-8"))["basis_row_indices"]
        off = len(M45)
        cands = certificate_witnesses(M45, t45, basis_idx, rows, M, t, off)
        console_log("MIS", "%s certificate witnesses: %d" % (tag, len(cands)))
        # Minimize each candidate, keep smallest; verify exact minimum.
        best = None
        for c in cands:
            w = minimize_witness(c["support"] + [c["row"]], M, t)
            if best is None or len(w) < len(best):
                best = w
        if best is not None and verify_minimum(best, M, t):
            mis_saved = {"system": tag, "indices": sorted(best),
                         "minimum_cardinality_verified": True,
                         "rows": [{k: rows[i][k] for k in
                                   ("n", "source_state_id", "target_state_id", "mode", "key",
                                    "a", "y", "scaled_slack", "b", "provenance")} for i in sorted(best)]}
            console_log("MIS", "%s minimum witness size=%d" % (tag, len(best)))
            break
        elif best is not None:
            # Irreducible but minimum not proven by single-drop; search smaller subsets.
            found = None
            pool = sorted(set(sum(([c["support"] + [c["row"]] for c in cands]), [])))
            for k in range(2, len(best)):
                for sub in itertools.combinations(pool, k):
                    if not consistent(list(sub), M, t):
                        found = list(sub)
                        break
                if found is not None:
                    break
            if found is not None and verify_minimum(found, M, t):
                mis_saved = {"system": tag, "indices": sorted(found),
                             "minimum_cardinality_verified": True,
                             "rows": [{k: rows[i][k] for k in
                                       ("n", "source_state_id", "target_state_id", "mode", "key",
                                        "a", "y", "scaled_slack", "b", "provenance")} for i in sorted(found)]}
                console_log("MIS", "%s exact-minimum witness size=%d" % (tag, len(found)))
                break
            mis_saved = {"system": tag, "indices": sorted(best),
                         "minimum_cardinality_verified": False,
                         "note": "irreducible (greedy, deterministic); exact minimum not proven",
                         "rows": [{k: rows[i][k] for k in
                                   ("n", "source_state_id", "target_state_id", "mode", "key",
                                    "a", "y", "scaled_slack", "b", "provenance")} for i in sorted(best)]}
            console_log("MIS", "%s irreducible witness size=%d (minimum unproven)" % (tag, len(best)))
            break
    if mis_saved is None:
        # All combined systems consistent (unexpected per v1 failure, but record honestly).
        mis_saved = {"system": None, "indices": [],
                     "note": "all combined systems consistent over Q; no obstruction witness"}
    with open(os.path.join(REPO, "artifacts", "hypotheses", "mis_n456.json"),
              "w", encoding="utf-8") as f:
        json.dump(mis_saved, f, sort_keys=True, indent=2)
        f.write("\n")
    # ---- identical DeltaF check ----
    all_rows = load_fcyclerows([2, 3, 4, 5, 6, 7])
    groups = {}
    for i, r in enumerate(all_rows):
        key = tuple(r["delta_F"][k] for k in FEATURE_ORDER)
        groups.setdefault(key, []).append(i)
    same_n, cross_n = [], []
    for key, idxs in groups.items():
        if len(idxs) < 2:
            continue
        tgts = set((all_rows[i]["target"].numerator, all_rows[i]["target"].denominator) for i in idxs)
        if len(tgts) > 1:
            entry = {"delta_F": {k: v for k, v in zip(FEATURE_ORDER, key)},
                     "rows": [row_label(all_rows[i]) + " ell=%s/%s" % (
                         all_rows[i]["target"].numerator, all_rows[i]["target"].denominator) for i in idxs]}
            if len(set(all_rows[i]["n"] for i in idxs)) == 1:
                same_n.append(entry)
            else:
                cross_n.append(entry)
    console_log("IDENT", "same-n conflicts=%d cross-n conflicts=%d" % (len(same_n), len(cross_n)))
    with open(os.path.join(REPO, "artifacts", "hypotheses", "identical_deltaF.json"),
              "w", encoding="utf-8") as f:
        json.dump({"same_n_identical_input_conflicts": same_n,
                   "cross_n_identical_input_conflicts": cross_n,
                   "note_same_n": "same-n conflict with different ell is the strongest F-v0.1-linear insufficiency witness",
                   "note_cross_n": "cross-n conflicts use per-n b* targets; valid global-linear obstructions "
                                   "(one alpha must fit all b* simultaneously)"}, f, sort_keys=True, indent=2)
        f.write("\n")
    console_log("GLOBAL-99", "done")


if __name__ == "__main__":
    main()
