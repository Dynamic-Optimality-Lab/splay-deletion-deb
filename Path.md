# Path.md — Implementation Tracker for SPLAY-AM-PD v0.1 (mirrors WorkPlan.md exactly)

**Experiment:** `SPLAY-AM-PD-v0.1` | **Plan:** `WorkPlan.md` (WP-1…WP-6 ← SPEC 00–18, §§0–36)
**Repo:** https://github.com/Dynamic-Optimality-Lab/splay-deletion-deb
**Rule (task-critical, never forgotten):** as implementation moves forward, *every* step is documented here — what was implemented, with what evidence, and **whether it follows WorkPlan.md or not, with deep detail exactly like WorkPlan.md** (same phase structure, same file/code/benchmark granularity). Deviations, if any, get their own dated entry with cause, impact, and corrective versioning. Failed hypotheses, counterexamples, and stopped runs are preserved, never overwritten.
**Status convention per WP phase:** `PENDING` (not started) / `IN_PROGRESS` (underway) / `GATED_PASS` (all gates green) / `GATED_FAIL` (a named failure label emitted) / `BLOCKED` (waiting on a dependency) / `DEVIATED` (off-plan — requires deviation entry).

---

## Step 0 — Clone, clear-check, deep study, plan creation (2026-09-20) ✅ DONE

**What was done (deep detail):**
1. Cloned `https://github.com/Dynamic-Optimality-Lab/splay-deletion-deb` into workspace `Splay-Wtv/splay-deletion-deb`. Evidence: `git log --oneline` → single commit `f122c99 Initial commit`; `git ls-files` → `LICENSE` only; `git status` → clean; `git branch -a` → `main` + `origin/main` only.
2. Previous-results clearing check: probed for `artifacts/`, `WorkPlan.md`, `Path.md`, any code/caches — all `Test-Path … → False`. Only `LICENSE` (MIT, Dynamic Optimality Lab 2026) exists. **Conclusion: nothing to delete; the "only new results after the changes" guarantee holds vacuously at plan time.** Recorded in `WorkPlan.md §0`. No files were deleted, no history rewritten — so nothing could have been silently lost.
3. Deep-studied the full frozen spec (`SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.md`, §§0–36, PHASE 00–18, T1–T22, INV-001–INV-040, full test matrix, §31 checklist, §33 Experiment-0 bundle, §34 tables, §36 purpose questions) end-to-end before writing any plan. Verified key quantitative anchors: Catalan counts 1,2,5,14,42,132,429,1430; pairs `C_n²`; edges `E_n=2nR_n`; cost `c=depth+1`; edge order `K(1..n),D(1..n)`; `pair_id=A_id·C_n+B_id`; sanity `1≤b_n*≤n`; denominator bound `q≤n|R_n|`; certificate = upper feasible potential + zero-slack path/cycle witness + independent verifier; discovery `n=2..5` / validation `n=6` / held-out `n=7`; H-GATE-0..9 ladder; 7 claim levels.
4. Created `WorkPlan.md` (6 phases WP-1…WP-6, coverage matrix SPEC 00–18 → WP, per-phase scope/files/code-how/model-benchmarks/anti-overfitting, global charter §9, cross-cutting rules §10) and this `Path.md`. Both written into the repo (`splay-deletion-deb/WorkPlan.md`, `splay-deletion-deb/Path.md`).
5. No implementation code written yet; no artifacts produced; no gates run. No AI-driven semantic change: cost/reachability/encoding untouched; no rounding; no hypothesis mutation (none exist yet); no kernel defined; no finite-evidence promotion; no counterexample exists to suppress.

**Follows WorkPlan.md?** YES — exactly. This step *is* `WorkPlan.md §0` (pre-work verification) executed verbatim: clone → list → clear-check → study → plan. No deviation. Next: WP-1 begins (Step 1 below).

**Evidence:** git outputs + `Test-Path` results quoted above (re-runnable: `git log --oneline -5; git ls-files; Test-Path artifacts` in repo dir).
**Plan commit:** `24c6adb` on `main` (2026-09-20) — `WorkPlan.md` + `Path.md` committed and pushed to `origin/main`; working tree clean. Standing instruction from owner: commit + push whenever a unit of work is done — applied here and to be applied going forward.

---

## Audit remediation — WorkPlan.md v0.1.1 (2026-09-20) ✅ DONE

**What was done (deep detail):** the owner supplied an external audit verdict checked against the exact frozen spec at `/mnt/data/SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.md` (SHA-256 `29070d39f54d40c3f8b1ccdde8b588545749dc3f60e8949c430036a0185f1565`). Verdict: mathematical architecture PASS, 19→6 coverage PASS, but not freeze-ready — 4 blockers, 4 clarifications, 1 typo, 1 recommendation. All 10 items were patched into `WorkPlan.md` (now revision v0.1.1, stamped in its header) with no research-architecture change:

1. **BLOCKER — append-only preservation (`WorkPlan.md` §0 + §8 seal):** replaced the gate-passing commit rule with the frozen-spec rule: every pipeline run (failed gates, counterexamples, invalid candidates, mutation failures, stops) is preserved with hashes; only gate-passing artifacts enter the sealed set; a failed gate never authorizes erasure; logs append-only; at seal, unexpected scientific artifacts cause audit failure or manifest-with-status, never deletion. Verified: `WorkPlan.md:17` (`append-only artifact rule`), `WorkPlan.md:171` (seal wording).
2. **BLOCKER — T0 gates (`WorkPlan.md` §3 + §4 + §12):** added frozen `T0-GATE-A` (T0-13 PROVED+REVIEWED before `q ≤ n·R_n` use) and `T0-GATE-B` (all T0-01..T0-14 PROVED+REVIEWED before any Phase-06 `b_n*` seal; no `EXACT_BN_*` while any T0 UNPROVED/BLOCKED); WP-2 may build infra but cannot seal without them. Verified: `WorkPlan.md:59`, `WorkPlan.md:87` (T0-GATE-A), `WorkPlan.md:212-213` (§12 acceptance).
3. **BLOCKER — nonempty witnesses (`WorkPlan.md` §4):** TRANSIENT witness must begin at a diagonal, contain ≥1 edge, use legal edges, `sum_a > 0`, `p*sum_a − q*sum_y = 0` (`ratio_empty_path_allowed = false`); CYCLIC witness must be a nonempty cycle with `sum_a_cycle > 0` plus diagonal prefix. Verified: `WorkPlan.md:88`.
4. **BLOCKER — Splay freeze boundary (`WorkPlan.md` §3):** `splay_model` semantics fully implemented, cross-checked and frozen in WP-1; WP-2 tabulates/optimizes only, never alters Splay or cost without a new experiment version. Verified: `WorkPlan.md:65`.
5. **CLARIFICATION — status namespace (`WorkPlan.md` §1 + §4):** `criticality_subtype` (`TRANSIENT`/`CYCLIC`/`MIXED`/`CLASSIFICATION_INCOMPLETE`) vs `top_level_status` (`EXACT_BN_*`) never blurred. Verified: `WorkPlan.md:36`, `WorkPlan.md:88`.
6. **CLARIFICATION — FGAP algorithm (`WorkPlan.md` §5):** `FGAP(e)` iff `G(s)=0` AND `G(t)=0` AND `U_scaled(t) − U_scaled(s) = L(e)`; only then `FGAP` + `FORCED_DELTA=true` + `Delta_H_scaled=L(e)`; endpoints-`U=V` alone insufficient. Verified: `WorkPlan.md:107`.
7. **CLARIFICATION — per-`n` data scope (`WorkPlan.md` §6 + §9):** frozen split DATA GENERATION (all certified `n`: full `F-v0.1` table over every `s ∈ R_n`, kernel ablation every certified `n`) / SELECTION (`n=2..5`) / VALIDATION (`n=6`) / HELD OUT (`n=7`). Verified: `WorkPlan.md:131`, §9 item 2.
8. **CLARIFICATION — B06 ownership (`WorkPlan.md` §2 table + §4 + §5):** WP-2 rejected-`b` negatives are diagnostics only and do NOT discharge B06; B06 is discharged in WP-3 (Spec Phase 08, frozen `b⁻` rule). Verified: `WorkPlan.md:45`, `WorkPlan.md:93`, `WorkPlan.md:113`.
9. **TYPO — claim levels (`WorkPlan.md` §8 + this file):** `8` → `7`; the listed set is unchanged and correct. Verified: `WorkPlan.md:163`; `Path.md` Step 0 item 3 corrected alongside.
10. **RECOMMENDED — one exact `b` per H (`WorkPlan.md` §7):** each `H-*.json` freezes `b_hypothesis: {p, q}` + `b_is_universal_candidate: true`; `E_K`/`E_D` use that same `b` for every tested `n` (per-size `b_n*` stays in WP-3/WP-4 discovery only). Verified: `WorkPlan.md:145`, `WorkPlan.md:149`.

**Follows WorkPlan.md?** YES — this remediation changes the plan itself per owner direction + external audit; it is recorded here with item-by-item line evidence. No execution deviation (no implementation exists yet to deviate).

**Collateral truthfulness note (not part of the audit):** the repo working tree currently holds *uncommitted* partial WP-1 scaffold from the interrupted 2026-09-20 implementation start (`README.md`, `CHANGELOG.md`, `CITATIONS.md`, `.gitignore`, `external/papers/` with downloaded L2/L3 PDFs). Those files are NOT covered by this commit; WP-1 remains `PENDING` and its Path section still reads NOT YET CREATED/WITTEN until the phase resumes and completes its gates. Nothing here alters that status.

---

## Audit remediation round 2 — WorkPlan.md v0.1.2 (2026-09-20) ✅ DONE

**What was done (deep detail):** the owner supplied a second external audit verdict, rechecked against the frozen spec (SHA-256 still `29070d39f54d40c3f8b1ccdde8b588545749dc3f60e8949c430036a0185f1565`). Verdict: all previous 10 findings fixed; all 56 mandatory test IDs present; but one new MAJOR mathematical issue + 7 smaller items before freeze. All 8 were patched (plan now v0.1.2, header-stamped), no research-architecture change:

1. **MAJOR — universal-`b_H` vs optimum-`b_n*` geometry split (`WorkPlan.md` §7):** the canonical sandwich for a universal hypothesis `(H,b_H)` must use `U_{b_H},V_{b_H}` recomputed at that same `b_H` (new artifact `artifacts/potentials/n{n}/hypothesis_bH/{U_bH,V_bH}.json.zst`, independently re-verified), never the WP-3 `U_{b_n*},V_{b_n*}` tables unless `b_H=b_n*` — testing one against the other mixes two Bellman problems and can falsely reject a valid universal potential. Frozen architecture now stated: WP-3/4 `b_n*`-geometry is the discovery microscope; WP-5 tests `(H,b_H)` at one fixed `b_H`; WP-6 proves it. Candidates split into **optimal-geometry hypotheses** vs **universal Pair-Access hypotheses**.
2. **MAJOR/spec-level — H-GATE-3 scope (SA-01, `WorkPlan.md` §7):** exact `b_n*` forced-derivative agreement stays a rejection gate for optimal-geometry hypotheses but is discovery evidence (not a rejection gate) for universal hypotheses with `b_H > b_n*`, which carry extra slack `ℓ_{b_H}(e) = ℓ_{b_n*}(e) + (b_H − b_n*)·a(e)`. Recorded as PROPOSED SPEC AMENDMENT SA-01: requires ratification in a new spec version before downgrading any gate; until ratified, both geometries are computed/reported separately and no universal hypothesis is marked `REJECTED` solely on a `b_n*`-derivative mismatch without a `b_H`-geometry violation (tension flagged in the ledger).
3. **ERROR — negative-endpoint wording (`WorkPlan.md` §1):** now reads "disproves approximate monotonicity and hence — via Levy–Tarjan equivalence after convention audit — disproves dynamic optimality for Splay."
4. **REQUIRED — WP-1 suite scope (`WorkPlan.md` §3):** reference+independent exhaustive through `n≤6`; third structurally independent slow functional implementation (`reference/functional_splay.py`) exhaustive through `n≤5`; required primitives now explicitly list `find_path`, `compute_depth`, `validate_bst`; M03–M04 benchmark text updated to match.
5. **REQUIRED — status spelling (`WorkPlan.md` §2 table + §4):** `UPPER/LOWER_CERTIFICATE_FAIL` written as the two exact statuses `UPPER_CERTIFICATE_FAIL`, `LOWER_CERTIFICATE_FAIL`.
6. **AMBIGUITY — schema extension (`WorkPlan.md` §7):** supersedes round-1 item 10 as implemented — `b_hypothesis`/`b_is_universal_candidate` do NOT go into `H-*.json`; the frozen `candidate_H.schema.json` is followed exactly and the universal-`b` fields live in versioned companion `H-*.eval_contract.json` (`EC-v0.1`); any future schema change means explicit schema/spec versioning.
7. **MINOR — notation:** `q ≤ n·R_n` → `q ≤ n·|R_n|` (3 sites: §1 contract, §3 T0-GATE-A, §4 discovery), `E_n=2nR_n` → `E_n=2n|R_n|` (§10); Step 0 item 3 of this file updated likewise.
8. **MINOR — exact filenames (`WorkPlan.md` §3):** `external/papers/` now lists `L1_sleator_tarjan_1985.pdf`, `L2_levy_tarjan_1907.06310v3.pdf`, `L3_chmel_et_al_2607.18498.pdf`; `math/` lists the five exact theorem-note filenames.

**Follows WorkPlan.md?** YES — plan correction per owner direction + external audit, recorded here with line-level evidence. No execution deviation (implementation still pending).

---

## WP-1 — Foundation, frozen contract & reference Splay + BST universe (SPEC 00, 01, 02) — status: `PENDING`

**Scope per WorkPlan.md §3:** freeze L1/L2/L3 + spec + prereg (`experiment.yaml`, `sizes.yaml`, `exact_contract.yaml`, allowed/forbidden claims, `prereg_sha256.txt`); `FORMAL_NOTES.md` T0-01..T0-14 + `proof_status.json`; scaffold §13 layout; pin `rust-toolchain.toml`/`Cargo.lock`/`requirements-lock.txt`; Python transparent reference + independent auditor + hand fixtures + cost/rotation canaries; canonical BST enumeration + Catalan + independent enumerator.
**Files (WorkPlan §3 list):** NOT YET CREATED — pending: `IMPLEMENTATION_SPEC.md`, `FORMAL_NOTES.md`, `prereg/*`, `external/*`, `math/*`, `schemas/*.schema.json` (14), `crates/splay_model/src/*`, `python/reference/*`, `python/audit/independent_*`, `artifacts/trees/n{n}/*`, `scripts/run_phase00-02.sh`, logs.
**Code + how (WorkPlan §3):** NOT YET WRITTEN — planned: Rust pointer-BST rotations + 5-case `splay` with invariant asserts (semantics frozen here, per plan v0.1.1); Python immutable-tuple reference (primitives include `find_path`, `compute_depth`, `validate_bst`) vs pointer-dict independent audit vs third slow functional implementation (`n≤5`); `l`-recursive generator → ASCII-sort `tree_id`; inorder-rank reconstruction; exact Catalan check; root-key-interval second enumerator; exhaustive two-impl agreement through `n≤6` (per plan v0.1.2).
**Model training:** NONE per plan — nothing trained, nothing to report.
**Benchmarks/gates:** M01–M06 (M03–M04: two-impl through `n≤6`, triple through `n≤5`, per plan v0.1.2), E01–E03 — NOT YET RUN. No `FOUNDATION_NOT_FROZEN` / `SPLAY_SEMANTICS_MISMATCH` / `TREE_ENUMERATION_MISMATCH` emitted (no run to fail).
**Follows WorkPlan.md?** N/A yet (not started) — adherence will be judged entry-by-entry once Step 1 begins. No deviation.
**Next action:** Step 1 — freeze sources + prereg + scaffold + pin deps → gate 00; then reference Splay + canaries → gate 01; then enumeration → gate 02. Each sub-step gets its own dated Path entry with file list + test output + adherence verdict before moving on.

---

## WP-2 — Exact dynamics: transitions, reachability, discovery & certification of b_n\* (SPEC 03, 04, 05, 06) — status: `PENDING`

**Scope per WorkPlan.md §4:** `n·C_n` transition tables + inverse conservation; BFS `R_n` + parents + closure + independent audit; HiGHS LP proposals (`authoritative=false`) + `q≤nR_n` rational reconstruction (after T0-13 PROVED); integer-only two-sided seal + subtype + independent verifier.
**Files:** NOT YET CREATED — pending: `crates/{pair_graph,exact_solver,cli}/*`, `python/reference/{pair_graph,solve_small,verify_small}.py`, `python/audit/{verify_transition_table,verify_reachability,verify_bn_certificate,verify_no_float_seal}.py`, `artifacts/{transitions,reachability,candidates,certificates}/n{n}/*`, `scripts/run_phase03-06.sh`.
**Code + how:** NOT YET WRITTEN — planned per WorkPlan §4 (table lookups, BFS order + re-sort, LP→convergents→Farey pipeline, label-correcting exact solver, zero-slack path/cycle search, big-int fallback, canonical-hash discipline).
**Model training:** NONE per plan (LP = quarantined proposer, not a model) — nothing trained.
**Benchmarks/gates:** T01–T03, R01–R04, B01–B05 — NOT YET RUN (rejected-`b` negative diagnostics preserved separately; B06 is discharged in WP-3, per plan v0.1.1). No failure labels emitted.
**Follows WorkPlan.md?** N/A yet. Entry Dependency: BLOCKED on WP-1 `GATED_PASS` (needs frozen Splay + trees + T0-13 status). No deviation.
**Next action:** begin only after WP-1 gates pass; sizes executed in order 2→7 (+8 stretch as resources allow); each `n` gets a per-size Path sub-entry (counts, `p/q`, subtype, witness hashes, verifier PASS/FAIL).

---

## WP-3 — Canonical potentials & critical geometry (SPEC 07, 08) — status: `PENDING`

**Scope per WorkPlan.md §5:** exact `U^Z/V^Z/G^Z` + forced states (`G==0` exact) + Bellman witnesses; zero-reduced graph + transient corridors + SCC cycles + `FORCED_DELTA` provenance union + trajectories; frozen `b⁻` diagnostic (midpoint or 1/2 rule) with separate NEGATIVE_PATH/CYCLE objects.
**Files:** NOT YET CREATED — pending: `canonical_potentials.rs` extension, `verify_uv.py`, `verify_critical_objects.py`, `artifacts/{potentials,critical}/n{n}/*`, `scripts/run_phase07-08.sh`.
**Code + how:** NOT YET WRITTEN — planned per WorkPlan §5 (super-source/sink shortest paths, inverse-table reverse generation filtered by `R_n`, exact `r_P`, lexicographic canonical reps, SCC preservation, trajectory emission).
**Model training:** NONE per plan — tables only.
**Benchmarks/gates:** U01–U03, V01–V03, G01–G02, C01–C05, B06 (discharged here via frozen `b⁻` diagnostic, per plan v0.1.1) — NOT YET RUN. No `CANONICAL_POTENTIAL_FAIL` emitted.
**Follows WorkPlan.md?** N/A yet. Dependency: BLOCKED on WP-2 sealed `b_n*` per `n` (INV-028). No deviation.
**Next action:** per-`n` Path sub-entries (`max U/V/G`, `#forced`, `#FORCED_DELTA`, `#SCCs` — the §22 summary row) once WP-2 seals.

---

## WP-4 — State-only features + forced-derivative mining + kernel ablation (SPEC 09, 10, 11) ⭐ — status: `PENDING`

**Scope per WorkPlan.md §6:** versioned `F-v0.1` state-only features (depth/parent/ancestor/subtree/rank/interval/access-path/crossing/heavy/bend + vectors + mirror declarations + hand tests); exact `ΔF` vs `ΔH=L/q` datasets; sparse exact combination + structured-atom searches with versioned coefficient domains + basis/inconsistency analysis + stratification; PC-style kernels (value-separation + transition-preservation + ablation + sharpness table + full-state control). Quarantine: mining never writes certificates.
**Files:** NOT YET CREATED — pending: `crates/feature_core/src/*` (10 modules), `python/mining/*` (9 scripts), `artifacts/{features,kernels,hypotheses}/…`, mining-report skeleton, `scripts/run_phase09-11.sh`.
**Code + how (incl. model specifics):** NOT YET WRITTEN — planned per WorkPlan §6/§9: discovery equations `n=2..5`; domains `ℤ[−M,M]→ℚ_{den≤D}→nonneg→signed` as new search versions; ranking `(count, residual, complexity, cross-n)`; `R²` secondary only; minimal-inconsistent-subsystem preservation; kernel whitelist + static audits.
**Resultant benchmarks:** NONE YET — planned: satisfaction counts, max residuals, rank/nullity, separation/preservation verdicts, stratified tables.
**Brutal anti-overfitting (ENTIRELY different benchmarks):** NOT YET EXECUTED — planned per WorkPlan §9: held-out `n=6/7` (10–100× larger, unseen shapes/SCCs), held-out strata (FCYCLE/DELETE/zig-zag), derivative-not-scalar target, independent re-implementation (WP-5), large-`n` adversaries (WP-5), out-of-domain panel (WP-5), mutation controls (WP-5); `CROSS_N_STABLE` only after untouched-size survival; post-holdout edits → new IDs.
**Follows WorkPlan.md?** N/A yet. Dependency: BLOCKED on WP-3 (`FORCED_DELTA` + `U/V/G` required). No deviation.
**Next action:** freeze `F-v0.1` definitions note before any code; then features → deltas → searches → kernels, each with Path sub-entries (schema hash, static-audit result, discovery tables).

---

## WP-5 — Candidate H synthesis + independent falsification + adversarial search (SPEC 12, 13, 14) ⭐ — status: `PENDING`

**Scope per WorkPlan.md §7:** versioned state-only `H` freeze (frozen H schema followed exactly; universal-`b` fields in companion `H-*.eval_contract.json` per plan v0.1.2 — supersedes the round-1 note that placed them in `H-*.json`), each validated at its own `b_H` with recomputed `U_{b_H},V_{b_H}` tables (never mixed with `b_n*` geometry); H1–H6 priority, no neural nets, `H(T,T)=0`, `H≥0`, sandwich, exact `E_K/E_D≤0` on discovery + held-out); independent clean-room falsifier (`M_K/M_D` over `R_n×[n]` + first maximizers + out-of-domain panel + `COUNTEREXAMPLE` freeze + mutation controls); large-`n` adversaries (listed generators × engines, exact-residual evaluation, history-realizable stream, motif generalization). Ceiling: `CANDIDATE_H_SURVIVES_FINITE_TESTS`.
**Files:** NOT YET CREATED — pending: frozen `H-*.json` ledger, adversary suite, independent audit package (no discovery imports), `artifacts/falsification/…`, `scripts/run_phase12-14.sh`.
**Code + how:** NOT YET WRITTEN — planned per WorkPlan §7 (exact rational residuals, sharded parallel eval + post-sort, heuristic-propose/exact-dispose).
**Benchmarks/gates:** H01–H05, A01–A02, H-GATE-0..8 — NOT YET RUN. No `REJECTED`/`COUNTEREXAMPLE_FOUND` emitted (no candidates exist).
**Follows WorkPlan.md?** N/A yet. Dependency: BLOCKED on WP-4 (needs derivative/kernel signal + held-out sizes). No deviation.
**Next action:** per-hypothesis Path sub-entries (definition, gates 0–8 verdicts, maximizers/counterexamples, adversarial logs).

---

## WP-6 — Universal proof (both branches) + seal & release (SPEC 15, 16, 17, 18) — status: `PENDING`

**Scope per WorkPlan.md §8:** P15-01..05 lemmas (declared domain, complete case split, no finite premises, independent audit, optional formalization) → P16 telescoping + Levy–Tarjan convention match → P17 negative family only if motif systematic (`T_k,X_k,Y_k`, `f/g`, `g/f→∞`) → P18 `FINAL_RESULT.json` + single claim level + SHA-256 manifest + deterministic archive + clean reproduction + Experiment-0 bundle/Tables A–E/mining report + §36 answers + AI-use declaration.
**Files:** NOT YET CREATED — pending: `math/proof_*.md`, `math/latex/*`, `artifacts/seal/*`, archive, audits, final reports/logs, `scripts/run_phase15-18.sh` + `reproduce_all.sh`.
**Benchmarks/gates:** P01–P02, S01–S03 — NOT YET RUN. No claim level emitted (current truthful level would be `FINITE_INFRASTRUCTURE_ONLY`-at-best, and even that requires WP-1; so **no level claimed yet**).
**Follows WorkPlan.md?** N/A yet. Dependency: BLOCKED on WP-5 (positive needs surviving `H`; negative needs systematic motif; seal needs everything executed). No deviation.
**Next action:** activate P17 only on evidence; otherwise pursue P15/P16 for the best WP-5 survivor; seal exactly what exists — never more.

---

## Deviation log (must stay empty until a real deviation occurs)

| Date (UTC) | WP phase | What deviated from WorkPlan.md | Cause | Impact on gates/claims | Corrective action (new version/ID) | Status |
|---|---|---|---|---|---|---|
| — | — | NONE TO DATE. Step 0 followed `WorkPlan.md §0` verbatim. | — | — | — | — |

*Rules: any deviation gets a row within the same editing session; the WP-phase section above gains a `DEVIATED` flag + cross-reference; silent deviation is forbidden (AI policy). Post-holdout hypothesis/feature edits are deviations by definition and create new IDs per WorkPlan §9.*

---

## Stop/failure ledger (STOP-01..16 + gate failure labels; preserved, never deleted)

| Date (UTC) | Size / scope | Label emitted | Trigger (exact) | Artifact preserved | Follow-up |
|---|---|---|---|---|---|
| — | — | NONE TO DATE. No runs executed, so no stops or failures. | — | — | — |

---

## Hypothesis & counterexample ledger (WP-4/5; failures preserved forever)

| ID | Definition (frozen) | Discovery / holdout | Gate verdicts | Killer counterexample / witness | Status |
|---|---|---|---|---|---|
| — | NONE YET. No hypotheses formed before WP-4. | — | — | — | — |

---

## Per-size exact-results table (§22 primary summary; filled only from sealed artifacts)

```text
n | C_n | |R_n| | b_n* (p/q) | subtype | #forced | #FORCED_DELTA | #crit SCCs | verifier
--|-----|-------|------------|---------|---------|---------------|------------|----------
2 |   — |     — |         —  |      —  |      —  |            —  |         —  | PENDING (WP-2)
3 |   — |     — |         —  |      —  |      —  |            —  |         —  | PENDING (WP-2)
4 |   — |     — |         —  |      —  |      —  |            —  |         —  | PENDING (WP-2)
5 |   — |     — |         —  |      —  |      —  |            —  |         —  | PENDING (WP-2)
6 |   — |     — |         —  |      —  |      —  |            —  |         —  | PENDING (WP-2)
7 |   — |     — |         —  |      —  |      —  |            —  |         —  | PENDING (WP-2)
```

*No decimal `b_n*` column will ever appear without an explicit "display-only" label (spec §34). No row is filled from expectations — only from `bn_certificate.json` + `verify_bn_certificate PASS`. The `subtype` column uses the `criticality_subtype` namespace (`TRANSIENT`/`CYCLIC`/`MIXED`/`CLASSIFICATION_INCOMPLETE`); the corresponding `top_level_status` (`EXACT_BN_*`) is recorded with the verifier verdict, per plan v0.1.1.*

---

## Claim-level tracker (only WP-6 may advance this; fail-closed)

- **Current truthful level:** NO LEVEL CLAIMED (nothing built yet; even `FINITE_INFRASTRUCTURE_ONLY` requires WP-1 gates).
- History: (none) — every future change recorded here with date, evidence, and the exact newly-satisfied gates.

---

## Next 3 actions (always concrete)

1. Resume WP-1: complete the interrupted scaffold (prereg, spec freeze, formal notes, schemas, code, tests, tree artifacts) → gates 00/01/02 → Path entries. Note: `README.md`, `CHANGELOG.md`, `CITATIONS.md`, `.gitignore`, `external/papers/` (L2/L3 PDFs) already exist in the working tree uncommitted; they will be verified/completed, not rewritten blindly.
2. WP-1 Step 2: reference + independent + functional Splay + fixtures + canaries (M01–M06) → Path entry; then enumeration (E01–E03) → Path entry.
3. Enforce plan v0.1.2 additions as WP-1 executes: frozen `splay_model` semantics (no WP-1/2 spill), T0 ledger with T0-GATE-A/B binding later seals, third functional impl + `n≤6` suite scope; carry the SA-01 proposal flag forward so WP-5 reports both `b`-geometries until ratification.

*End of Path.md — updated every session work is done; mirrored 1:1 with WorkPlan.md phases so adherence is checkable line-by-line.*
