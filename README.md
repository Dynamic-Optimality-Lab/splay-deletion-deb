# SPLAY-AM-PD v0.1 — Exact Pair-Dynamics, Canonical Potential, and Theorem-Mining Experiment

Target problem: Sleator–Tarjan Dynamic Optimality Conjecture for bottom-up Splay,
via the Levy–Tarjan approximate-monotonicity bridge.

Research chain (frozen):

```text
exact finite paired game -> exact b_n* -> (U,V,G) -> critical paths/cycles
-> forced discrete derivatives -> structural law H
-> universal Pair Access Lemma -> approximate monotonicity
-> dynamic optimality
(or, on the negative branch: an explicit infinite unbounded witness family)
```

Style: deterministic, exact, non-statistical, certificate-first, fail-closed,
two-implementation verification. No floating-point value is authoritative.
Every finite claim terminates in an exact certificate.

## Current status

See `Path.md` (progress tracker, mirrors `WorkPlan.md` phase-for-phase) and
`artifacts/seal/FINAL_RESULT.json` once sealed. Truthful claim level at WP-1
completion: `FINITE_INFRASTRUCTURE_ONLY` at best; no theorem-level claim is made
before WP-6 proof gates pass.

## Repository layout (abridged; full map in WorkPlan.md)

```text
WorkPlan.md / Path.md        plan + progress tracker
IMPLEMENTATION_SPEC.md        frozen normative contract (v0.1 + SA-01 amendment v0.1.1)
FORMAL_NOTES.md              Phase-0 proof obligations T0-01..T0-14
prereg/                      preregistration (experiment, sizes, contract, claims)
external/                    frozen literature copies + SHA-256 manifest
math/                        definitions, theorem notes, proof-status ledger
schemas/                     16 canonical JSON schemas (14 base + 2 SA-01)
crates/                      Rust exact core (splay_model, pair_graph, exact_solver,
                             feature_core, cli)
python/                      reference impl, independent audit, mining, adversary
tests/                       gate suites per work phase
artifacts/                   raw/trees/transitions/reachability/candidates/
                             certificates/potentials/critical/features/kernels/
                             hypotheses/falsification/audits/logs/seal
scripts/                     phase drivers (run_phaseNN) + reproduce_all
```

## Quickstart (WP-1 gates)

```powershell
# Phase-0 foundation gate (SPEC 00)
.\scripts\run_phase00.ps1
# Reference Splay gate (SPEC 01): two-impl n<=6, triple n<=5 + canaries
.\scripts\run_phase01.ps1
# BST enumeration gate (SPEC 02): Catalan counts + canonical IDs, n=1..8
.\scripts\run_phase02.ps1
# Full WP-1 gate suite with evidence log
python tests\test_wp1.py
```

Requirements: Python >= 3.12 (validated on 3.13.7), Rust stable (see
`rust-toolchain.toml`). WP-1 has no third-party Python runtime dependencies;
`requirements-lock.txt` records this exactly.

## Cost and Splay conventions (frozen; see IMPLEMENTATION_SPEC.md)

- Keys `[n] = {1..n}`, inorder fixed. Root depth `0`.
- Access cost `c(T,x) = depth_T(x) + 1`, hence `1 <= c <= n`.
- Bottom-up Splay only: ZIG / ZIG-ZIG LL / ZIG-ZIG RR / ZIG-ZAG LR / ZIG-ZAG RL.
- Pair domain is diagonal-reachable `R_n` only. Unreachable pairs never enter
  solver or mining inputs.
