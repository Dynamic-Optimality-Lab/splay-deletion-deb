# Changelog

All notable changes to this repository are recorded here. Sealed exact results
are never edited in place; corrections create new versions.

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
