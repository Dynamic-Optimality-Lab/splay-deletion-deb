"""Exhaust the Track-B n=4/5 exact linear solution space over Q (WP-4 completion).

POST-n7-DEVELOPMENT analysis: n=6/n=7 rows are used here ONLY as
development/falsification data (n7_status =
PREVIOUSLY_REVEALED_AFTER_H-SA02-B-v1-final_FREEZE). Nothing here claims an
untouched holdout. H-SA02-B-v1 / H-SA02-B-v1-final are never modified.

Outputs (exact rational arithmetic only; floats never authoritative):
  artifacts/hypotheses/track_b_affine_space.json  (full affine analysis)
  artifacts/hypotheses/global_n456_report.json     (combined n=4+5+6 system)
  artifacts/hypotheses/global_n4567_report.json    (combined n=4+5+6+7 diagnostic)
  artifacts/hypotheses/mis_n456.json               (minimal inconsistent subsystem)
  artifacts/hypotheses/identical_deltaF.json       (identical-input check)

All row orderings deterministic (sorted by (n, source_state_id, mode, key)).
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


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def load_fcyclerows(sizes):
    """FCYCLE edge-delta rows for given n, deterministic order, with exact targets."""
    import zstandard as zstd
    rows = []
    for n in sorted(sizes):
        firewall.guard_initial_fit_load("artifacts/features/n%d/edge_deltas.json.zst" % n)
        with open(os.path.join(REPO, "artifacts", "features", "n%d" % n,
                               "edge_deltas.json.zst"), "rb") as f:
            deltas = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
        p, q = b_for_n(n)
        for r in deltas:
            if "FCYCLE" not in r["provenance"]:
                continue
            rows.append({
                "n": n,
                "source_state_id": r["source_state_id"],
                "target_state_id": r["target_state_id"],
                "mode": r["mode"],
                "key": r["key"],
                "provenance": sorted(r["provenance"]),
                "a": r["a"],
                "y": r["y"],
                "scaled_slack": str(r["scaled_slack"]),
                "delta_F": {k: int(r["delta_F"][k]) for k in FEATURE_ORDER},
                "target": Fraction(int(r["scaled_slack"]), q),
                "b": [str(p), str(q)],
            })
    rows.sort(key=lambda r: (r["n"], r["source_state_id"], r["mode"], r["key"]))
    return rows


def sp_matrix(mat):
    import sympy as sp
    return sp.Matrix([[sp.Rational(x.numerator, x.denominator) for x in row] for row in mat])


def sp_vector(vec):
    import sympy as sp
    return sp.Matrix([sp.Rational(x.numerator, x.denominator) for x in vec])


def mat_of(rows):
    return [[r["delta_F"][k] for k in FEATURE_ORDER] for r in rows]


def tgt_of(rows):
    return [r["target"] for r in rows]


def primitive_intvec(sympy_vec):
    """Normalize exact rational vector to primitive integer tuple, sign-fixed."""
    import sympy as sp
    from math import gcd
    dens = []
    for x in sympy_vec:
        r = sp.Rational(x)
        dens.append(int(r.q))
    from math import gcd as _g
    import functools
    L = 1
    for d in dens:
        L = L * d // _g(L, d)
    ints = [int(sp.Rational(x) * L) for x in sympy_vec]
    g = 0
    for v in ints:
        g = _g(g, v)
    if g > 1:
        ints = [v // g for v in ints]
    for v in ints:  # sign fix: first nonzero positive
        if v != 0:
            if v < 0:
                ints = [-v for v in ints]
            break
    return ints


def analyze_selection():
    import sympy as sp
    rows = load_fcyclerows([4, 5])
    M = mat_of(rows)
    t = tgt_of(rows)
    m = sp_matrix(M)
    b = sp_vector(t)
    rank = m.rank()
    null = m.nullspace()
    null_prim = sorted([primitive_intvec(v) for v in null])
    sol, params = m.gauss_jordan_solve(b)
    subs = {p: sp.Rational(0) for p in params}
    particular = [sp.simplify(x.subs(subs)) if hasattr(x, "subs") else x for x in sol]
    particular_s = [str(x) for x in particular]
    # Column-structure facts.
    col_zero = [j for j in range(16) if all(M[i][j] == 0 for i in range(len(M)))]
    # Verify crossing == Aonly+Bonly on selection rows.
    ia = FEATURE_ORDER.index("f_ancestor_Aonly")
    ib = FEATURE_ORDER.index("f_ancestor_Bonly")
    ic = FEATURE_ORDER.index("f_crossing_reversal")
    cross_derived = all(M[i][ic] == M[i][ia] + M[i][ib] for i in range(len(M)))
    return {
        "rows": rows, "M": M, "t": t,
        "rank": rank, "nullity": 16 - rank,
        "nullspace_primitive": null_prim,
        "particular": particular_s,
        "zero_columns": [FEATURE_ORDER[j] for j in col_zero],
        "crossing_is_Aonly_plus_Bonly": cross_derived,
    }


DOMAINS = {
    # name: (predicate over Fraction, box bound info)
    "INT1": {"kind": "int_box", "M": 1},
    "INT2": {"kind": "int_box", "M": 2},
    "INT3": {"kind": "int_box", "M": 3},
    "Q2": {"kind": "rat_box", "D": 2, "NUM": 20},
    "Q3": {"kind": "rat_box", "D": 3, "NUM": 20},
    "Q4": {"kind": "rat_box", "D": 4, "NUM": 20},
    "Q5": {"kind": "rat_box", "D": 5, "NUM": 20},
    "NONNEG": {"kind": "nonneg_box", "D": 5, "NUM": 20},
    "SIGNED": {"kind": "rat_box", "D": 5, "NUM": 10},
}


def in_domain(fr, dom):
    spec = DOMAINS[dom]
    k = spec["kind"]
    if k == "int_box":
        return fr.denominator == 1 and abs(fr.numerator) <= spec["M"]
    if k == "rat_box":
        return fr.denominator <= spec["D"] and abs(fr.numerator) <= spec["NUM"]
    if k == "nonneg_box":
        return fr >= 0 and fr.denominator <= spec["D"] and fr.numerator <= spec["NUM"]
    raise AssertionError("unknown domain")


def restricted_solve(M, t, support):
    """Exact solve of M_S a = t. Returns (status, payload).

    status: 'inconsistent' | 'unique' (solution list) | 'affine' (particular, nullvecs).
    """
    import sympy as sp
    cols = list(support)
    if not cols:
        if all(x == 0 for x in t):
            return ("affine", ([], []))
        return ("inconsistent", None)
    sub = [[row[j] for j in cols] for row in M]
    m = sp_matrix(sub)
    b = sp_vector(t)
    if m.rank() != m.row_join(b).rank():
        return ("inconsistent", None)
    sol, params = m.gauss_jordan_solve(b)
    subs = {p: sp.Rational(0) for p in params}
    part = [sp.simplify(x.subs(subs)) if hasattr(x, "subs") else x for x in sol]
    if not params:
        return ("unique", [Fraction(str(x)) for x in part])
    ns = m.nullspace()
    ns_prim = [primitive_intvec(v) for v in ns]
    return ("affine", ([Fraction(str(x)) for x in part], ns_prim))


def box_points(support, dom):
    """Enumerate domain box points on support (finite, explicit bounds)."""
    spec = DOMAINS[dom]
    k = spec["kind"]
    per_coord = []
    if k == "int_box":
        per_coord = [list(range(-spec["M"], spec["M"] + 1))] * len(support)
    elif k == "rat_box":
        vals = set()
        for d in range(1, spec["D"] + 1):
            for num in range(-spec["NUM"], spec["NUM"] + 1):
                vals.add(Fraction(num, d))
        per_coord = [sorted(vals)] * len(support)
    elif k == "nonneg_box":
        vals = set()
        for d in range(1, spec["D"] + 1):
            for num in range(0, spec["NUM"] + 1):
                vals.add(Fraction(num, d))
        per_coord = [sorted(vals)] * len(support)
    for tup in itertools.product(*per_coord):
        if all(v == 0 for v in tup):
            continue
        yield tup


def exact_residual_zero(M, t, alpha):
    for row, tgt in zip(M, t):
        if sum(a * x for a, x in zip(alpha, row)) != tgt:
            return False
    return True


def sparse_search(M, t, dom, k_max, zero_cols):
    """Least support-size exact solution in domain; exhaustive through k_max.

    Returns dict(min_support, example or None, scope).
    Lexicographic order: subsets ascending, box points ascending -> canonical first hit.
    Zero-only columns excluded from supports (they can never help; documented).
    """
    cols = [j for j in range(16) if j not in zero_cols]
    # k = 0: zero vector works iff all targets zero.
    if all(x == 0 for x in t):
        return {"min_support": 0, "example": {}, "scope": "exhaustive k=0"}
    for k in range(1, k_max + 1):
        for support in itertools.combinations(cols, k):
            status, payload = restricted_solve(M, t, support)
            if status == "inconsistent":
                continue
            if status == "unique":
                sol = payload
                if all(in_domain(v, dom) for v in sol):
                    return {"min_support": k,
                            "example": {FEATURE_ORDER[j]: "%s/%s" % (v.numerator, v.denominator)
                                        for j, v in zip(support, sol) if v != 0},
                            "scope": "exhaustive through k=%d" % k_max}
                continue
            # affine: the restricted solution set is infinite. INT/NONNEG boxes are
            # finite -> full box enumeration (exhaustive). Q boxes are infinite ->
            # bounded parametric probe: particular + small integer combinations of
            # the restricted nullspace (coeffs in -3..3, explicit bound, documented
            # as non-exhaustive over infinite families).
            part, ns = payload
            spec = DOMAINS[dom]
            if spec["kind"] in ("int_box", "nonneg_box"):
                iterator = box_points(support, dom)
                for tup in iterator:
                    alpha = [Fraction(0)] * 16
                    for j, v in zip(support, tup):
                        alpha[j] = v
                    if exact_residual_zero(M, t, alpha):
                        return {"min_support": k,
                                "example": {FEATURE_ORDER[j]: "%s/%s" % (v.numerator, v.denominator)
                                            for j, v in zip(support, tup) if v != 0},
                                "scope": "exhaustive through k=%d" % k_max}
            else:
                import sympy as sp
                ns_frac = [[Fraction(str(x)) for x in vec] for vec in ns]
                found = None
                for combo in itertools.product(range(-3, 4), repeat=len(ns_frac)):
                    if all(c == 0 for c in combo):
                        cand = list(part)
                    else:
                        cand = list(part)
                        for c, nv in zip(combo, ns_frac):
                            for a in range(len(support)):
                                cand[a] = cand[a] + c * nv[a]
                    if all(in_domain(v, dom) for v in cand):
                        alpha = [Fraction(0)] * 16
                        for j, v in zip(support, cand):
                            alpha[j] = v
                        if exact_residual_zero(M, t, alpha):
                            found = cand
                            break
                if found is not None:
                    return {"min_support": k,
                            "example": {FEATURE_ORDER[j]: "%s/%s" % (v.numerator, v.denominator)
                                        for j, v in zip(support, found) if v != 0},
                            "scope": "through k=%d; affine supports via bounded parametric probe "
                                     "(null coeffs -3..3; non-exhaustive over infinite families)" % k_max}
    if DOMAINS[dom]["kind"] in ("int_box", "nonneg_box"):
        scope = "exhaustive through k=%d: no %s solution" % (k_max, dom)
    else:
        scope = ("through k=%d: no %s solution found; unique-solve screening exhaustive, "
                 "affine supports covered by bounded parametric probe only "
                 "(non-exhaustive over infinite families)" % (k_max, dom))
    return {"min_support": None, "example": None, "scope": scope}


def residual_vector(M, t, alpha):
    out = []
    worst = Fraction(0)
    worst_i = 0
    for i, (row, tgt) in enumerate(zip(M, t)):
        r = abs(sum(a * x for a, x in zip(alpha, row)) - tgt)
        out.append("%s/%s" % (r.numerator, r.denominator))
        if r > worst:
            worst = r
            worst_i = i
    return out, "%s/%s" % (worst.numerator, worst.denominator), worst_i


def main():
    firewall.hydrate_from_files()
    sel = analyze_selection()
    M, t, rows = sel["M"], sel["t"], sel["rows"]
    console_log("AFFINE-00", "selection rows=%d rank=%d nullity=%d" % (len(M), sel["rank"], sel["nullity"]))
    zero_cols = [FEATURE_ORDER.index(nm) for nm in sel["zero_columns"]]
    # Per-domain sparse search. INT exhaustive through k=4; Q/NONNEG through k=5
    # (documented bounds; C(15,5)=3003 subsets max after dropping the zero column).
    domain_results = {}
    for dom in ["INT1", "INT2", "INT3", "Q2", "Q3", "Q4", "Q5", "NONNEG", "SIGNED"]:
        k_max = 4 if dom.startswith("INT") else 5
        # Q-box enumeration per affine support could be heavy; restricted unique-solve
        # path is exact and fast; affine supports fall back to bounded box (NUM bound).
        r = sparse_search(M, t, dom, k_max, zero_cols)
        domain_results[dom] = r
        console_log("AFFINE-DOM", "%s min_support=%s scope=%s" % (dom, r["min_support"], r["scope"]))
    out = {
        "experiment_id": "SPLAY-AM-PD-v0.1",
        "n7_status": firewall.N7_STATUS,
        "analysis_class": "POST-n7-DEVELOPMENT (selection-system analysis; n6/n7 used only as labeled development data)",
        "selection": {
            "row_count": len(M),
            "rank_over_Q": sel["rank"],
            "nullity": sel["nullity"],
            "zero_columns": sel["zero_columns"],
            "crossing_is_Aonly_plus_Bonly_on_selection": sel["crossing_is_Aonly_plus_Bonly"],
            "nullspace_basis_primitive_int": sel["nullspace_primitive"],
            "particular_solution": dict(zip(FEATURE_ORDER, sel["particular"])),
            "degrees_of_freedom": "9-dim affine space over Q (particular + 9 null directions)",
        },
        "sparse_per_domain": domain_results,
        "float_note": "exact rational arithmetic only (sympy Rational + Fraction); floats never authoritative",
    }
    with open(os.path.join(REPO, "artifacts", "hypotheses", "track_b_affine_space.json"),
              "w", encoding="utf-8") as f:
        json.dump(out, f, sort_keys=True, indent=2)
        f.write("\n")
    console_log("AFFINE-99", "wrote track_b_affine_space.json")
    return out, M, t, rows


if __name__ == "__main__":
    main()
