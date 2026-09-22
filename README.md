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

## Experiment-0 tables A–E (sealed exact values; decimals display-only)

Fractions are exact `p/q`; parenthesized decimals are labeled display only,
never authoritative. Full evidence: `artifacts/seal/FINAL_RESULT.json`.

Table A — exact optima `b_n*` (sealed certificates, independent PASS):
n=2: 1/1 (1.0); n=3: 1/1 (1.0); n=4: 3/2 (1.5); n=5: 8/5 (1.6);
n=6: 8/5 (1.6); n=7: 23/14 (1.642857...).

Table B — reachable domain sizes `|R_n|` (diagonal-rooted BFS):
n=2: 4; n=3: 19; n=4: 196; n=5: 1764; n=6: 17424; n=7: 184041
(total 203448 states; edges `E_n = 2n|R_n|`).

Table C — canonical `b_n*` geometry maxima (U_max / V_max / forced):
n=2: 2/1/2; n=3: 5/2/5; n=4: 33/7/14; n=5: 144/21/42; n=6: 172/35/132;
n=7: 616/119/429 (forced = Catalan diagonals).

Table D — fresh universal `b_H=2/1` geometry maxima (U_2 / V_2 / forced):
n=2: 4/0/2; n=3: 10/1/5; n=4: 22/2/14; n=5: 38/3/42; n=6: 44/5/132;
n=7: 58/6/429 (`artifacts/potentials/n{n}/hypothesis_bH/`).

Table E — universal-hypothesis verdicts (all REJECTED; first failure UH-4):
H-0001 UPPER from n=5 (52/352/3300 upper n=5/6/7); H-0002 UPPER from n=4
(14/204/2028/31408); H-0003 UPPER from n=4 (same counts); H-0004 LOWER
from n=5 (3/40/471 lower); H-0005 LOWER from n=5 (2/36/520 lower);
H-0006 UPPER from n=3 (4/38/210/1694/16546). UH-5 counterexamples
preserved as supplementary evidence.

Sealed claim level: `FINITE_EXACT_BN_RESULTS` (no survivor, no proved
lemma, no proved unbounded family; P15 closed, P17 not activated,
Levy–Tarjan bridge not invoked).
