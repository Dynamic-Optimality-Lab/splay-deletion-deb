# THEOREM_MINING_REPORT.md — SPLAY-AM-PD v0.1 (SA-02 discovery, mining evidence only)

**Experiment:** `SPLAY-AM-PD-v0.1` | **Amendment:** SA-02 (v0.1.2) | **Plan:** v0.1.6
**Claim ceiling:** `FINITE_EXACT_BN_RESULTS` (this report proves no theorem).
**Status:** WP-4 SA-02 discovery complete (Tracks A/B + validation + holdout);
WP-5/6 pending. All statements below are labeled
`CERTIFIED FACT` / `FINITE OBSERVATION` / `HYPOTHESIS` / `HEURISTIC`.

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

*End — mining evidence only; fail-closed to claims.*
