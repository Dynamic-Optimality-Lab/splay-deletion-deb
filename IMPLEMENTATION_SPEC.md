# IMPLEMENTATION_SPEC.md — Frozen Normative Contract (v0.1 extraction + SA-01 rev.2)

**Source:** `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.md` (SHA-256
`29070d39f54d40c3f8b1ccdde8b588545749dc3f60e8949c430036a0185f1565`),
as ratified-amended by `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md`
(amendment SA-01 rev.2).
**Status:** FROZEN. Any change requires a new experiment version.
**Scope of this file:** complete normative extraction. The full v0.1 text and
the SA-01 amendment file are authoritative for prose; this file is the
machine-checkable freeze of every definition, bound, gate, and rule the code
enforces. In case of conflict, the amendment file governs hypothesis
validation and v0.1 governs all else.

---

## 1. Key universe

`[n] = {1, 2, …, n}`, `n ≥ 1`. Distinct totally ordered integer keys. No
insertion, deletion, duplicate, failed search, or weighted key in the primary
experiment. (INV-001)

## 2. Tree universe

`T_n` = all BSTs with inorder exactly `1..n`. Shape determines the labeled BST
uniquely. `|T_n| = C_n = (2n)! / ((n+1)!·n!)` (Catalan). Every enumerator
verifies the emitted count equals `C_n` exactly. (INV-002, INV-007)

## 3. Depth and cost (frozen)

Root depth `0`: `d_T(x)` = edges on root→x path. (INV-003)
Access cost `c(T,x) = d_T(x) + 1` (nodes on the pre-splay search path), hence
`1 ≤ c(T,x) ≤ n`. Rotations are not separately charged. No alternative cost
may mix into a primary run. (INV-004)

## 4. Bottom-up Splay (frozen, INV-005)

`S_x(T)`: let `v` be node `x`. While `v` is not root, with parent `p` and
grandparent `g`:
ZIG (no `g`): single rotation at `p` (right if `v` left child, left if right).
ZIG-ZIG LL (`v`,`p` both left): rotate-right at `g`, then at `p`.
ZIG-ZIG RR (both right): rotate-left at `g`, then at `p`.
ZIG-ZAG LR (`v` right of `p`, `p` left of `g`): rotate-left at `p`, rotate-right at `g`.
ZIG-ZAG RL: rotate-right at `p`, rotate-left at `g`.
After every rotation and final Splay assert: parent/child consistency, no
cycle, exactly `n` nodes, inorder `1..n`, `x` is root. (INV-006)

## 5. Sequence cost

`T_i = S_{x_i}(T_{i-1})`; `Splay(X,T) = Σ c(T_{i-1},x_i)`;
`Splay(∅,T) = 0`.

## 6. Subsequence

`Y ⪯ X`: position-based deletion subsequence, order preserved, repeats allowed
and position-distinguished.

## 7. Pair dynamics (frozen)

Pair state `s = (A,B)`, `A,B ∈ T_n`. Diagonal `Δ_n = {(T,T)}`; every legal
execution begins at a diagonal state. (INV-009)
KEEP `K_x(A,B) = (S_xA, S_xB)` with `a(e) = c(A,x)`, `y(e) = c(B,x)`. (INV-012, INV-014)
DELETE `D_x(A,B) = (S_xA, B)` with `a(e) = c(A,x)`, `y(e) = 0`. (INV-013, INV-015)
Edge identity `(source_state_id, mode, key)`, `mode ∈ {0 KEEP, 1 DELETE}`.
Deterministic edge order `K(1..n), D(1..n)`; global order by
`(source_state_id, mode, key)`. (INV-008)
Path decoding: `X(P)` = all edge keys, `Y(P)` = KEEP-edge keys only;
`Σa = Splay(X,T)`, `Σy = Splay(Y,T)` exactly. (INV-016, INV-017)

## 8. Reachable domain (frozen)

Authoritative domain `R_n` = pairs reachable from `Δ_n` by finite KEEP/DELETE
paths (INV-010). `R_n` is forward closed under all `2n` actions (INV-011).
No unreachable pair may enter a constraint system, solver input, or mining
statistic. `ratio_empty_path_allowed = false`; empty future allowed in `V`.
(INV-018, INV-019)

## 9. Regret, slack, overhead

`w_b(e) = y − b·a`; `ℓ_b(e) = b·a − y = −w_b(e)`; path sums `W_b`, `L_b`.
`b` valid for `n` iff every diagonal-rooted finite path has `L_b(P) ≥ 0`.
`b_n* = sup_{nonempty P from Δ} Σy/Σa = inf{b : valid}`. (INV-020)
Sanity `1 ≤ b_n* ≤ n` (`BN_SANITY_FAIL` otherwise). (INV-025)
No finite-attainment assumption: TRANSIENT / CYCLIC / MIXED.
Integer scale at `b = p/q` reduced: `L_{p,q}(e) = p·a − q·y ∈ ℤ`. (INV-021)
No float decides an exact sign/equality. (INV-022)

## 10. Canonical potentials

`U_b(s) = inf_{Δ⇝s} L_b`; `V_b(s) = sup_{s⇝*} W_b` (empty continuation allowed,
so `V ≥ 0`); `G_b = U_b − V_b ≥ 0`; FORCED ⟺ `G = 0` by exact integer equality.
(INV-028, INV-029)
`V` Bellman: `V_b(s) = max(0, max_e[−ℓ_b(e) + V_b(s')])`, hence
`V(s') − V(s) ≤ ℓ_b(e)`.
Feasible set `F_{n,b}`: `H ≥ 0`, `H = 0` on diagonals, `H(s') − H(s) ≤ ℓ_b(e)`.
Extremal theorem: `V ≤ H ≤ U` for all `H ∈ F`; `V, U ∈ F` at valid `b`.

## 11. Critical objects and forcing

Below-optimum failures: TRANSIENT negative path vs CYCLIC negative cycle
(recorded separately). At certified optimum only zero-slack objects:
transient zero-slack diagonal path; reachable zero-slack directed cycle.
Criticality subtype `TRANSIENT / CYCLIC / MIXED / CLASSIFICATION_INCOMPLETE`;
top-level status `EXACT_BN_TRANSIENT / EXACT_BN_CYCLIC / EXACT_BN_MIXED /
EXACT_BN_CRITICALITY_INCOMPLETE` (namespaces never blurred).
Zero-slack path theorem: every edge forced `H(s')−H(s) = ℓ_b(e)`, every
path state forced. Zero-slack cycle theorem: every cycle edge forced
(states need not be). Provenance `FPATH / FCYCLE / FGAP / VBELLMAN /
UBELLMAN → FORCED_DELTA` with `ΔH(e) = ℓ_b(e) = L_{p,q}(e)/q`. (INV-030)
`FGAP(e)` iff `G(s)=0 ∧ G(t)=0 ∧ U_scaled(t)−U_scaled(s)=L(e)`.
Rationality `b_n* ∈ ℚ`; denominator bound `q ≤ n·|R_n|` (usable only after
T0-13 PROVED+REVIEWED, T0-GATE-A).

## 12. Exact certificate for `b_n*`

Upper: integer `P ≥ 0`, `P = 0` on diagonals,
`P(s')−P(s) ≤ L_{p,q}(e)` on every reachable edge. (INV-023)
Lower transient: nonempty diagonal path, legal edges, `sum_a > 0`,
`p·sum_a − q·sum_y = 0`. Lower cyclic: diagonal prefix + nonempty directed
cycle, `sum_a_cycle > 0`, zero scaled slack. (INV-024)
Seal ⟺ valid upper AND (valid transient OR valid cyclic witness).
Negative `b`: `NEGATIVE_PATH` / `NEGATIVE_CYCLE` certificates with exact
scaled slack `< 0`. Negative reachable cycle invalidates candidate `b`.
(INV-026, INV-027)

## 13. Canonical encoding

Shape grammar `EMPTY='.'`, `NODE='(LEFT RIGHT)'` (e.g. `(..)`, `((..).)`).
`tree_id` = ASCII-lexicographic sort order of shape codes.
`pair_id = A_id·C_n + B_id` (stable incl. unreachable pairs); dense
`reachable_index` from ascending sort of reachable `pair_id`s.

## 14. Outcome taxonomy (exact strings)

`EXACT_BN_TRANSIENT`, `EXACT_BN_CYCLIC`, `EXACT_BN_MIXED`,
`EXACT_BN_CRITICALITY_INCOMPLETE`, `REACHABILITY_MISMATCH`,
`TREE_ENUMERATION_MISMATCH`, `SPLAY_SEMANTICS_MISMATCH`, `BN_SANITY_FAIL`,
`CANDIDATE_DISCOVERY_INCOMPLETE`, `UPPER_CERTIFICATE_FAIL`,
`LOWER_CERTIFICATE_FAIL`, `CANONICAL_POTENTIAL_FAIL`,
`INDEPENDENT_VERIFICATION_FAIL`, `RESOURCE_LIMIT_NO_CLAIM`.

## 15. Phase-0 theorems and T0 gates

T0-01 path-to-(X,Y) correspondence; T0-02 path costs equal Splay costs;
T0-03 fixed-n path formulation; T0-04 `1 ≤ b_n* ≤ n`; T0-05 valid b iff
normalized pair potential exists; T0-06 U/V definitions and Bellman
inequalities; T0-07 `V ≤ H ≤ U`; T0-08 U,V feasible at valid b; T0-09
zero-slack path forcing; T0-10 zero-slack cycle forcing; T0-11 walk
decomposition; T0-12 rationality; T0-13 denominator bound; T0-14 upper +
zero-slack lower certificate implies `b_n* = p/q`. Proofs: FORMAL_NOTES.md.
T0-GATE-A: T0-13 PROVED+REVIEWED before `q ≤ n·|R_n|` use. T0-GATE-B: all
T0-01..T0-14 PROVED+REVIEWED before any Phase-06 seal; no `EXACT_BN_*`
otherwise.

## 16. Hypothesis validation (SA-01 rev.2, decisive)

Two tracks. OG-1..OG-3 (`b_n*` derivatives, `b_n*` sandwich, corridors):
diagnostics, never `REJECTED` alone. UH-0 well-defined, UH-1 identity on
every certified diagonal (nonzero rejects from the universal track;
additive-overhead uses another class/ID), UH-2 `H ≥ 0` on every certified
state (any negative value rejects; arbitrary-`n` proof is UH-9), UH-3
`b_H ≥ b_n*` exact per certified `n` (FAIL rejects immediately with reused
transient/cyclic witness logic incl. minimal `k` + `repeat_count`),
UH-4 `b_H`-sandwich with recomputed tables, UH-5 KEEP/DELETE at `b_H`,
UH-6 held-out, UH-7 independent implementation, UH-8 adversarial, UH-9
universal symbolic proof (only theorem gate). UH-3 suite BH01–BH05.
`H` is state-only `(A,B,n)`, versioned immutable, `n`-independent constants,
no black-box predictors. (INV-031..INV-034)

## 17. Mandatory test IDs (spec §19; BH01–BH05 added by SA-01)

M01–M06, E01–E03, T01–T03, R01–R04, B01–B06, U01–U03, V01–V03, G01–G02,
C01–C05, F01–F03, D01–D03, K01–K03, H01–H05, A01–A02, P01–P02, S01–S03,
BH01–BH05. No mandatory test may be deleted without a new experiment version.

## 18. Invariants INV-001..INV-040 (assert in code)

001 key set exactly 1..n; 002 inorder 1..n; 003 root depth 0; 004
`c=depth+1`; 005 bottom-up Splay only; 006 `x` root after Splay; 007
canonical-shape tree IDs; 008 `pair_id=A_id·C_n+B_id`; 009 executions begin
at diagonal; 010 foundational domain `R_n`; 011 forward closure under 2n
actions; 012 KEEP splays both; 013 DELETE splays A only; 014 KEEP y=c(B,x);
015 DELETE y=0; 016 path A-cost = Splay(X,T); 017 path y-cost = Splay(Y,T);
018 empty future allowed in V; 019 empty path excluded from b-ratio;
020 b rational p/q in exact stage; 021 scaled slack `p·a−q·y`; 022 no float
decides exactness; 023 upper certificate required; 024 lower certificate
required; 025 `1≤b_n*≤n`; 026 negative reachable cycle invalidates b;
027 optimum cycles have zero slack; 028 U/V/G only after `b_n*` seal;
029 forced means exact U=V; 030 forced derivative needs provenance; 031
features state-only unless diagnostic-labeled; 032 H versioned immutable;
033 discovery code cannot edit certificates; 034 falsifier independent of
discovery H; 035 final b universal for theorem claim; 036 finite
experiments prove nothing about arbitrary n; 037 counterexamples
preserved; 038 failed hypotheses preserved; 039 sealed artifacts include
input hashes; 040 claims generated only from verified artifacts.

## 19. Stops, claims, seal

STOP-01..STOP-16 halt the size-run immediately and are recorded, never
silently repaired. Claim levels (exactly 7): `FINITE_INFRASTRUCTURE_ONLY`,
`FINITE_EXACT_BN_RESULTS`, `FINITE_THEOREM_MINING_ONLY`,
`CANDIDATE_H_SURVIVES_FINITE_TESTS`, `UNIVERSAL_PAIR_ACCESS_LEMMA_PROVED`,
`DYNAMIC_OPTIMALITY_PROVED`, `DYNAMIC_OPTIMALITY_DISPROVED`.
`FINAL_RESULT.json` carries `normative_spec_set` (v0.1 + v0.1.1-SA01 hashes)
plus the single true claim level.
