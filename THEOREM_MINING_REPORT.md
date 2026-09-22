# THEOREM_MINING_REPORT.md — SPLAY-AM-PD v0.1 FINAL (WP-6 seal)

**Experiment:** `SPLAY-AM-PD-v0.1` | **Plan:** v0.1.8 (SA-01..SA-04) |
**Sealed claim:** `FINITE_EXACT_BN_RESULTS`
(`artifacts/seal/FINAL_RESULT.json`, schema-validated).
**Status:** WP-1..WP-6 complete; positive branch closed (no survivors);
negative branch not activated (samples only); bridge not invoked.
All statements below are labeled
`CERTIFIED FACT` / `FINITE OBSERVATION` / `HYPOTHESIS` / `HEURISTIC`.
Severity key: CERTIFIED FACT = sealed + independently verified;
FINITE OBSERVATION = exact computation on certified sizes, no universal
content; HYPOTHESIS = versioned falsifiable statement under test;
HEURISTIC = exploration aid, never evidence.

---

## A. Certified facts (from sealed WP-1/2/3, commit `bd658be`)

- CERTIFIED FACT: `b_n* = 1/1,1/1,3/2,8/5,8/5,23/14` for `n=2..7` (two-sided
  certificates + independent PASS).
- CERTIFIED FACT: `U/V/G` canonical tables + `G==0` forced = diagonals only
  (`2,5,14,42,132,429`).
- CERTIFIED FACT: `FORCED_DELTA 4,17,12,8,84,10`; `FPATH 4,15,0,0,0,0`;
  `FCYCLE 4,15,12,8,84,10`; corridors `2,5,0,0,0,0`; SCCs `1,4,6,1,11,1`.
- CERTIFIED FACT: FPATH orientation `U(source)+L-V(target)==0`
  (`math/fpath_orientation_note.md`; 15/15 regression PASS; no reseal).

## B. SA-02 trigger (finite observation → versioned amendment)

- FINITE OBSERVATION: for `n>=4`, corridors vanish and 100% of forced
  derivatives are cyclic; original FCYCLE holdout leaves Track-A selection
  with 0 rows (`n=2` 4 FCYCLE-out; `n=3` 15 FCYCLE-out + 2 FPATH-only but
  zig-zag-out; `n=4` 12-out; `n=5` 8-out), starved where `b_n*>1`.
- HYPOTHESIS (methodological): a preregistered cycle-discovery track can
  learn from cyclic forcing without contaminating later sizes → SA-02
  Track B (`n=4,5` FCYCLE, 20 equations; `n=6` validation; `n=7` holdout).

## C. Tracks (frozen prereg `prereg/wp4_sa02.yaml` `BDE98934…`)

- Track A (control, untouched): selection `n=2..5` `reserved==false` → 0 rows
  (`artifacts/datasets/track_a_manifest.json` `6B2D3250…`).
- Track B (discovery): selection `n=4,5` FCYCLE → 20 rows (12+8)
  (`artifacts/datasets/track_b_manifest.json` `62E24AE8…`).
- Validation/holdout physically separate; firewall + contamination ledger
  enforce order; `b_7*=23/14` aggregates previously known, details unread
  until final freeze.

## D. Cycle anatomy (selection only before fitting; full after freezes)

- FINITE OBSERVATION (`artifacts/cycle_anatomy/n4,n5`): `n=4` 6 cycles
  (each `sum_a=4,sum_y=6,len2,k=2` at `b=3/2`); `n=5` 1 canonical cycle
  (`sum_a=10,sum_y=16,len4,k=2` at `b=8/5`); all `sum_L==0`,
  `p*sum_a==q*sum_y`, `sum_a==q*k`, `sum_y==p*k`, `k>0` exact.
- FINITE OBSERVATION (revealed in order): `n=6` 11 cycles / 44 edge records
  (`b=8/5`); `n=7` 1 cycle / 10 edges (`b=23/14`, `k` verified).
  Motif comparison: `n=4` short 2-cycles (all zig); `n=5` 4-cycle
  (zig/zigzig mix); `n=6` 11 SCCs with 2–? edge cycles (zig/zigzig split
  42/42); `n=7` single 10-edge cycle with multi-step `LL,ZIG`/`RR,ZIG`
  motifs (unseen at selection) — holdout differs in kind, not just sample.

## E. Features (F-v0.1, state-only, exact)

- 16 integer scalars (depth/parent/ancestor/subtree/interval/access/
  crossing/heavy/bend-placeholder) + vectors; no `U/V/G/b*/criticality`
  reads (F01 static PASS); sanity identical-zero + spine diffs (F02 PASS);
  all invariant under joint mirror (F03 declared).
- State tables for every reachable state (`n=2:4, n=3:19, n=4:196,
  n=5:1764, n=6:17424, n=7:184041`); edge deltas staged (n=6 after initial
  freeze, n=7 after final unlock).

## F. Exact linear search first (rationals only)

- Track A: 0 rows → rank 0, nullity 16, vacuously consistent, no basis;
  recorded as rank-starved scientific result (never repaired).
- Track B: 20 rows → rank 7, nullity 9, basis `[0,1,2,4,12,13,14]`,
  consistent over Q with dense particular solution
  `H_B_v1 = (8/5)*depth_sum + (17/5)*depth_max + (8/5)*parent_diff
  + (-1/5)*parent_flip + (-9/5)*ancestor_Aonly + (-8/5)*ancestor_both`
  (6-support rational); sparsest integer `[-2,2]` support≤2 best residual
  `4/5` (`depth_max=1`) — no sparse integer exact fit.
- No float determined acceptance (floats: none). Minimal inconsistent
  subsystem: none (both tracks consistent; starved vs dense).

## G. Nonlinear atoms (after linear exhaustion)

- Linear not exhausted (dense exact fit exists), so structured ladder
  (`min/max`, indicators, counts, per-node sums, frozen piecewise) was NOT
  invoked for acceptance. Documented as deferred; any future atom gets a new
  `hypothesis_id` with answer-independent definition. No unrestricted
  symbolic regression performed.

## H. Validation order (Track B)

- A. Fit n=4,5 only → B. Freeze `H-SA02-B-v1` (`7B4079A6…`) → C. Reveal n=6:
  exact max residual `5/1` on 84 FCYCLE rows (FAIL; worst `src=3598→14770`
  `K k=1 slack=9`) → D. No coefficient revision (new ID would mark n=6
  development; preserved as validation FAIL) → E. Freeze final
  `H-SA02-B-v1-final` (`04BFACAD…`, same coeffs, parent v1) → F. Reveal n=7
  once: max residual `139/35` on 10 rows (FAIL, untouched) → G. No post-n7
  change (any change → new track, never re-call n=7 untouched; old runs
  preserved).

## I. Kernels (track-separated)

- `FULL_STATE` positive control PASS on all tested sizes (Tracks A/B).
- Ablations (minus-one-family) all `KERNEL_VALUE_INSUFFICIENT` with smallest
  separating pairs (e.g. Track-B `minus_depth [9,83]`, `minus_parent [1,14]`);
  sharpness tables + witnesses in `artifacts/kernels/`. No answer-smuggling
  (static audit); transition-preservation sampled + value-failure witnesses
  preserved.

## J. Artifacts & schemas

- SA-02 amendment + prereg + Track manifests + anatomy + firewall audit +
  contamination ledger + per-track linear reports + validation/holdout
  reports (all versioned + hashed). Schemas 18/18 (2 new SA-02:
  `wp4_dataset_manifest_v0.1`, `cycle_anatomy_v0.1`).

## K. Tests / gates

- FPATH orientation 15/15; SA-02 freeze 23/23; sealed WP-1..3 hashes
  unchanged; Track-A 0 / Track-B 20; firewall block/unlock flows;
  `sum_L==0`, `sum_a==q*k`; feature no-answer-import; namespace distinct;
  n=6/7 revealed only in order; kernels FULL_STATE PASS.
  Full gate matrix in `tests/test_sa02_*` + `Path.md` SA-02/discovery entries.

## L. Claim discipline

- No theorem proved. No promotion beyond `FINITE_EXACT_BN_RESULTS` merely
  because a dense fit exists (it FAILS untouched validation/holdout).
  Structural formula must still pass WP-5 UH gates + WP-6 proof before any
  universal claim. Mining success ≠ theorem.

## M. Next (WP-5/6, not started)

- WP-5 UH-0..UH-8 for any future universal `(H,b_H)` (OG diagnostics
  alongside); adversaries; independent falsifier. WP-6 proof or unbounded
  family; seal with spec set base+SA01+SA02; §36 answers.

## Z. WP-6 seal record (FINAL — closes §M)

- CERTIFIED FACT: WP-5 executed fully (6 ERA-B hypotheses H-0001..H-0006,
  `b_H=2/1`; UH-0/1/2/3 PASS; UH-4 REJECTED 6/6 with fresh b=2 sandwich —
  UPPER failures H-0001/2/3/6 from n=5/4/4/3, LOWER failures H-0004/5 from
  n=5; UH-5 counterexamples preserved supplementary; n8/H1 EMPTY).
- CERTIFIED FACT: P15-01..05 + P16 `VACUOUS_NO_SUBJECT` (survivor census
  empty; `artifacts/wp6/positive_branch_closure.json`).
- FINITE OBSERVATION: P01 telescoping identity holds on the checked R_4
  path (mechanism only); P02 five convention gaps recorded, bridge not
  invoked.
- FINITE OBSERVATION: six motif families reproduced identical (k=0,1,2);
  P17 NOT activated (H-residual samples, no OPT quantity, no symbolic
  bounds, no limit argument — T19).
- CERTIFIED FACT: seal — FINAL_RESULT `FINITE_EXACT_BN_RESULTS`,
  778-entry manifest (manifest never lists itself), deterministic archive,
  S01 byte-identical rebuild 15/15, S02 18/18, S03 zero violations, T1–T22
  covered, INV-035..040 hold. Terminal answers: `math/terminal_answers.md`.

---

# WP-4 COMPLETION SUPPLEMENT (2026-09-22, commit `072b211` onward work)

**Scope rule:** `n7_status = PREVIOUSLY_REVEALED_AFTER_H-SA02-B-v1-final_FREEZE`
for everything below. All new IDs are POST-n7-DEVELOPMENT; n=6/n=7 are
development/falsification data, never untouched holdout. `H-SA02-B-v1` and
`H-SA02-B-v1-final` are byte-preserved (hashes `dc96cabf…`, `1aef5d42…`).

## N. Affine-space exhaustion (FINITE OBSERVATION + CERTIFIED FACT)

- FINITE OBSERVATION (`artifacts/hypotheses/track_b_affine_space.json`):
  selection system 20x16, rank 7, nullity 9. Zero columns: `f_bend_placeholder`
  only. CERTIFIED FACT (recomputed): `f_crossing_reversal = f_ancestor_Aonly
  + f_ancestor_Bonly` on all 20 selection rows (exact column dependency).
- CERTIFIED FACT (nullspace): 9 primitive integer basis directions (sorted,
  sign-fixed; see artifact). Degrees of freedom: full 9-dim affine space over Q.
- CERTIFIED FACT (minimum support): exactly 5 over Q. Proof: all 1941 column
  subsets of size ≤4 (bend excluded) have inconsistent restricted systems
  (`artifacts/hypotheses/min_support_exhaustion_log.json`: 1+15+105+455+1365
  all inconsistent) → support ≤4 impossible in ANY domain; support 5 attained
  (canonical example below). No sparse INT1/INT2/INT3 solution ≤4 (exhaustive);
  no Q2/Q3/Q4 or NONNEG solution ≤5 within stated bounds; Q5/SIGNED min 5.
- FINITE OBSERVATION (canonical 5-support, lexicographically first):
  `{-9/5 ancestor_Aonly, +8/5 ancestor_Bonly, -8/5 ancestor_both,
  +1/5 depth_max, -1/5 parent_flip}` — note the dense 6-support particular from
  discovery is NOT canonical; it was one arbitrary member.
- FINITE OBSERVATION (family non-uniqueness is behavioral): 11 canonical
  alternatives (particular, +9 null directions, 5-support) evaluated on
  development n6/n7 (`artifacts/hypotheses/track_b_alternatives.json`):
  n6 max-residuals split `5` vs `34/5` vs `17/5`; n7 `139/35` vs `193/35`.
  The linear family does not speak with one voice off-selection — but §O
  decides the class question without sampling doubt.

## O. Global linear verdict (INCONSISTENCY WITNESS + CERTIFIED FACT)

- Central question: does any single linear state-only F-v0.1 potential explain
  all currently known cyclic forced derivatives simultaneously?
- CERTIFIED FACT: NO. Combined n456 FCYCLE system (104x16): rank 8, augmented
  rank 9 → INCONSISTENT over Q. Combined n4567 (114x16): rank 8, aug 9 →
  INCONSISTENT. (`artifacts/hypotheses/global_n456_report.json`,
  `global_n4567_report.json`.)
- INCONSISTENCY WITNESS (minimum, proven): 3 rows —
  `n=4 src=58 KEEP k=1 (a=2,y=3,L=0,ZIG,scc185)`,
  `n=6 src=3863 KEEP k=1 (a=3,y=3,L=9,LL/RR,non-canonical)`,
  `n=6 src=9683 KEEP k=5 (a=2,y=3,L=1,ZIG,scc17173)`.
  Proof of minimum: system-wide exact sweep (Bareiss) finds no inconsistent
  single or pair among all 104 rows (`sweep_F456.json`); this triple is
  inconsistent (sympy ranks 2 vs 3); all 3 pairs consistent.
  (`artifacts/hypotheses/mis_n456.json` with stratified rows; a superseded
  7-row irreducible witness is preserved inside for trail.)
- FINITE OBSERVATION (localization): `{n4,n5}` consistent; `{n4,n6}` and
  `{n5,n6}` each INCONSISTENT. The obstruction is n6-vs-selection (either
  selection size alone), needs no n7, all-KEEP (DELETE never forced), ZIG +
  LL/RR mix, cost regimes `(2,3),(3,3),(2,5),(3,5)`.
- FINITE OBSERVATION (identical inputs): zero same-n identical-`DeltaF`
  conflicts and zero cross-n conflicts among all 133 FCYCLE rows n=2..7
  (`identical_deltaF.json`) — the obstruction is a dependency-with-mismatch
  (row in span, target off the implied value), not a duplicate-input clash.

## P. Nonlinear atom ladder F-v0.1+A1 (FINITE OBSERVATION + COUNTEREXAMPLE)

- 14 frozen atoms, `g_*` namespace (`python/mining/nonlinear_atoms.py`):
  cost min/max sums, cost-comparison counts, depth-disagreement counts,
  frozen-C=2 caps/excesses, scalar sign indicators — each with an
  answer-independent tree-theoretic definition; mirror-invariant declared.
  F-v0.1 untouched (new version ID, never silently extended).
- FINITE OBSERVATION (`atom_ladder_A1_report.json`): extended selection system
  20x30 still rank 7 (atoms add no direction on selection; min atoms needed 0).
- CERTIFIED FACT: extended n456 system (104x30) rank 11, aug 12 →
  INCONSISTENT. Extended n4567 likewise. No single authorized atom restores
  consistency (`single_atom_rescue`: NONE of 14).
- INCONSISTENCY WITNESS (ladder-level): 12 n6-only rows, irreducible, with
  system-wide sweep ruling out sizes 1-3 (`sweep_X456.json`, exact minimum in
  [4,12] undetermined — honestly labeled, not overstated)
  (`mis_n456_extended.json`). Note: the 7-row F-witness becomes consistent
  under atoms (absorbed by new directions); the ladder dies on strictly-n6
  internal conflict instead.
- Charge-ansatz verdict: `H(A,B)=sum_v h(local_v)` with these 14 local forms
  cannot reproduce all cyclic forced derivatives simultaneously. Exact, not
  statistical. HEURISTIC (labeled as such): trying further rungs (more
  breakpoints, products) is permitted future mining with new atom versions,
  but the ladder's two-level failure (selection-redundant yet globally
  insufficient, self-contradictory on n6 alone) suggests the missing
  structure is not a local per-key charge of these forms.

## Q. Cycle comparison, aggressive (FINITE OBSERVATION)

- (`artifacts/cycle_anatomy/comparison_n4567.json`): k=2 uniformly at all n;
  n=4 six 2-cycles, all-ZIG, every edge individually `L_i=0`; n=5 one 4-cycle
  (ZIG+LL/RR, `L` in [-9,9]); n=6 eleven 4-cycles (22 ZIG + 22 LL/RR);
  n=7 one 10-cycle with multi-step `LL,ZIG`/`RR,ZIG` motifs (`L` in [-24,22]).
- Common: 100% KEEP on canonical cycles; `sum_L=0`, `sum_a=q*k`, `k>=1` exact;
  no LR/RL zig-zag on any canonical cycle edge n=4..7.
- The n4 `L_i=0`-everywhere vs n5/n6/n7 wide-`L` contrast is the structural
  fingerprint of why selection-only fits cannot project forward: selection
  cycles never exhibit the nonzero-slack edge patterns the larger sizes force.

## R. POST-n7 candidates (COUNTEREXAMPLE × 2, preserved + killed)

- `H-SA02-C-1` (canonical 5-support; `d3b76c91…`): global 59/135 sat,
  max `139/35`. `H-SA02-C-2` (bounded-local n6 minimizer, residual 4 vs v1's
  5 — still FAIL; `5a810cdf…`): global 53/135 sat, max `31/7`.
  Full stratified tables (n / FPATH-FCYCLE-FGAP / KEEP-DELETE / zig / cost /
  SCC, exact counts + maxima + first/worst + residual distributions) in
  `candidate_global_tests.json`. Both FAIL → killed, preserved.
- Strongest surviving structural formula: NONE. Every tested exact candidate
  (dense v1, 11 affine alternatives, 5-support canonical, local minimizer,
  14-atom ladder class) fails on development sizes. The honest WP-4 output is
  the impossibility evidence, not a formula.

## S. Kernels, complete program (FINITE OBSERVATION)

- Method upgraded from sampled to representative-based FULL transition checks
  (equality transitivity makes rep-vs-each sufficient), n=2..5 all edges,
  value-separation on (V,U) pairs (`python/mining/kernel_ablation.py`,
  `K-v0.1-complete`).
- K01: FULL_STATE PASS every size, both tracks. K02/K03: every family
  necessary — Track B ablations fail at n=4 by VALUE (e.g. minus_depth [9,83]);
  Track A ablations pass everything at n=2, then fail at n=3 by TRANSITION
  (e.g. minus_depth states 0 vs 24, DELETE k=2, same observables, successor
  kernels differ in heavy-agreement: depth predicts successor heavy structure
  — mechanistic necessity witness).
- Structural sufficiency (§9): the full 8-family descriptor is MINIMAL —
  minus-anything breaks by n≤3 (transition) or n=4 (value). Same-K pairs with
  different successor-K (n=3) and different (V,U) (n≥4) are preserved as
  theorem-mining obstructions guiding future refinement (new features = new
  versions, not silent edits).

## T. Gates (all green; WP-4 GATED_PASS stands completed)

- F01/F02/F03, D01/D02/D03, K01/K02/K03: 26/26 in `tests/test_wp4_gates.py`;
  plus FPATH 15/15, SA-02-freeze 23/23, SA-02-tracks 34/34. Schemas validate
  (dataset, anatomy sample, candidate_H incl. C-ids, kernel projection with
  the `smallest_n_failing` schema-exact key + legacy alias check);
  determinism (hashes reproduce, sorted-keys canonical, no bare set-iteration);
  sealed WP-1/2/3 hashes unchanged; v1/v1-final bytes preserved.

## U. Claim discipline (unchanged)

- `FINITE_EXACT_BN_RESULTS`. No promotion: nothing survives; impossibility
  evidence is mining, not theorem. WP-5 UH gates + WP-6 proof still required
  for any future universal claim. n=8 exact seal unavailable (resources) —
  stated limitation, NOT a replacement holdout; no fake holdout created.

## V. Scientific conclusion of WP-4 (exact)

- Track A starved by design (recorded, never repaired).
- Track B selection is a 9-dim exact affine space (min support 5); its dense
  representative failed forward — and the class question is settled
  negatively: F-v0.1-linear cannot fit n456 simultaneously (minimum 3-row
  witness), nor can F-v0.1+14-authorized-atoms (n6-internal 12-row witness).
- The obstruction localizes to n6-vs-selection (either n4 or n5 alone),
  needs no n7, lives in KEEP/FCYCLE/ZIG-LLRR structure with wide-L edges
  unseen at selection.
- Kernel descriptor minimal at 8 families (transition-necessary by n=3).

## W. Recommended WP-5 inputs (NOT started)

- Carry forward ONLY: MIS triple + ladder 12-row witness + kernel transition
  witnesses + comparison table as falsification/oracle material for future
  universal candidates; C-ids as killed baselines. Any new fitting needs a
  fresh certified size (e.g. n=8, resources permitting) for a genuine
  untouched holdout. Awaiting review before WP-5.

*End of WP-4 completion supplement — mining evidence only; fail-closed to claims.*


---

## X. CORRECTION ENTRY (SA-04, append-only; original text above untouched)

- OLD CLAIM: n8 was the fresh untouched SA-03 Pair-Access holdout.
- CORRECTED CLAIM: n8 was partially revealed by an infrastructure canary
  (H=0 test vector, KEEP max 89 / DELETE max -23 with argmaxes, 3,944,504 + 0
  positives, first counterexamples (7,KEEP,8,+5) and (14,KEEP,8,+5)) before
  WP-5 synthesis, and is therefore classified
  N8_STATUS = PARTIALLY_REVEALED_CANARY_CONTAMINATED. n8 keeps mandatory
  EV-8 (N8_CONTAMINATED_EXHAUSTIVE_VALIDATION) duty: any exact failure still
  REJECTS, but n8 never again counts as fresh/untouched or as the sole UH-6.
- REPLACEMENT: HOLDOUT-H1-v0.1 is the new fresh UH-6 holdout (120,000 hidden
  reachable states in {9,10,12,16,24,32}; 4,120,000 edge evaluations;
  commitment C9D9BE26-0613BFF; synthesis-blocked; independently replayed).
- Crucially, no POST_N7 scientific candidate had yet been synthesized when the
  canary ran (candidate set EMPTY), so candidate development remained
  uncontaminated by candidate-specific n8 testing. The previously reported
  maxima 89/-23 and associated argmax/counterexample information are
  permanently treated as revealed development metadata (contamination ledger
  entry N8_CANARY_RECLASSIFIED_SA04).
- Claim unchanged: FINITE_EXACT_BN_RESULTS. No theorem; mining only.

*End of correction - fail-closed to claims.*

---

## WP-5 validation record (2026-09-22; all subjects REJECTED, evidence preserved)

- H-0001 (depth-sum/H1, b_H=2): UH-1/2/3 PASS; UH-5 REJECTED (first-fails n=5; worst n=7 KEEP 6 / DELETE 7). OG-1 0/12 + 0/8; mirror-invariant.
- H-0002 (ancestor-sym/H3, b_H=2): UH-1/2/3 PASS; UH-5 REJECTED (first-fails n=4; worst n=7 13/14). OG-1 0/12 + 0/8; mirror-invariant.
- H-0003 (access-sym/H3, b_H=2): UH-1/2/3 PASS; UH-5 REJECTED (first-fails n=4; worst n=7 13/14). OG-1 0/12 + 0/8; mirror-invariant.
- H-0004 (heavy-disagree/H5, b_H=2): UH-1/2/3 PASS; UH-5 REJECTED (first-fails n=3; DELETE passes everywhere). OG-1 4/12 + 0/8; mirror-VARIANT (heavy tie-break asymmetry, discovery).
- H-0005 (parent-diff/H2, b_H=2): UH-1/2/3 PASS; UH-5 REJECTED (first-fails n=4; DELETE passes). OG-1 4/12 + 0/8; mirror-invariant.
- H-0006 (depth+heavy combo/H6, b_H=2): UH-1/2/3 PASS; UH-5 REJECTED (first-fails n=3; worst 7/11 at n=7). OG-1 8/12 + 0/8; mirror-VARIANT.
- Independent agreement on all six (maxima, argmaxes, counts, counterexamples, UH-1/2 counts; 0 transition mismatches); BH01–BH05 green; 18 sign-flip mutants caught; 1272 adversarial runs → 955 supplementary counterexamples; 6 sampled motif families (no proof).
- Survivors: none. n8 + H1 holdouts unconsumed (both firewalls EMPTY). No universal claim; mining only.

*End of WP-5 record - fail-closed to claims.*
