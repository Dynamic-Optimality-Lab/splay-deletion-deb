# Changelog

All notable changes to this repository are recorded here. Sealed exact results
are never edited in place; corrections create new versions.

## [0.1.9] - 2026-09-22 - SA-03 freeze (post-n7 WP-5 protocol; rules only, no candidates)

- `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3.md`: ratified amendment SA-03
  (Post-n7 Universal-Candidate Validation Protocol; SHA-256
  `BB407FAC46DB30FA58F8833E513152FC10182AC931AFD84DDB0C29B0217E25E1`),
  triggered after WP-4 completion with n7 legitimately revealed.
- Eras frozen: ERA-A pre-n7 labels immutable; all future IDs ERA-B POST_N7
  with n7 as revealed development data, never untouched.
- Fresh n=8 direct Pair-Access holdout: 32,718,400 exact checks on
  authoritative `R_8` without sealed `b_8*`; pass = finite n8 fact only
  (+ finite `b_8* <= b_H` upper certificate, never exact `b_8*`).
- `python/n8_holdout/` package (sweep + clean-room independent + n8 firewall
  `EMPTY`→`SET_FROZEN`→`UNLOCKED_ONCE` + freeze helpers); SA-02 n6/n7
  firewall left byte-identical. Machinery self-tested once with degenerate
  `H=0` vector (`b_H=23/14`) on EMPTY set: edge count exact, maxima 89/−23,
  primary↔independent agreement; H=0 REJECTED as required, never a hypothesis.
- UH-6 refined for ERA B only (`UH-6_PASS_FINITE_N8` at most); freeze
  contract, reveal protocol, multiplicity, adversarial separation,
  negative-branch discipline frozen.
- `prereg/wp5_sa03.yaml` (+ `.sha256`
  `FCE7F8C0A32F3590B3EFA7A6487330B7F11867DDF0D377D654E305ECA365BD73`).
- `schemas/`: 20 schemas (+ `wp5_post_n7_candidate_v0.1` with
  untouched-7 schema ban + `n8_pair_access_holdout_v0.1`).
- `WorkPlan.md` v0.1.7 FROZEN: spec stack + WP-5 semantics + UH-6 + n8
  holdout + charter + 20 schemas + four-spec seal set.
- `tests/test_sa03_freeze.py` (31/31: SA03-01..20 + SEP + UH3 + AGREE4).
  Fail-closed verified live: a hand-transcription slip in the recorded
  prereg hash was caught by SA03-20 and corrected from computed bytes.
- `Path.md`: SA-03 freeze entry; claim stays `FINITE_EXACT_BN_RESULTS`;
  NO WP-5 candidate synthesized (candidate set EMPTY).

## [0.1.8] - 2026-09-22 - WP-4 completion (affine exhaustion, ladder, C-ids, kernels; mining evidence only)

- `n7_status = PREVIOUSLY_REVEALED_AFTER_H-SA02-B-v1-final_FREEZE` ledgered;
  `H-SA02-B-v1`/`-final` bytes preserved; firewall gains additive
  `require_post_n7_label` gate (no existing behavior changed).
- Affine space: 9 primitive null directions, min support exactly 5 over Q
  (1941 subsets ≤4 all inconsistent; `min_support_exhaustion_log.json`);
  per-domain sparse results; 11 alternatives differ on development n6/n7.
- Global verdict: n456 + n4567 F-linear INCONSISTENT (rank 8 vs aug 9);
  proven-minimum triple witness (`mis_n456.json`); n6-vs-selection localized;
  zero identical-`DeltaF` conflicts.
- Atom ladder F-v0.1+A1 (14 atoms): selection-redundant, globally dead
  (104x30 rank 11 vs 12; no single-atom rescue; 12-row n6-internal witness).
- Cycles compared (`comparison_n4567.json`); `H-SA02-C-1`/`-C-2`
  POST-n7-frozen, globally tested (59/135 + 53/135 sat), both killed.
- Kernels complete (`K-v0.1-complete`): full transition checks n=2..5,
  (V,U) value sweeps; FULL_STATE PASS; every family necessary (transition
  failure from n=3, value failure at n≥4); schema-exact
  `smallest_n_failing` key added (legacy alias kept, schema untouched).
- `tests/test_wp4_gates.py` 26/26 (F01-D03, K01-K03, firewall, schema,
  determinism, sealed preservation). Claim stays `FINITE_EXACT_BN_RESULTS`.

## [0.1.6] - 2026-09-22 - SA-02 freeze (rules only; no fitting)

- `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md`: ratified amendment SA-02
  (Adaptive Cycle-Discovery Mining Track; SHA-256
  `79C58ED0278A6F81FE42685955C2D50EEF9A6744CCD0A701B6FE8DF96EE41CDF`),
  triggered by sealed WP-3 FCYCLE observation before WP-4 fitting.
- `WorkPlan.md` v0.1.6 FROZEN: normative stack base+SA-01+SA-02, two WP-4
  tracks (A control 0 rows / B n=4,5 FCYCLE 20 rows), charter + firewall,
  spec set + 18 schemas.
- `prereg/wp4_sa02.yaml` (+ `.sha256`
  `BDE98934623B8EDCE00369F0C426E0DFE1358F158A688BA1EA2D885628B3B826`):
  Track-A/B selection/validation/holdout, prohibited reads, version rules.
- `schemas/`: 18 schemas (16 + `wp4_dataset_manifest_v0.1` +
  `cycle_anatomy_v0.1`).
- `python/mining/holdout_firewall.py` + `tests/test_sa02_freeze.py`
  (23/23) + `tests/test_fpath_orientation.py` (15/15) +
  `math/fpath_orientation_note.md` (FPATH `U(source)+L-V(target)`; behaviour
  correct, names ambiguous; NO WP-3 reseal).
- `artifacts/audits/contamination_ledger.json`: previously known `b_7*`
  aggregates ledgered; detailed n7/n6 unread attested.
- `Path.md`: SA-02 freeze entry with trigger/starvation/Track-A/B/n7-known-vs-unread/hashes.

## [0.1.7] - 2026-09-22 - SA-02 discovery (Tracks A/B + validation + holdout; mining evidence only)

- `artifacts/cycle_anatomy/n{4,5,6,7}/`: canonical cycles with `sum_L==0`,
  `p*sum_a==q*sum_y`, `sum_a==q*k` exact (`n=4` 6/12, `n=5` 1/4, `n=6` 11/44
  after initial freeze, `n=7` 1/10 after final unlock-once); motifs compared.
- `python/mining/scalar_features.py` (F-v0.1, 16 state-only ints + vectors,
  mirror invariant) + `artifacts/features/n{2..7}/` staged (n=6 after initial,
  n=7 after final); `build_datasets.py` Track-A 0 rows / Track-B 20 FCYCLE rows.
- `python/mining/exact_linear.py`: Track-A rank0/null16 starved; Track-B rank7/
  null9 consistent dense `H_B_v1` (6-support rational), sparse `[-2,2]`≤2 best
  `4/5`; no floats; no nonlinear ladder (linear not exhausted).
- `H-SA02-B-v1` (`7B4079A6…`) → n=6 validation 84 rows max `5/1` FAIL →
  `H-SA02-B-v1-final` (`04BFACAD…`, same coeffs) → n=7 holdout once 10 rows max
  `139/35` FAIL untouched (`n7_unlock.json` once-only).
- `python/mining/kernel_ablation.py` track-separated: `FULL_STATE` PASS;
  ablations `KERNEL_VALUE_INSUFFICIENT` with smallest pairs.
- `THEOREM_MINING_REPORT.md` (A–M, mining only, ceiling
  `FINITE_EXACT_BN_RESULTS`); `tests/test_sa02_tracks.py` (34/34);
  `artifacts/audits/{holdout_firewall_audit,n7_unlock}.json` + ledger N6/N7
  reveals in order; firewall test-isolation fix ledgered (no normative change).
- `Path.md`: WP-4 `GATED_PASS` (mining evidence, no theorem) + hypothesis
  ledger (v1/v1-final FAILs preserved) + claim retained
  `FINITE_EXACT_BN_RESULTS`.

## [0.1.5] - 2026-09-20 - Plan frozen (v0.1.5)

- `WorkPlan.md` v0.1.1-v0.1.5: external-audit remediations (T0 gates,
  nonempty witnesses, append-only seal, FGAP rule, per-n data split, B06
  ownership, universal `b_H`, `b_H`/`b_n*` geometry split, eval contract,
  UH-3 feasibility, OG/UH tracks, BH01-BH05, holdout mask).
- `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md`: ratified amendment SA-01 rev.2.
- `schemas/`: 16 schemas (14 base + `eval_contract_v0.1` + `bh_feasibility`).
- `Path.md`: audit-remediation rounds 1-5 with line-level evidence.

## [0.1.0] - 2026-09-20 - WP-1 foundation (SPEC 00, 01, 02)

Added:

- `WorkPlan.md`: 6-phase implementation plan covering SPEC PHASE 00-18.
- `Path.md`: progress tracker mirroring `WorkPlan.md`.
- Frozen preregistration: `prereg/experiment.yaml`, `prereg/sizes.yaml`,
  `prereg/exact_contract.yaml`, `prereg/allowed_claims.md`,
  `prereg/forbidden_claims.md`.
- `IMPLEMENTATION_SPEC.md`: frozen normative contract (v0.1 extraction).
- `FORMAL_NOTES.md`: Phase-0 proof obligations T0-01..T0-14 with proofs.
- `external/MANIFEST.json`: literature ledger (L1/L2/L3 status + hashes).
- `schemas/`: 14 canonical JSON schemas.
- `crates/splay_model`: Rust exact tree/rotation/Splay/enumeration/encoding core.
- `python/reference`: transparent tuple-based Splay implementation + enumerator.
- `python/audit`: independent dict-based Splay implementation + array-based
  functional third implementation for n<=5 cross-checks.
- `python/reference/fixtures.json`: hand-worked oracle fixtures (n=1,2 fully;
  curated n=3 rotation cases).
- `tests/test_wp1.py`: WP-1 gate suite (M01-M06, E01-E03) plus canary tests.
- `scripts/run_phase00.ps1`, `run_phase01.ps1`, `run_phase02.ps1` (plus POSIX
  `.sh` counterparts): deterministic phase drivers with identified step logging.
- `artifacts/trees/n1..n8`: canonical tree universes with Catalan verification
  and SHA-256 seals.
