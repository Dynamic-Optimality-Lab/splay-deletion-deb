"""Extended-ladder MIS: smallest row set killing [F|A1] global linearity.

Same certificate method as global_obstruction.py, applied to the 30-column
extended system on n456. POST-n7-DEVELOPMENT diagnostic only.
Output: artifacts/hypotheses/mis_n456_extended.json
"""
import itertools
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining import holdout_firewall as firewall
from python.mining.atom_search import load_extended, EXT_ORDER
from python.mining.affine_exhaustion import sp_matrix, sp_vector


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def consistent(idxs, M, t):
    m = sp_matrix([M[i] for i in idxs])
    b = sp_vector([t[i] for i in idxs])
    return m.rank() == m.row_join(b).rank()


def main():
    firewall.hydrate_from_files()
    rows = load_extended([4, 5, 6])
    M = [r["vec"] for r in rows]
    t = [r["target"] for r in rows]
    n45 = [i for i, r in enumerate(rows) if r["label"].startswith("n=4") or r["label"].startswith("n=5")]
    rest = [i for i in range(len(rows)) if i not in n45]
    import sympy as sp
    B = [M[i] for i in n45]
    # Independent basis rows of the selection block.
    basis, cur = [], []
    for i in n45:
        trial = cur + [M[i]]
        if sp_matrix(trial).rank() > sp_matrix(cur).rank() if cur else any(v != 0 for v in M[i]):
            cur = trial
            basis.append(i)
        if len(basis) == sp_matrix(B).rank():
            break
    console_log("EXTMIS", "selection basis size=%d" % len(basis))
    Bt = sp_matrix([M[i] for i in basis]).T
    tB = [t[i] for i in basis]
    cands = []
    for j in rest:
        r = M[j]
        aug = Bt.row_join(sp_vector(r))
        if Bt.rank() != aug.rank():
            continue
        sol, params = Bt.gauss_jordan_solve(sp_vector(r))
        subs = {p: sp.Rational(0) for p in params}
        c = [sp.simplify(x.subs(subs)) if hasattr(x, "subs") else x for x in sol]
        implied = sum(ci * ti for ci, ti in zip(c, [sp.Rational(x.numerator, x.denominator) for x in tB]))
        if implied == sp.Rational(t[j].numerator, t[j].denominator):
            continue
        cands.append({"row": j, "support": [basis[i] for i, ci in enumerate(c) if ci != 0]})
    console_log("EXTMIS", "certificate witnesses: %d" % len(cands))
    best = None
    seeds = []
    for c in cands:
        seeds.append(c["support"] + [c["row"]])
    if not seeds:
        # No in-span mismatch: inconsistency rides on rank growth at n6.
        # Seed greedy shrink from the full set (deterministic order).
        seeds.append(list(range(len(rows))))
    for seed in seeds:
        w = list(seed)
        changed = True
        while changed:
            changed = False
            for x in list(w):
                trial = [y for y in w if y != x]
                if not consistent(trial, M, t):
                    w = trial
                    changed = True
                    break
        if best is None or len(w) < len(best):
            best = w
    # exact-minimum verification (feasible only for small witnesses).
    min_verified = True
    if len(best) <= 12:
        for k in best:
            if not consistent([x for x in best if x != k], M, t):
                min_verified = False
                break
    else:
        min_verified = False
    out = {"system": "n456 extended [F-v0.1|A1]",
           "n7_status": firewall.N7_STATUS,
           "label": "POST-n7-DEVELOPMENT diagnostic (NOT untouched)",
           "indices": sorted(best),
           "minimum_cardinality_verified": min_verified,
           "size": len(best),
           "rows": [{"label": rows[i]["label"],
                     "target": "%s/%s" % (t[i].numerator, t[i].denominator)} for i in sorted(best)]}
    with open(os.path.join(REPO, "artifacts", "hypotheses", "mis_n456_extended.json"),
              "w", encoding="utf-8") as f:
        json.dump(out, f, sort_keys=True, indent=2)
        f.write("\n")
    console_log("EXTMIS", "size=%d min_verified=%s" % (len(best), min_verified))
    for i in sorted(best):
        console_log("EXTMIS-ROW", "%s target=%s/%s" % (rows[i]["label"], t[i].numerator, t[i].denominator))


if __name__ == "__main__":
    main()
