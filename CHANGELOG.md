# Changelog

All notable changes to this repository are recorded here. Sealed exact results
are never edited in place; corrections create new versions.

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
