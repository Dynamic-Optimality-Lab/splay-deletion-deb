"""Exact linear search first (SA-02, rationals only).

Solves sum_j alpha_j * DeltaF_j(e) = ell_b(e) over Q.
Per track: rank, nullity, basis rows, solution family if consistent,
sparsest integer candidates under frozen domains, exact max residual,
minimal inconsistent subsystem on failure. No float determines acceptance.
"""

import json
import os
import sys
from fractions import Fraction

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


FEATURE_ORDER = [
    "f_depth_sum_abs_diff", "f_depth_max_abs_diff", "f_root_same",
    "f_parent_diff_count", "f_parent_flip_count",
    "f_ancestor_Aonly", "f_ancestor_Bonly", "f_ancestor_both",
    "f_subtree_sum_abs_diff", "f_interval_identical_count",
    "f_interval_symdiff_sum", "f_access_sum_abs_diff",
    "f_access_symdiff_sum", "f_crossing_reversal",
    "f_heavy_agree_count", "f_bend_placeholder",
]


def load_manifest(track):
    name = "track_%s_manifest.json" % track.lower()
    with open(os.path.join(REPO, "artifacts", "datasets", name), encoding="utf-8") as f:
        return json.load(f)


def b_for_n(target_n):
    with open(os.path.join(REPO, "artifacts", "certificates", "n%d" % target_n,
                           "bn_certificate.json"), encoding="utf-8") as f:
        cert = json.load(f)
    return int(cert["b"]["p"]), int(cert["b"]["q"])


def build_system(rows):
    """Returns (matrix rows as Fraction lists, targets as Fraction)."""
    mat = []
    tgt = []
    for row in rows:
        prime_p, prime_q = b_for_n(row["n"])
        scaled = int(row["scaled_slack"])
        # ell = L/q
        target = Fraction(scaled, prime_q)
        vec = [Fraction(row["delta_F"][k]) for k in FEATURE_ORDER]
        mat.append(vec)
        tgt.append(target)
    return mat, tgt


def rank_nullity(mat):
    import sympy as sp
    if not mat:
        return 0, len(FEATURE_ORDER), []
    m = sp.Matrix([[sp.Rational(x.numerator, x.denominator) for x in row] for row in mat])
    r = m.rank()
    # Independent basis rows: first r linearly independent rows (greedy).
    basis = []
    cur = []
    for idx, row in enumerate(mat):
        trial = cur + [row]
        mm = sp.Matrix([[sp.Rational(x.numerator, x.denominator) for x in rr] for rr in trial])
        if mm.rank() > len(cur) and len(cur) < r:
            # Actually rank of trial vs rank of cur
            pass
        # Simpler: check rank increment.
        if not cur:
            # Single row: independent iff nonzero.
            if any(x != 0 for x in row):
                cur.append(row)
                basis.append(idx)
        else:
            m_cur = sp.Matrix([[sp.Rational(x.numerator, x.denominator) for x in rr] for rr in cur])
            m_trial = sp.Matrix([[sp.Rational(x.numerator, x.denominator) for x in rr] for rr in trial])
            if m_trial.rank() > m_cur.rank():
                cur = trial
                basis.append(idx)
        if len(basis) >= r:
            break
    return r, len(FEATURE_ORDER) - r, basis


def check_consistent(mat, tgt):
    import sympy as sp
    if not mat:
        return True, [sp.Rational(0)] * len(FEATURE_ORDER)
    m = sp.Matrix([[sp.Rational(x.numerator, x.denominator) for x in row] for row in mat])
    b = sp.Matrix([sp.Rational(x.numerator, x.denominator) for x in tgt])
    aug = m.row_join(b)
    if m.rank() != aug.rank():
        return False, None
    sol, params = m.gauss_jordan_solve(b)
    # Particular solution: set free parameters to 0.
    subs = {p: sp.Rational(0) for p in params}
    particular = [sp.simplify(x.subs(subs)) if hasattr(x, "subs") else x for x in sol]
    return True, particular


def max_residual_for_alpha(mat, tgt, alpha):
    worst = Fraction(0)
    for row, target in zip(mat, tgt):
        pred = sum(a * x for a, x in zip(alpha, row))
        res = abs(pred - target)
        if res > worst:
            worst = res
    return worst


def sparsest_integer_search(mat, tgt, max_M=2, max_support=2):
    """Brute-force sparse integer combos in [-M,M] up to support size.

    Returns best (support, coeffs, max_residual_num/den) by (residual, support).
    Floats never used. Deterministic order.
    """
    import itertools
    ncols = len(FEATURE_ORDER)
    best = None
    # Support 0 (zero predictor).
    zero_res = max_residual_for_alpha(mat, tgt, [Fraction(0)] * ncols) if mat else Fraction(0)
    best = (zero_res, (), {})
    cols = list(range(ncols))
    # Skip zero columns (bend placeholder) for support enumeration? Keep for completeness but they never help.
    for support_size in range(1, max_support + 1):
        for support in itertools.combinations(cols, support_size):
            # Skip supports containing only zero columns? Still evaluate (residual same as zero).
            for coeffs in itertools.product(range(-max_M, max_M + 1), repeat=support_size):
                if all(c == 0 for c in coeffs):
                    continue
                alpha = [Fraction(0)] * ncols
                for col, val in zip(support, coeffs):
                    alpha[col] = Fraction(val)
                res = max_residual_for_alpha(mat, tgt, alpha) if mat else Fraction(0)
                # Rank by (residual, support size, lexicographic).
                cand = (res, support, dict(zip([FEATURE_ORDER[c] for c in support], coeffs)))
                if cand[0] < best[0] or (cand[0] == best[0] and len(cand[1]) < len(best[1])):
                    best = cand
    return best


def minimal_inconsistent_subsystem(mat, tgt):
    """Smallest row subset that is already inconsistent (brute force by size)."""
    import itertools
    import sympy as sp
    nrows = len(mat)
    if nrows == 0:
        return None
    # Check full consistency first.
    m_full = sp.Matrix([[sp.Rational(x.numerator, x.denominator) for x in row] for row in mat])
    b_full = sp.Matrix([sp.Rational(x.numerator, x.denominator) for x in tgt])
    if m_full.rank() == m_full.row_join(b_full).rank():
        return None
    for size in range(1, min(nrows, 6) + 1):
        for subset in itertools.combinations(range(nrows), size):
            sub_m = [mat[i] for i in subset]
            sub_b = [tgt[i] for i in subset]
            m = sp.Matrix([[sp.Rational(x.numerator, x.denominator) for x in row] for row in sub_m])
            b = sp.Matrix([sp.Rational(x.numerator, x.denominator) for x in sub_b])
            if m.rank() != m.row_join(b).rank():
                return list(subset)
    return list(range(nrows))


def analyze_track(track, outdir):
    os.makedirs(outdir, exist_ok=True)
    manifest = load_manifest(track)
    rows = manifest["rows"]
    mat, tgt = build_system(rows)
    rank, nullity, basis = rank_nullity(mat)
    consistent, solution = check_consistent(mat, tgt)
    if consistent and solution is not None:
        sol_list = ["%s" % x for x in solution]
        # Max residual should be 0.
        alpha_frac = [Fraction(str(x)) for x in solution]
        worst = max_residual_for_alpha(mat, tgt, alpha_frac) if mat else Fraction(0)
    else:
        sol_list = None
        worst = None
    sparse_best = sparsest_integer_search(mat, tgt, max_M=2, max_support=2)
    sparse_res, sparse_support, sparse_coeffs = sparse_best
    mis = None if consistent else minimal_inconsistent_subsystem(mat, tgt)
    # Stratification counts.
    from collections import Counter
    strat = Counter((r["mode"], tuple(sorted(r["provenance"]))) for r in rows)
    report = {
        "track": track,
        "dataset_id": manifest["dataset_id"],
        "dataset_sha256": manifest["sha256"],
        "feature_order": FEATURE_ORDER,
        "row_count": len(rows),
        "rank_over_Q": rank,
        "nullity": nullity,
        "basis_row_indices": basis,
        "consistent_over_Q": consistent,
        "solution_family": sol_list,
        "exact_max_residual_best_sparse": "%s/%s" % (sparse_res.numerator, sparse_res.denominator),
        "sparsest_support": list(sparse_support),
        "sparsest_coeffs": sparse_coeffs,
        "minimal_inconsistent_subsystem": mis,
        "stratification": {str(k): v for k, v in strat.items()},
        "float_note": "floats not used; all exact rationals (non-authoritative floats: none)",
    }
    with open(os.path.join(outdir, "track_%s_linear_report.json" % track.lower()), "w", encoding="utf-8") as f:
        json.dump(report, f, sort_keys=True, indent=2)
        f.write("\n")
    if mis is not None:
        wit = {"track": track, "rows": [rows[i] for i in mis], "indices": mis,
               "note": "minimal inconsistent subsystem (exact over Q)"}
        with open(os.path.join(outdir, "track_%s_inconsistency_witness.json" % track.lower()),
                  "w", encoding="utf-8") as f:
            json.dump(wit, f, sort_keys=True, indent=2)
            f.write("\n")
    console_log("LINEAR", "track=%s rows=%d rank=%d nullity=%d consistent=%s sparse_res=%s mis=%s" % (
        track, len(rows), rank, nullity, consistent, sparse_res, mis))
    return report
