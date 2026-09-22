"""Exact search over [F-v0.1 | A1 atoms] (POST-n7-DEVELOPMENT, no untouched claims).

Stages:
  N1: n45 extended system (20 x 30): rank, consistency, sparse-per-domain.
  N2: n456 extended system (104 x 30): consistency = does the ladder rescue global linearity?
  N3: n4567 extended diagnostic (114 x 30).
  N4: residual vectors of any exact n45 atom-solution on n6/n7 (development).
Output: artifacts/hypotheses/atom_ladder_A1_report.json
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
from python.mining.nonlinear_atoms import ATOM_NAMES, ATOM_VERSION
from python.mining.affine_exhaustion import (
    sp_matrix, sp_vector, primitive_intvec, residual_vector, in_domain, DOMAINS,
)


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


EXT_ORDER = list(FEATURE_ORDER) + list(ATOM_NAMES)


def load_extended(sizes):
    import zstandard as zstd
    rows = []
    for n in sorted(sizes):
        firewall.guard_initial_fit_load("artifacts/features/n%d/edge_deltas.json.zst" % n)
        firewall.guard_load("artifacts/features/n%d/edge_deltas.json.zst" % n)
        with open(os.path.join(REPO, "artifacts", "features", "n%d" % n,
                               "edge_deltas.json.zst"), "rb") as f:
            deltas = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
        with open(os.path.join(REPO, "artifacts", "features", "n%d" % n,
                               "edge_atom_deltas.json.zst"), "rb") as f:
            ad = {(r["source_state_id"], r["mode"], r["key"]): r["delta_G"]
                  for r in json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))}
        p, q = b_for_n(n)
        for r in deltas:
            if "FCYCLE" not in r["provenance"]:
                continue
            g = ad[(r["source_state_id"], r["mode"], r["key"])]
            vec = [int(r["delta_F"][k]) for k in FEATURE_ORDER] + [int(g[k]) for k in ATOM_NAMES]
            rows.append({
                "label": "n=%d src=%d %s k=%d" % (n, r["source_state_id"], r["mode"], r["key"]),
                "vec": vec, "target": Fraction(int(r["scaled_slack"]), q),
            })
    return rows


def main():
    firewall.hydrate_from_files()
    rep = {"atom_version": ATOM_VERSION, "atom_names": ATOM_NAMES,
           "n7_status": firewall.N7_STATUS,
           "label": "POST-n7-DEVELOPMENT (no untouched claims)"}
    # N1: selection extended.
    rows45 = load_extended([4, 5])
    M45 = [r["vec"] for r in rows45]
    t45 = [r["target"] for r in rows45]
    import sympy as sp
    m = sp_matrix(M45)
    b = sp_vector(t45)
    rank, aug = m.rank(), m.row_join(b).rank()
    rep["N1_selection_extended"] = {"rows": len(M45), "cols": len(EXT_ORDER),
                                    "rank_over_Q": rank, "nullity": len(EXT_ORDER) - rank,
                                    "consistent_over_Q": rank == aug}
    console_log("ATOM-N1", "rows=%d rank=%d aug=%d consistent=%s" % (len(M45), rank, aug, rank == aug))
    if rank == aug:
        sol, params = m.gauss_jordan_solve(b)
        subs = {p: sp.Rational(0) for p in params}
        part = [sp.simplify(x.subs(subs)) if hasattr(x, "subs") else x for x in sol]
        rep["N1_selection_extended"]["particular"] = dict(zip(EXT_ORDER, [str(x) for x in part]))
        # Sparse check: does an exact solution use any atom at all? Find min atom-count
        # solution: iterate atom-subsets by size with F-columns free (exact restricted solve).
        f_idx = list(range(16))
        a_idx = list(range(16, 30))
        found = None
        for na in range(0, 3):
            for acomp in itertools.combinations(a_idx, na):
                cols = f_idx + list(acomp)
                sub = [[row[j] for j in cols] for row in M45]
                ms = sp_matrix(sub)
                bs = sp_vector(t45)
                if ms.rank() != ms.row_join(bs).rank():
                    continue
                s2, p2 = ms.gauss_jordan_solve(bs)
                sbs = {p: sp.Rational(0) for p in p2}
                pv = [sp.simplify(x.subs(sbs)) if hasattr(x, "subs") else x for x in s2]
                # Check the F-part coincides with an exact F-only solution? Just record coeffs.
                found = {"n_atoms": na, "atom_cols": [EXT_ORDER[j] for j in acomp],
                         "coeffs": dict(zip([EXT_ORDER[j] for j in cols], [str(x) for x in pv]))}
                break
            if found is not None:
                break
        rep["N1_selection_extended"]["min_atoms_needed"] = found
        console_log("ATOM-N1", "min atoms needed: %s" % (found["n_atoms"] if found else None))
    # N2/N3 need n6/n7 atom deltas (development builds happen outside; check presence).
    for tag, sizes in (("N2_n456", [4, 5, 6]), ("N3_n4567", [4, 5, 6, 7])):
        try:
            rows = load_extended(sizes)
        except FileNotFoundError as e:
            rep[tag] = {"status": "SKIPPED (atom deltas not built: %s)" % e}
            continue
        M = [r["vec"] for r in rows]
        t = [r["target"] for r in rows]
        m = sp_matrix(M)
        b = sp_vector(t)
        rank, aug = m.rank(), m.row_join(b).rank()
        rep[tag] = {"rows": len(rows), "rank_over_Q": rank, "nullity": len(EXT_ORDER) - rank,
                    "consistent_over_Q": rank == aug,
                    "label": "POST-n7-DEVELOPMENT diagnostic (NOT untouched)"}
        console_log("ATOM-%s" % tag[:2], "rows=%d rank=%d aug=%d consistent=%s" % (len(rows), rank, aug, rank == aug))
    with open(os.path.join(REPO, "artifacts", "hypotheses", "atom_ladder_A1_report.json"),
              "w", encoding="utf-8") as f:
        json.dump(rep, f, sort_keys=True, indent=2)
        f.write("\n")
    console_log("ATOM-99", "wrote atom_ladder_A1_report.json")


if __name__ == "__main__":
    main()
