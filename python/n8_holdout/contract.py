"""Frozen n=8 holdout contract constants (SA-03, normative values only).

No candidate logic lives here. TEST_VECTOR_ID marks the degenerate H=0
machinery self-test vector: it is NOT a hypothesis, never enters
artifacts/hypotheses/ or any ledger, and exists only inside test code.
"""
import json
import os

N8 = 8
CATALAN_C8 = 1430
R8_SIZE = 2044900
N8_EDGE_CHECKS = 2 * N8 * R8_SIZE  # 32,718,400

# Sealed exact b_n* for UH-3 prechecks (n=2..7 have certificates; n=8 does not).
SEALED_B_STAR = {
    2: (1, 1), 3: (1, 1), 4: (3, 2), 5: (8, 5),
    6: (8, 5), 7: (23, 14),
}

# Deterministic edge order: KEEP keys 1..n, then DELETE keys 1..n.
KEEP, DELETE = 0, 1

# Sealed artifact paths (relative to repo root).
TABLES_DIR = "artifacts/transitions/n8"
REACH_DIR = "artifacts/reachability/n8"
FORWARD_FILE = "forward.bin.zst"
REACH_FILE = "reachable.json.zst"

# Expected sealed summary hashes (pinned; SA03-18 re-verifies).
EXPECTED_FORWARD_SHA256 = "7c2d8c5d9309da09f6a5f01f8ca0883337825288092e9b6b849a3a84da7cfa5d"
EXPECTED_INVERSE_SHA256 = "3f686c289467510569a83adad472c5d82bf1f0421945e51ad2bc0a2c002a3d20"
EXPECTED_REACHABLE_SHA256 = "d6f5e920180cc9ba335a47b7f8a58358af58d8aa49efa233d7caecec88757647"

TEST_VECTOR_ID = "TEST-VECTOR-H0 (machinery self-test only, never a hypothesis)"

# Counterexample preservation policy (SA-03.8 step 10): lex-first 16
# positive-residual counterexamples per mode + exact counts + maxima.
PRESERVED_COUNTEREXAMPLES_PER_MODE = 16


def uh3_feasibility(p_H, q_H):
    """Exact UH-3 precheck for a frozen b_H against sealed b_n* (n=2..7).

    Returns list of per-n records {n, b_H, b_n_star, comparison, verdict}.
    Pure integer cross-multiplication; no floats. n=8 excluded by design
    (b_8* unsealed).
    """
    from math import gcd
    assert q_H > 0 and gcd(p_H, q_H) == 1, "b_H must be reduced with q_H>0"
    records = []
    for n in sorted(SEALED_B_STAR):
        p_n, q_n = SEALED_B_STAR[n]
        ok = p_H * q_n >= p_n * q_H
        records.append({
            "n": n,
            "b_H": {"p": str(p_H), "q": str(q_H)},
            "b_n_star": {"p": str(p_n), "q": str(q_n)},
            "comparison": "p_H*q_n >= p_n*q_H -> %s" % ok,
            "verdict": "PASS" if ok else "FAIL",
        })
    return records


def load_bn_certificate_b(n, repo_root):
    """Cross-check a sealed certificate value (aggregate read, always allowed)."""
    with open(os.path.join(repo_root, "artifacts", "certificates", "n%d" % n,
                           "bn_certificate.json"), encoding="utf-8") as f:
        cert = json.load(f)
    return int(cert["b"]["p"]), int(cert["b"]["q"])
