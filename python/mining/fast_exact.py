"""Exact integer (Bareiss) consistency checks + system-wide small-subset sweeps.

Bareiss fraction-free elimination: exact over Z, fast for small systems.
Used to prove rigorous lower bounds on minimum-inconsistent-subsystem size:
if no inconsistent pair/triple exists system-wide, any MIS has size >= 4.
"""
import itertools
import json
import os
import sys
from fractions import Fraction

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)


def bareiss_rank(mat):
    """Rank of integer matrix via fraction-free Bareiss elimination."""
    M = [list(map(int, row)) for row in mat]
    m = len(M)
    if m == 0:
        return 0
    n = len(M[0])
    det_prev = 1
    rank = 0
    prow = 0
    for col in range(n):
        piv = None
        for i in range(prow, m):
            if M[i][col] != 0:
                piv = i
                break
        if piv is None:
            continue
        M[prow], M[piv] = M[piv], M[prow]
        for i in range(prow + 1, m):
            for j in range(col + 1, n):
                M[i][j] = (M[i][j] * M[prow][col] - M[i][col] * M[prow][j]) // det_prev
            M[i][col] = 0
        det_prev = M[prow][col]
        prow += 1
        rank += 1
        if prow == m:
            break
    return rank


def consistent_int(rowvecs, targets_num, targets_den):
    """Exact consistency of integer rows with fractional targets.

    Scales each equation by its denominator (exact): D_i * (row . a) = N_i.
    """
    aug = [list(r) + [targets_num[k] ] for k, r in enumerate(rowvecs)]
    # Scale: multiply row k by den_k -> integer augmented matrix; rank compare
    # of coefficient part vs augmented part.
    coef = []
    augm = []
    for k, r in enumerate(rowvecs):
        d = targets_den[k]
        coef.append([v * d for v in r])
        augm.append([v * d for v in r] + [targets_num[k]])
    return bareiss_rank(coef) == bareiss_rank(augm)


def sweep_small(rows_M, rows_tnum, rows_tden, max_size, label):
    """System-wide sweep for inconsistent subsets up to max_size. Returns hits."""
    n = len(rows_M)
    hits = []
    for size in range(1, max_size + 1):
        found_this_size = []
        for sub in itertools.combinations(range(n), size):
            M = [rows_M[i] for i in sub]
            tn = [rows_tnum[i] for i in sub]
            td = [rows_tden[i] for i in sub]
            if not consistent_int(M, tn, td):
                found_this_size.append(list(sub))
                break  # existence per size is enough for the lower bound
        print("[SWEEP-%s] size=%d inconsistent_exists=%s" % (label, size, bool(found_this_size)),
              flush=True)
        if found_this_size:
            hits.append((size, found_this_size[0]))
            break
    return hits
