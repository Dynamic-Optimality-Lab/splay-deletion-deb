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

**Collateral truthfulness note (closed 2026-09-21):** the partial WP-1 scaffold
that sat uncommitted during audit rounds was completed, verified, and committed
with the WP-1 implementation (see WP-1 entry). No file was rewritten blindly:
`README.md`/`CHANGELOG.md`/`CITATIONS.md`/`.gitignore`/L2-L3 PDFs were kept and
accuracy-patched where the frozen plan had moved on (16 schemas, n≤6 suite,
spec v0.1.1).

---

## Audit remediation round 2 — WorkPlan.md v0.1.2 (2026-09-20) ✅ DONE

**What was done (deep detail):** the owner supplied a second external audit verdict, rechecked against the frozen spec (SHA-256 still `29070d39f54d40c3f8b1ccdde8b588545749dc3f60e8949c430036a0185f1565`). Verdict: all previous 10 findings fixed; all 56 mandatory test IDs present; but one new MAJOR mathematical issue + 7 smaller items before freeze. All 8 were patched (plan now v0.1.2, header-stamped), no research-architecture change:

1. **MAJOR — universal-`b_H` vs optimum-`b_n*` geometry split (`WorkPlan.md` §7):** the canonical sandwich for a universal hypothesis `(H,b_H)` must use `U_{b_H},V_{b_H}` recomputed at that same `b_H` (new artifact `artifacts/potentials/n{n}/hypothesis_bH/{U_bH,V_bH}.json.zst`, independently re-verified), never the WP-3 `U_{b_n*},V_{b_n*}` tables unless `b_H=b_n*` — testing one against the other mixes two Bellman problems and can falsely reject a valid universal potential. Frozen architecture now stated: WP-3/4 `b_n*`-geometry is the discovery microscope; WP-5 tests `(H,b_H)` at one fixed `b_H`; WP-6 proves it. Candidates split into **optimal-geometry hypotheses** vs **universal Pair-Access hypotheses**.
2. **MAJOR/spec-level — H-GATE-3 scope (SA-01, `WorkPlan.md` §7):** exact `b_n*` forced-derivative agreement stays a rejection gate for optimal-geometry hypotheses but is discovery evidence (not a rejection gate) for universal hypotheses with `b_H > b_n*`, which carry extra slack `ℓ_{b_H}(e) = ℓ_{b_n*}(e) + (b_H − b_n*)·a(e)`. Recorded as PROPOSED SPEC AMENDMENT SA-01 (since RATIFIED as spec v0.1.1 — see round-3 entry below): requires ratification in a new spec version before downgrading any gate; until ratified, both geometries are computed/reported separately and no universal hypothesis is marked `REJECTED` solely on a `b_n*`-derivative mismatch without a `b_H`-geometry violation (tension flagged in the ledger).
3. **ERROR — negative-endpoint wording (`WorkPlan.md` §1):** now reads "disproves approximate monotonicity and hence — via Levy–Tarjan equivalence after convention audit — disproves dynamic optimality for Splay."
4. **REQUIRED — WP-1 suite scope (`WorkPlan.md` §3):** reference+independent exhaustive through `n≤6`; third structurally independent slow functional implementation (`reference/functional_splay.py`) exhaustive through `n≤5`; required primitives now explicitly list `find_path`, `compute_depth`, `validate_bst`; M03–M04 benchmark text updated to match.
5. **REQUIRED — status spelling (`WorkPlan.md` §2 table + §4):** `UPPER/LOWER_CERTIFICATE_FAIL` written as the two exact statuses `UPPER_CERTIFICATE_FAIL`, `LOWER_CERTIFICATE_FAIL`.
6. **AMBIGUITY — schema extension (`WorkPlan.md` §7):** supersedes round-1 item 10 as implemented — `b_hypothesis`/`b_is_universal_candidate` do NOT go into `H-*.json`; the frozen `candidate_H.schema.json` is followed exactly and the universal-`b` fields live in versioned companion `H-*.eval_contract.json` (`EC-v0.1`); any future schema change means explicit schema/spec versioning.
7. **MINOR — notation:** `q ≤ n·R_n` → `q ≤ n·|R_n|` (3 sites: §1 contract, §3 T0-GATE-A, §4 discovery), `E_n=2nR_n` → `E_n=2n|R_n|` (§10); Step 0 item 3 of this file updated likewise.
8. **MINOR — exact filenames (`WorkPlan.md` §3):** `external/papers/` now lists `L1_sleator_tarjan_1985.pdf`, `L2_levy_tarjan_1907.06310v3.pdf`, `L3_chmel_et_al_2607.18498.pdf`; `math/` lists the five exact theorem-note filenames.

**Follows WorkPlan.md?** YES — plan correction per owner direction + external audit, recorded here with line-level evidence. No execution deviation (implementation still pending).

---

## Audit remediation round 3 — SA-01 RATIFIED, WorkPlan.md v0.1.3 (2026-09-20) ✅ DONE

**What was done (deep detail):** the owner supplied a third audit verdict: all round-1/round-2 findings fixed, but two items remained before freeze — (1) SA-01 must be ratified as a real spec version, not a proposal, with the ladder split into two tracks; (2) a new `b_H`-feasibility precheck is mathematically required. Both are now done:

1. **SA-01 RATIFIED as `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md` (new file, 127 lines, SHA-256 `5A82106730D68D831104B9DD0B36B297FF4452D60EC0B3CA53B035566B3F317D`):** parent v0.1 (`29070d39…f1565`) unchanged except the ladder application. OPTIMAL-GEOMETRY TRACK — OG-1 forced derivatives at `b_n*`, OG-2 `b_n*`-sandwich, OG-3 corridor explanation (diagnostics; OG failure flagged, never `REJECTED` alone). UNIVERSAL PAIR-ACCESS TRACK — UH-0 well-defined, UH-1 identity, UH-2 nonnegativity, UH-3 feasibility, UH-4 `b_H`-sandwich, UH-5 KEEP/DELETE at `b_H`, UH-6 held-out, UH-7 independent impl, UH-8 adversarial, UH-9 symbolic proof (WP-6); any UH-0..UH-8 failure ⇒ `REJECTED`. Normative v0.1 mapping included (H-GATE-3→OG-1, H-GATE-4→OG-2+UH-4, rest 1:1). The amendment resolves the contradiction the auditor identified (simultaneous "H-GATE-0..8 in order" + "don't reject on `b_n*`-derivative mismatch") — the former now reads as the UH order with OG reported alongside.
2. **UH-3 wired into `WorkPlan.md` §7:** feasibility precheck runs BEFORE any `U_{b_H},V_{b_H}` computation — exact `p_H·q_n ≥ p_n·q_H` per certified `n` into `H-*.bH_feasibility.json`; three-case rule (`<` ⇒ immediate `REJECT` reusing the certified `b_n*` lower witness with verifier-checked negative slack under `b_H`; `=` ⇒ reuse WP-3 tables; `>` ⇒ compute fresh). Verified: scope two-track wording (§7 scope), `H-*.bH_feasibility.json` in files list, UH-3 bullet, RATIFIED SA-01 bullet with track definitions + mapping, benchmarks line (UH-0..UH-8 + OG), §12 WP-5-done line, §2 omission-audit §24 mapping, §8 seal manifest (spec v0.1 + amendment v0.1.1).
3. **Plan header now points at the amended spec:** `WorkPlan.md` spec-source line cites v0.1.1 + both hashes; revision stamped v0.1.3. WP-1 files list includes the amendment file.

**Follows WorkPlan.md?** YES — plan + spec-amendment work per owner direction + external audit. No execution deviation (implementation still pending).

---

## Audit remediation round 4 — byte-audit, BH suite, provenance; PLAN FROZEN v0.1.4 (2026-09-20) ✅ DONE

**What was done (deep detail):** the owner supplied a fourth verdict (freeze-ready pending one verification caveat + two hardening edits). All three are now closed:

1. **CAVEAT CLOSED — byte/content audit of `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md`:** file read in full (164 read-lines); recomputed SHA-256 via `Get-FileHash` = `5A82106730D68D831104B9DD0B36B297FF4452D60EC0B3CA53B035566B3F317D`, byte-exact match to the hash stated in `WorkPlan.md` header and round-3 entry; `git status` confirms the file is unmodified since commit `452d6a6`. Normative content verified section by section: SA-01.1 rationale + extra-slack formula (file lines 15–33), OG-1..OG-3 with diagnostic-only decision power (37–48), UH-0..UH-9 with `REJECTED`-on-UH-failure semantics (52–71), UH-3 cross-multiplied check + three-case rule (75–98), `H-*.bH_feasibility.json` record schema (100–118), PASS-gate before sandwich work (120–122), v0.1 H-GATE mapping incl. H-GATE-3→OG-1 and H-GATE-4→OG-2+UH-4 (126–142), unchanged clause (146–155), ratification record (159–164). The amendment contains exactly the SA-01 rules the WorkPlan summarizes — no drift. The auditor may still inspect the pushed file directly; nothing further is needed on this item.
2. **HARDENING — BH01–BH05 (`WorkPlan.md` §7):** UH-3 now has explicit mandatory coverage — BH01 exact `b_H ≥ b_n*` per certified `n`; BH02 witness-reuse with verifier-checked negative `b_H` slack; BH03 equality table-reuse byte/hash consistency; BH04 recomputed `U_bH,V_bH` canonical inequalities; BH05 independent-verifier agreement on `b_H` geometry. Planned runner `tests/test_bh_feasibility.py` added to the WP-5 files list. Placed at plan level (the amendment's gate text is unchanged, so its hash is stable by design).
3. **HARDENING — release provenance (`WorkPlan.md` §8 seal):** `FINAL_RESULT.json` now carries `normative_spec_set: [{v0.1, 29070d39…f1565}, {v0.1.1-SA01, 5A821067…317D}]`; the archive name stays `SPLAY-AM-PD-v0.1.tar.zst` with the spec set embedded, so no future reproduction can silently omit SA-01.
4. **FREEZE:** `WorkPlan.md` stamped v0.1.4 FROZEN ("no further plan edits without a new audit finding"). Per the auditor's stop-editing guidance, the next information comes from implementation (`b_2*`, `b_3*`, …, first critical corridors), not more planning.

**Follows WorkPlan.md?** YES — hardening per owner direction + external audit, recorded here with line-level evidence. No execution deviation (implementation still pending).

---

## Audit remediation round 5 — UH-1/UH-2 semantics, BH02 split, holdout mask, schemas; PLAN FROZEN v0.1.5 (2026-09-20) ✅ DONE

**What was done (deep detail):** the owner supplied a fifth verdict (freeze-ready pending 4 wording/implementation fixes, no redesign). All four are now frozen:

1. **UH-1/UH-2 finite semantics (`SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md` SA-01.3 + `WorkPlan.md` §7 gates):** one interpretation everywhere — UH-1: `H(T,T)=0` on every certified diagonal, any nonzero value rejects from the universal track (additive-overhead variants take a different class/ID, never survive UH-1); UH-2: `H(s)≥0` ∀ `s∈R_n` on every certified size, any negative value is an exact counterexample and rejects; the remaining "proof obligation" is solely the arbitrary-`n` proof and belongs to UH-9. This required re-cutting the amendment (rev.2), so its SHA-256 changed `5A821067…317D` → `8B77278FF98F6AB5A3AA4D929A5787735F269647D5E3088CF4288F8ACF8C7726` (recomputed via `Get-FileHash`; history entries keep the old hash as-at-that-time, this entry is the supersession record). `WorkPlan.md` header, `normative_spec_set`, and revision stamp (v0.1.5 FROZEN) all carry the new hash.
2. **BH02 transient/cyclic split (amendment SA-01.4 + `WorkPlan.md` §7 UH-3 bullet + BH02 text):** TRANSIENT `b_n*` witness ⇒ same path must have negative `b_H` slack (exact check); CYCLIC witness ⇒ cycle infeasibility `L_{b_H}(C)<0` suffices, or diagonal-rooted `P_0·C^k` with exact minimal `k > L_{b_H}(P_0)/(−L_{b_H}(C))` and stored `repeat_count`. The `bH_feasibility.json` failure-witness schema gained `witness_kind` (`transient_path`|`cycle`|`prefix_plus_cycles`) and `repeat_count`.
3. **Explicit selection mask (`WorkPlan.md` §6 + §9.2):** frozen — SELECTION = `n=2..5` with `reserved_family_holdout=false`; RESERVED FAMILY HOLDOUT (never for coefficient selection) = all FCYCLE edges + DELETE-only stratum + zig-zag-dominated stratum; SIZE VALIDATION `n=6`; SIZE HOLDOUT `n=7`. Edge-delta rows carry the flag; selection code must exclude flagged rows; family holdout never claimed for strata seen at `n=2..5`.
4. **SA-01 schemas (`schemas/eval_contract_v0.1.schema.json` + `schemas/bh_feasibility.schema.json`, both written and JSON-validated this session):** cross-cutting rule now reads "14 base + 2 SA-01 schemas (16 total)"; WP-1 files list updated. No loosely validated JSON remains.

**Follows WorkPlan.md?** YES — hardening per owner direction + external audit, recorded here with line-level evidence. No execution deviation (implementation still pending).

---

## WP-1 — Foundation, frozen contract & reference Splay + BST universe (SPEC 00, 01, 02) — status: `GATED_PASS` (2026-09-21)

**Scope per WorkPlan.md §3 (plan v0.1.5):** all items executed. Literature
L2/L3 frozen+hashed, L1 paywall-recorded; spec + prereg frozen
(`prereg_sha256.txt` = `276529e5…3627`, gate-verified); `FORMAL_NOTES.md`
T0-01..T0-14 PROVED+REVIEWED with T0-GATE-A/B binding (ledger
`math/proof_status.json` all-PROVED; T0-GATE-A satisfied for WP-2,
T0-GATE-B re-checked before any Phase-06 seal); layout scaffolded;
`rust-toolchain.toml` 1.92.0 + `Cargo.lock` generated, `pyproject.toml`
(requires-python >=3.12, env 3.13.7), `requirements-lock.txt` (stdlib-only
for WP-1); reference (tuple) + independent (pointer-object, imports only
itself — verified by import scan) + functional third (index-array
copy-on-write) implementations; 20 fixtures (10 hand + 10 triple-agreement);
canaries; canonical enumeration + Catalan + interval-enumerator cross-check.
**Out-discipline held:** no `b_n*`/potential/feature/`H` code or artifact
anywhere in WP-1 scope.

**Files (WorkPlan §3 list — all created, verified present):**
`README.md` (accuracy-patched: spec v0.1.1, 16 schemas, n≤6 suite),
`IMPLEMENTATION_SPEC.md` (normative freeze, hash above),
`SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md` (pre-existing),
`FORMAL_NOTES.md`, `CHANGELOG.md` (+0.1.5 plan entry), `CITATIONS.md`,
`LICENSE` (kept), `pyproject.toml`, `requirements-lock.txt`, `Cargo.toml`,
`Cargo.lock` (generated, unedited), `rust-toolchain.toml`, `.gitignore`,
`prereg/` (6 files), `external/MANIFEST.json` + papers (L2/L3 + SHA256SUMS;
L1 `UNFROZEN_PAYWALL` with reliance note), `math/` (7 files),
`schemas/` (16/16 JSON-validated), `crates/splay_model/src/` (6 modules),
`python/reference/` (tree/splay/enumerate/functional/fixtures_hand/fixtures),
`python/audit/` (2 modules), `tests/test_wp1.py` + `tests/unit/` +
`tests/exhaustive/`, `artifacts/trees/n1..n8` (3 files each incl.
SHA256SUMS), `artifacts/logs/` (gate + stress JSON),
`scripts/run_phase00.{ps1,sh}`, `run_phase01.{ps1,sh}`, `run_phase02.{ps1,sh}`,
`freeze_fixtures.py`, `stress_wp1.py`.

**Code + how (as planned):** Rust pointer-index BST, no-recursion rotation
core with `debug_assert` consistency, 5-case `splay` with root/BST
post-conditions, exact-u128 Catalan, ASCII-sort canonical IDs; `cargo check
--tests` PASS. Rust native test *execution* is BLOCKED by environment (no
`link.exe`/MSVC linker) — recorded here, not a plan deviation: semantics
are verified by the Python triple gates below, and the Rust unit tests
(LL/RR/zig fixtures, Catalan, round-trips) will execute where MSVC exists.
Python reference exposes all required primitives (`parse_shape`,
`serialize_shape`, `assign_inorder_keys`, `find_path`, `compute_depth`,
`validate_bst`, `rotate_*`, `splay`).
**Model training:** NONE per plan — nothing trained, nothing to report (verified:
no fitting/learning code anywhere in WP-1 scope).

**Bugs found by the gates (evidence the gates work, all fixed + rerun green):**
B1 author inorder-labeling order bug (`tree.py`/`enumerate.py` read the
counter after right recursion; failed M03 on `(.(..))`) — fixed by capturing
the key before right recursion; the independent impl was already correct.
B2 hand-fixture error F-006/F-007 (`["LL","ZIG"]` — a 3-chain needs one
zig-zig only; all three implementations agreed `["LL"]`) — hand entries
corrected, machine cross-check won as designed. B3 `freeze_fixtures.py`
path bugs (two issues, fixed). B4 hash-compare case bug in gate00 (fixed;
artifacts were correct). B5 PS5.1 native-stderr termination in
`run_phase00.ps1` (fixed via preference guard). B6 Rust test typo (fixed).

**Benchmarks/gates (final full run 2026-09-21, 30/30 PASS, 0.3 s):**
gate00 18/18 (13 files, spec-hash, 2 papers, 14 T0, 16 schemas, 8 unit
tests), gate01 M01/M02/M03 (n=2 triple)/M04 (n=3, 15 ops triple)/M04-FIX
(20 fixtures)/M05/M06, gate02 E01 (Catalan 1,2,5,14,42,132,429,1430) /
E02-E03 / E-IND (interval agreement n≤6) / M04-EXT (n=4: 56 ops, n=5: 210
ops triple) / G02-EXH. Stress `wp1_stress.json`: n=6 ref-vs-ind 792/792
identical; enumerate rerun byte-identical; transition digest stable
(`62853f23dc0952a1`, n=4); reversed-zig-zag faulty variant detected;
depth-offset detected. No `FOUNDATION_NOT_FROZEN` / `SPLAY_SEMANTICS_MISMATCH`
/ `TREE_ENUMERATION_MISMATCH`; no STOP triggered. Covers STOP-01/02/03/15,
threats T2/T3, INV-001..INV-006 (INV-007/008 structural; pair side is WP-2).

**Console logging (user instruction; language mapping frozen here):**
implementation languages are Python/Rust/PowerShell (frozen stack), which
have no `console.log` primitive. The faithful equivalent is used —
`print()` in Python via `console_log()` helpers, `Write-Host` in `.ps1`
via step lines, `echo` in `.sh` — each preceded by an identification
comment `# console.log equivalent [ID]: purpose`. 25 statements, verified
by search with exact file:line (line numbers as committed):
`scripts/run_phase00.ps1`:7 [WP1-P00-01], :11 [WP1-P00-02], :18 [WP1-P00-03];
`scripts/run_phase01.ps1`:4 [WP1-P01-01], :8 [WP1-P01-02];
`scripts/run_phase02.ps1`:4 [WP1-P02-01], :9 [WP1-P02-02], :14 [WP1-P02-03];
`scripts/freeze_fixtures.py`:43 [WP1-FIX-01], :70 [WP1-FIX-02];
`scripts/stress_wp1.py`:90 [WP1-S-01], :98 [WP1-S-02], :120 [WP1-S-03],
:134 [WP1-S-04];
`tests/test_wp1.py`:81 [WP1-T-00], :95 [WP1-T-01], :133 [WP1-T-02],
:159 [WP1-T-03], :192 [WP1-T-04], :231 [WP1-T-05], :240 [WP1-T-06];
`python/reference/enumerate.py`:138 [WP1-ENUM-01], :148 [WP1-ENUM-02],
:182 [WP1-ENUM-03]. (POSIX `.sh` drivers carry the same IDs.)
Library code (tree/splay/enumerate core, Rust modules) is print-free by
design; audit code has no reference imports by construction + scan.

**Follows WorkPlan.md?** YES — every §3 scope/file/code/benchmark/model
(NONE)/gate element executed with evidence above. No WorkPlan deviation
(no deviation-log row). Environment limitation (MSVC linker) and the six
fixed bugs are recorded here, not deviations.

**Step history:** Step 1 freeze+scaffold (prereg/spec/notes/schemas/
toolchain/manifests) → Step 2 Splay core (3 impls, fixtures, canaries,
B1/B2 found+fixed) → Step 3 enumeration + artifacts n1..n8 (B5 found+fixed)
→ stress (B1–B6 all closed) → compliance sweep (closed Cargo.lock,
unit/exhaustive dirs, SHA256SUMS-per-size, README accuracy) → this entry.

**Next action:** WP-2 (transitions, `R_n`, discovery, `b_n*` seal) — needs
frozen WP-1 Splay + trees (satisfied) and T0-GATE-A/B (satisfied, re-checked
at seal). Per-size Path sub-entries will follow.

---

## WP-2 — Exact dynamics: transitions, reachability, discovery & certification of b_n\* (SPEC 03, 04, 05, 06) — status: `GATED_PASS` (2026-09-21)

**Scope per WorkPlan.md §4 (plan v0.1.5):** all items executed. Exact
single-tree tables (`n·C_n` records + inverse conservation) for n=2..8;
BFS `R_n` + parents + closure for n=2..8; two-mechanism discovery (HiGHS LP
proposal-only + exact parametric Dinkelbach) for n≤6 with AGREE everywhere;
exact two-sided seals (upper feasible potential + nonempty transient/cyclic
zero-slack witness + independent audit PASS + no-float scan) for n=2..7;
criticality subtyping with complete decision rules; rejected-`b` negatives
preserved in candidate trails. n=8: tables+reach observed and independently
verified; `b_8*` seal = `RESOURCE_LIMIT_NO_CLAIM` (stretch size, no
extrapolation). B06 correctly deferred to WP-3.
**Out-discipline held:** LP floats quarantined (`authoritative=false`,
agreement-checked only); no V/G mining, no `H` (upper potentials are
certificate vehicles per plan, WP-3 owns canonical analysis).

**Files (WorkPlan §4 list — all created):** `crates/pair_graph/src/`
(lib/state/edge/reachability/csr/reverse) + `crates/exact_solver/src/`
(8 modules) + `crates/cli` (all `cargo check --workspace --tests` PASS;
native test execution still needs an MSVC host), `python/reference/`
(pair_graph/solve_small/verify_small), `python/audit/` (graph +
verify_transition_table/verify_reachability/verify_bn_certificate/
verify_no_float_seal; import-scan proves zero `python.reference` imports),
`artifacts/{transitions,reachability,candidates,certificates}/n{2..7}` +
`transitions,reachability/audits/n8`, `artifacts/logs/` (gate + stress JSON),
`scripts/run_phase03..06.{ps1,sh}` + `run_n7.py` (staged n=7 driver) +
`stress_wp2.py`.

**Code + how (as planned, two exactness-relevant upgrades documented):**
(1) Hot paths use compact CSR (flat C arrays) + SLF queue Bellman-Ford:
n=6 discovery 1101 s → 0.6 s with byte-identical exact answer (8/5, same
trail shape); all witnesses verify-by-recompute (fail-closed).
(2) Budgeted far-below-optimum probes (sound climbing steps only —
INVALID solely with verified negative witnesses; UNDECIDED reruns
unbounded); LP floats never seed the climb (a float above the optimum
would break it) — agreement evidence only. (3) Reverse-CSR forward-index
bug found by the seal assert (fail-closed worked): pass-2 traversal mixed
reverse/forward edge domains; fixed with `rfwd` array + the bogus
single-edge fallback replaced by loud failure (zero-reduced ≠ zero-slack
for single edges). (4) GC-thrash fix in CSR bulk build (C-array appends +
gc guard) after the first n=7 worker stalled at 3.7 GB. (5) n=7 LP leg:
HiGHS burned 30+ min CPU on the 2.5M-row proposal LP without finishing;
worker killed (no artifact, no claim — not a STOP); size policy recorded
(`use_lp=False` for n>6, LP leg binds n≤6 where AGREE holds everywhere);
n=7 second mechanism = independent audit re-verification (stronger).
(6) Candidate generation: exact parametric Dinkelbach emits reduced
rationals directly (denominator bound enforced live via B-DENOM `q ≤ nR`);
LP-float→fraction reconstruction checked via B-DENOM + LP-REC agreement —
same gate substance as the convergents/Farey pipeline, recorded here as
the implemented procedure.

**Sealed exact results (evidence: `bn_certificate.json` + audit reports):**
n=2: C=2, R=4 (all), b*=1/1, EXACT_BN_MIXED, PASS.
n=3: C=5, R=19 (partial — R_n restriction is load-bearing, threats T1/T13),
b*=1/1, EXACT_BN_MIXED, PASS.
n=4: C=14, R=196 (all), b*=3/2, EXACT_BN_CYCLIC, PASS.
n=5: C=42, R=1764 (all), b*=8/5, EXACT_BN_CYCLIC, PASS.
n=6: C=132, R=17424 (all), b*=8/5, EXACT_BN_CYCLIC, PASS.
n=7: C=429, R=184041 (all), b*=23/14, EXACT_BN_CYCLIC, PASS.
n=8: C=1430, R=2044900 (all, independently verified) — observation only,
no `b_8*` claim (`RESOURCE_LIMIT_NO_CLAIM`).
Every seal: reduced p/q, cross-multiplied bracket, full-edge upper sweep
(2.5M edges at n=7 re-verified independently), nonempty diagonal-rooted /
prefixed witnesses with recomputed zero slack, criticality consistent,
`independent_verifier: PASS` + report hash (finalized post-audit; PENDING
→ PASS transition recorded in the file history), no-float scan clean.

**Benchmarks/gates (final runs 2026-09-21, all green):** gate03 T01/T02/T03
+ independent transition audit exact-match (n≤8 tables incl.); gate04
R01/R02/R03 + independent exact-set agreement (all sizes incl. n=7, n=8 —
exceeds the n≤6 minimum); gate05 B01/B02/B-TRAIL/B-DENOM/LP-REC (LP AGREE
n≤6, policy skip n=7); gate06 T0-GATE-B (ledger all-PROVED+REVIEWED before
every seal) + B03–B05 + SEP-AUDIT (zero reference imports) + S02
(independent PASS all sealed sizes) + S03 (float-free). Stress
`wp2_stress.json`: rediscovery byte-identical candidates n≤6, CLI rebuild
identical, audit repeat PASS. No failure labels; no STOP triggered. Covers
STOP-04..10/14, threats T1/T4/T5/T6/T13/T14/T15, INV-008..027.
**Model training:** NONE per plan (LP = quarantined proposer with quarantined
floats, not a model) — nothing trained; certificate outcomes are exact
(`UPPER/LOWER_CERTIFICATE_FAIL` vs seal), not scores.

**Console logging (same frozen mapping as WP-1):** `print()` via
`console_log()` helpers (Python), `Write-Host` (`.ps1`), `echo` (`.sh`),
`println!` (Rust CLI dispatch) — each with `# console.log equivalent [ID]`
comments. 50 statements, search-verified with exact file:line:
drivers `run_phase03.ps1`:4,:8; `run_phase04.ps1`:4,:8; `run_phase05.ps1`:4,:8;
`run_phase06.ps1`:4,:8 (`.sh` mirrors same IDs at :5,:6,:8,:9);
`run_n7.py`:40,:50,:63,:73,:79,:92; `stress_wp2.py`:41,:57,:77,:92;
`test_wp2.py`:71,:93,:120,:136,:190,:198;
`pair_graph.py`:54,:76,:109,:132,:140,:207;
`solve_small.py`:101,:170,:366,:386,:397,:630,:637,:706 (SOL-00 twice:
build-start + ready);
`verify_transition_table.py`:34,:57; `verify_reachability.py`:35,:78;
`verify_bn_certificate.py`:44,:67,:136; `verify_no_float_seal.py`:46,:59;
`crates/cli/src/main.rs`:8 [WP2-CLI-01].
Library/solver/audit code paths are print-free except these identified
emissions; audit imports verified reference-free by scan + SEP-AUDIT gate.

**Follows WorkPlan.md?** YES — every §4 scope/file/code/benchmark/model
(NONE)/gate element executed with evidence above, including T0-GATE-A/B,
nonempty witness rules, subtype/top-level namespaces, B06 deferral, and
rejected-`b` diagnostics in trails. No WorkPlan deviation (no deviation-log
row). Recorded non-deviations: CSR+SLF/budgeted-probe engineering,
Dinkelbach-first discovery with LP agreement (B-DENOM/LP-REC close the
reconstruction loop), n=7 LP size policy, n=8 `RESOURCE_LIMIT_NO_CLAIM`,
Rust exec limitation (check-green, MSVC host pending).

**Step history:** Step 1 recon (LP backends: scipy/HiGHS present, highspy
absent; pins recorded) + Rust crates (check-green) → Step 2 reference
pair-graph + exact solver (smoke n=2: b=1, n=3: b=1 MIXED, R_3=19/25) →
Step 3 audit verifiers (caught+removed a reference import) → Step 4 gates
03/04 green (R: 4/19/196/1764/17424) → Step 5 discovery (b*: 1,1,3/2,8/5,8/5;
n=6 LP slowness → COO rebuild 17 s) → Step 6 seal n≤6 (reverse-index bug
found by seal assert → fixed; all PASS) → Step 7 n=7 (GC-thrash kill →
CSR fix → b*=23/14 CYCLIC, LP 30-min hang → size policy, seal+PASS) →
Step 8 n=8 observation (R=2044900 verified, no `b*` claim) + stress green
+ B-DENOM/LP-REC hardening + this entry.

**Next action:** WP-3 (canonical U/V/G + forced states + FORCED_DELTA +
frozen `b⁻` B06 diagnostic) — needs sealed `b_n*` per `n` (satisfied for
2..7, INV-028). Per-size Path sub-entries will follow.

---

## WP-3 — Canonical potentials & critical geometry (SPEC 07, 08) — status: `GATED_PASS` (2026-09-21)

**Scope per WorkPlan.md §5 (plan v0.1.5):** all items executed. Exact
`U^Z/V^Z/G^Z` at each certified `b_n*` (n=2..7) with Bellman witnesses;
forced states exact (`G==0`, verified == diagonals everywhere);
zero-reduced graph + transient corridors + critical SCCs/cycles with
canonical representatives; `FORCED_DELTA = FPATH ∪ FCYCLE ∪ FGAP` with
frozen FGAP rule + `VBELLMAN`/`UBELLMAN` recorded + exact
`Delta_H_scaled`; human-readable trajectories with full step detail
(shapes, a/y, slack, U/V, forced transitions, WP-4 deltas placeholder);
frozen `b⁻` diagnostic discharging **B06** (all `NEGATIVE_CYCLE`, type
preserved separately).
**Out-discipline held:** tables reported as certified facts, no universal
interpretation (that is WP-4/5/6 business).

**Files (WorkPlan §5 list — all created):**
`crates/exact_solver/src/canonical_potentials.rs` extended (FGAP rule +
Bellman fns + unit tests, workspace check-green),
`python/audit/verify_uv.py` + `verify_critical_objects.py`,
`python/reference/canonical.py` + `critical.py`,
`artifacts/potentials/n{2..7}/` (U/V/G zst + forced_states + summary +
bellman_witnesses), `artifacts/critical/n{2..7}/` (zero_reduced zst,
paths/canonical_paths, sccs, canonical_cycles, forced_delta zst,
trajectories.md, below_optimum.json, summary),
`artifacts/logs/wp3_gate_*.json` + `wp3_stress.json`,
`scripts/run_phase07/08.{ps1,sh}` + `stress_wp3.py`.

**Code + how (as planned, two correctness upgrades documented):**
(1) V via reverse propagation (super-sink-style all-zero init; converges:
no negative-slack cycle can exist anywhere in `R_n` at valid `b`, else
diagonal reachability would break validity); reverse predecessors are the
CSR reverse relation = exact spec-§7.3 predecessor sets (audit uses the
inverse-table method independently; agreement proves the relation).
(2) FPATH completeness fix (bug B7, found by cross-checking WP-2 witness
existence against corridor output): `U[t]+L(e)==0` is sufficient-only; the
complete rule is `U[t]+L(e)-V[s]==0` (both directions by telescoping +
sandwich with attained optima). Corridors rebuilt as canonical
prefix(U-optimal DFS)/suffix(V-optimal DFS) per forced state (non-diagonal:
through-path; diagonal: out-starting path, else tight-backward path from
another diagonal). WP-2 `find_transient` upgraded to the same complete rule
(shared DFS machinery; V via `shortest_future`); all seals reproduced
identically (subtypes unchanged: complete-FPATH = 4,15,0,0,0,0 for
n=2..7). (3) Trajectories enriched to the full §8.5 step schema after a
compliance sweep caught thin steps. (4) Audit brute-force predecessor scan
hung at n=6 (hours) → replaced by inverse-table generation per spec §7.3.

**Measured canonical geometry (evidence: summaries + audits):**
forced = 2,5,14,42,132,429 = exactly the diagonals (verified by set
equality all sizes: off-diagonal freedom gap is always > 0);
maxU = 2,5,33,144,172,616; maxV = 1,2,7,21,35,119; maxG = 1,3,32,140,170,611.
Corridors (canonical zero paths): 2,5,0,0,0,0 — consistent with MIXED (n=2,3)
vs CYCLIC (n≥4) seals. Critical SCCs: 1,4,6,1,11,1. FORCED_DELTA edges:
4,17,12,8,84,10. B06: `NEGATIVE_CYCLE` at every size (below-optimum
failures are cyclic, incl. the `b⁻=1/2` diagnostic runs at b*=1).

**Benchmarks/gates (final runs 2026-09-21, all green):** gate07 54/54
(U01/U02/U03/V01/V02/V03/G01/G02 + independent UV-AUD incl. 184041-state
sweep at n=7); gate08 24/24 (C01–C05 incl. per-edge forcing provenance,
B06 typed diagnostics + independent CR-AUD with 6/6 checks: forced_set,
provenance, paths, cycles, coverage, below). Stress `wp3_stress.json`:
rebuild-identical summaries n≤5, audit repeat PASS. No
`CANONICAL_POTENTIAL_FAIL` (would have raised loudly); no STOP-11/12/13.
Covers threats T5/T7/T12/T15/T16, INV-028..030.

**Console logging (same frozen mapping):** 32 statements, search-verified
with exact file:line: `run_phase07.ps1`:4,:8; `run_phase08.ps1`:4,:8 (`.sh`
same IDs); `stress_wp3.py`:40,:70,:86; `test_wp3.py`:75,:98,:127,:135;
`canonical.py`:34,:49,:60,:63,:147; `critical.py`:57,:74,:237,:282,:311,
:370,:377,:396,:402,:417; `verify_uv.py`:47,:74,:112;
`verify_critical_objects.py`:80,:111,:268. Solver/audit internals are
print-free except these identified emissions.

**Follows WorkPlan.md?** YES — every §5 scope/file/code/benchmark/model
(NONE)/gate element executed with evidence above, incl. FGAP exact rule,
B06 ownership (deferred from WP-2 correctly), and T0/U/V/G theorem targets
as tables (not theories). No WorkPlan deviation (no deviation-log row).
Recorded non-deviations: CSR-reverse predecessor relation, Dinkelbach-first
discovery carried over, V shared with WP-2 detector, trajectory schema
enrichment, audit predecessor method.

**Step history:** Step 1 canonical module (smoke n=4: 14 forced) → Step 2
critical module (smoke: corridors=0 exposed the FPATH incompleteness) →
Step 3 audits (brute-force hang → inverse-table fix; zst-load bug) →
Step 4 gates green → Step 5 FPATH/corridor completeness rebuild + WP-2
detector upgrade + full re-seal (identical subtypes) → Step 6 trajectory
enrichment + stress + this entry.

**Next action:** WP-4 (state-only features + forced-derivative mining +
kernel ablation on the WP-3 FORCED_DELTA equations) — needs
`FORCED_DELTA` + `U/V/G` (satisfied for n=2..7). Per-size mining entries
will follow.

---

## SA-02 — Adaptive Cycle-Discovery Mining Track — amendment + preregistration freeze (2026-09-22) ✅ FROZEN (rules only; no coefficients fitted)

**What was done (deep detail, fail-closed, audit-preserving):**
1. PRE-FLIGHT: read `WorkPlan.md` v0.1.5, base extraction `IMPLEMENTATION_SPEC.md`, ratified SA-01 v0.1.1, `Path.md`, WP-3 summaries. Verified WP-1..WP-3 sealed hashes before mutation: `git status` clean at `bd658be`; WorkPlan `B83B77AF…1486`, Path `AC29C43F…0593`, SA-01 `8B77278F…7726`, extraction `276529E5…3627`; gates 00 (17PASS) / 01 (7) / 02 (5) / 03 (4) / 04 (4) / 05 (30) / 06 (36) / 07 (54) / 08 (24); `bn_certificate` b* `1,1,3/2,8/5,8/5,23/14`; critical summaries `forced 2,5,14,42,132,429`, `FORCED_DELTA 4,17,12,8,84,10`, corridors `2,5,0,0,0,0`, SCCs `1,4,6,1,11,1`. No sealed artifact deleted/rewritten/replaced/cleaned; no Splay/cost/reachability/`b_n*`/U/V/G/forcing/arithmetic/claim/SA-01-architecture change.
2. FPATH AUDIT (`math/fpath_orientation_note.md`, `tests/test_fpath_orientation.py` 15/15 PASS): froze `e : source_state_id -> target_state_id`; derived `min_total(e) = U(source)+L(e)-V(target)` because min continuation is `-V(target)`; inspected `critical.py:build_zero_graph` (`U[i]+w-V[j]`, `i`=source, `j`=target), `solve_small.py:find_transient` (`U[i]-V[j]`), `build_critical` diagonal block (`U[f]-V[j]`), `verify_critical_objects.py:107` (`U[pid]-V[tgt]`) — all behaviour CORRECT. Textual reversals are naming-only: `critical.py:59` + `solve_small.py:685-686` + `Path.md:374` write `U[t]+L-V[s]` (swapped if `t`=target, `s`=source); `critical.py:4-5` shorthand `U[t]+L==0` is sufficient-only; `tight_pred_lists` uses `s`=target/`t`=source (reverse-index convention). Full-edge recompute proves orientation load-bearing: correct `4,15,0,0,28→0,336→0,944→0` vs swapped `6,27,20,28,336,944` (all differences non-zero-reduced; sealed FPATH `4,15,0,0,0,0` matches correct exactly). Verdict: NO WP-3 RESEAL (behaviour correct, prose ambiguous); regression test uses only `source_state_id`/`target_state_id` (AST-enforced, no `s`/`t` Name nodes) + hand unit + tightness checks.
3. SA-02 RATIFIED as `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md` (SHA-256 `79C58ED0278A6F81FE42685955C2D50EEF9A6744CCD0A701B6FE8DF96EE41CDF`): triggered by sealed WP-3 observation before WP-4 fitting (see trigger below); SA-01 untouched; applies only where stated; base+SA-01+WorkPlan normative elsewhere.
4. WorkPlan v0.1.6 FROZEN (SHA-256 recorded post-edit; header carries SA-02 + prereg hashes): minimal changes — normative stack + trigger + two tracks + anti-overfitting charter (Track-A vs Track-B validation) + `normative_spec_set` base+SA01+SA02 + schemas 16→18. Preserves v0.1.5 history; permitted by the “no further edits without a new audit finding” rule (this FCYCLE starvation IS that finding).
5. PREREG `prereg/wp4_sa02.yaml` (SHA-256 `BDE98934623B8EDCE00369F0C426E0DFE1358F158A688BA1EA2D885628B3B826`, sidecar `prereg/wp4_sa02.sha256`): selection/validation/holdout, prohibited reads, candidate-version rules, firewall, anatomy fields, search order, validation order A–G. Frozen before coefficient search.
6. FIREWALL `python/mining/holdout_firewall.py` (default-deny detailed n7; blocks detailed n6 during initial fit; unlock-once after final freeze; mismatch/second-unlock fail-closed) + `tests/test_sa02_freeze.py` 23/23 PASS (prereg/SA-02 hashes, v0.1.6/18/schemas/spec-set, Track-A 0 rows with per-n `{2:0,3:0,4:0,5:0}`, Track-B 20 rows `{4:12,5:8}`, FW-N7/FW-N6/UNLOCK flows, sealed n4/5 cycle `p*sum_a==q*sum_y`, `sum_a==q*k` checks, no-answer-import, namespace, sealed-hash preservation). Contamination ledger `artifacts/audits/contamination_ledger.json` (previously known `b_7*=23/14` + counts ledgered; detailed n7/n6 unread attested). Schemas 18/18 JSON-valid (2 new SA-02).
7. NO coefficient search has run at this freeze. NO `n=6` row fitted. NO detailed `n=7` inspected for generation. Cycle anatomy / features / datasets / linear search / kernels begin ONLY after this freeze commit.

**Exact sealed WP-3 observation triggering SA-02:** corridors `2,5,0,0,0,0` (zero for all `n>=4`, consistent with `CYCLIC` seals at `b_n* = 3/2,8/5,8/5,23/14`); `FORCED_DELTA` `4,17,12,8,84,10` with provenance `FPATH 4,15,0,0,0,0` vs `FCYCLE 4,15,12,8,84,10` (100% cyclic at `n>=4`); all forced edges KEEP (DELETE 0); `n=3` non-FCYCLE 2 rows both zig-zag (`LR`/`RL`, recomputed via frozen Splay); Track-B zig strata at selection: `n=4` 12×zig, `n=5` 4×zig + 4×zigzig; validation `n=6` 42×zig + 42×zigzig; holdout `n=7` 6×zig + 2×LL,ZIG + 2×RR,ZIG (unseen multi-step motifs).
**Why the original FCYCLE holdout became discovery-starved:** reserving all FCYCLE (+ DELETE-only + zig-zag) leaves Track-A selection `n=2..5` with 0 rows (`n=2` 4 FCYCLE-out; `n=3` 15 FCYCLE-out + 2 FPATH-only but zig-zag-out; `n=4` 12-out; `n=5` 8-out) — precisely where `b_n*>1` non-trivial geometry lives.
**Why Track A is retained untouched:** it is the original preregistered control; reinterpreting it after seeing starvation would be silent preregistration alteration. Starvation is recorded as a scientific result, never repaired.
**Why Track B is scientifically justified:** it learns only from the exact cyclic forcing WP-3 discovered (`n=4,5` FCYCLE, 20 equations), with DELETE/KEEP and zig families as reporting strata (never masks), strict `n=6`-after-initial-freeze / `n=7`-once-after-final-freeze order, firewall + contamination ledger, exact-linear-first discipline, and per-track manifests — discovery without contaminating later sizes.
**What n=7 information was already known before SA-02:** aggregates from sealed summaries — `b_7*=23/14`, forced 429 / `FORCED_DELTA` 10 / SCC 1 / `CYCLIC` / corridors 0 / all-KEEP (ledgered as PREVIOUSLY KNOWN AGGREGATE METADATA).
**What detailed n=7 information remained unread:** every per-edge/cycle/trajectory/delta/residual/provenance detail at `n=7` (firewall default-deny; deliberately failed-read test confirms).
**Exact commit/hash at which SA-02 became frozen:** freeze commit hash recorded post-commit (see follow-up discovery entry for the hash); file hashes: SA-02 `79C58ED0…41CDF`, prereg `BDE98934…3B826`, WorkPlan v0.1.6 (header), schemas manifest `372E0E03…DBEE99`, anatomy `3B9919EC…7699DD`, firewall `0514AEFF…012C1A`, FPATH note `3E19C875…371AE8`, FPATH test `775D7893…F97EB9`. WP-3 required NO resealing (orientation verdict above).

**Follows WorkPlan.md?** YES — this amendment IS WorkPlan v0.1.6 (`§6` SA-02 tracks, `§9` charter, `§10` 18 schemas, `§8` spec set) executed append-only with evidence above. No deviation.

---

## WP-4 — State-only features + forced-derivative mining + kernel ablation (SPEC 09, 10, 11) ⭐ — status: `PENDING`

**Scope per WorkPlan.md §6:** versioned `F-v0.1` state-only features (depth/parent/ancestor/subtree/rank/interval/access-path/crossing/heavy/bend + vectors + mirror declarations + hand tests); exact `ΔF` vs `ΔH=L/q` datasets; sparse exact combination + structured-atom searches with versioned coefficient domains + basis/inconsistency analysis + stratification; PC-style kernels (value-separation + transition-preservation + ablation + sharpness table + full-state control). Quarantine: mining never writes certificates.
**Files:** NOT YET CREATED — pending: `crates/feature_core/src/*` (10 modules), `python/mining/*` (9 scripts), `artifacts/{features,kernels,hypotheses}/…`, mining-report skeleton, `scripts/run_phase09-11.sh`.
**Code + how (incl. model specifics):** NOT YET WRITTEN — planned per WorkPlan §6/§9: discovery equations `n=2..5`; domains `ℤ[−M,M]→ℚ_{den≤D}→nonneg→signed` as new search versions; ranking `(count, residual, complexity, cross-n)`; `R²` secondary only; minimal-inconsistent-subsystem preservation; kernel whitelist + static audits.
**Resultant benchmarks:** NONE YET — planned: satisfaction counts, max residuals, rank/nullity, separation/preservation verdicts, stratified tables.
**Brutal anti-overfitting (ENTIRELY different benchmarks):** NOT YET EXECUTED — planned per WorkPlan §9: held-out `n=6/7` (10–100× larger, unseen shapes/SCCs), held-out strata (FCYCLE/DELETE/zig-zag), derivative-not-scalar target, independent re-implementation (WP-5), large-`n` adversaries (WP-5), out-of-domain panel (WP-5), mutation controls (WP-5); `CROSS_N_STABLE` only after untouched-size survival; post-holdout edits → new IDs.
**Follows WorkPlan.md?** N/A yet (WP-4 not started). Entry Dependency: UNBLOCKED
2026-09-21 — WP-3 delivered `FORCED_DELTA` + `U/V/G` for n=2..7 with audits.
No deviation.
**Next action:** freeze `F-v0.1` definitions note before any code; then features → deltas → searches → kernels, each with Path sub-entries (schema hash, static-audit result, discovery tables).

---

## WP-5 — Candidate H synthesis + independent falsification + adversarial search (SPEC 12, 13, 14) ⭐ — status: `PENDING`

**Scope per WorkPlan.md §7 (spec v0.1.1, plan v0.1.3):** ratified two-track ladder — OG-1..OG-3 diagnostics reported for every universal hypothesis, UH-0..UH-8 decisive (UH-9 is WP-6); UH-3 `b_H`-feasibility precheck (`H-*.bH_feasibility.json`, exact cross-multiplication, reject/reuse/recompute rule) before any `U_{b_H},V_{b_H}` work; versioned state-only `H` freeze (frozen H schema followed exactly; universal-`b` fields in companion `H-*.eval_contract.json`), each validated at its own `b_H` with recomputed `U_{b_H},V_{b_H}` tables (never mixed with `b_n*` geometry); H1–H6 priority, no neural nets, `H(T,T)=0`, `H≥0`, sandwich, exact `E_K/E_D≤0` on discovery + held-out); independent clean-room falsifier (`M_K/M_D` over `R_n×[n]` + first maximizers + out-of-domain panel + `COUNTEREXAMPLE` freeze + mutation controls); large-`n` adversaries (listed generators × engines, exact-residual evaluation, history-realizable stream, motif generalization). Ceiling: `CANDIDATE_H_SURVIVES_FINITE_TESTS`.
**Files:** NOT YET CREATED — pending: frozen `H-*.json` ledger, adversary suite, independent audit package (no discovery imports), `artifacts/falsification/…`, `scripts/run_phase12-14.sh`.
**Code + how:** NOT YET WRITTEN — planned per WorkPlan §7 (exact rational residuals, sharded parallel eval + post-sort, heuristic-propose/exact-dispose).
**Benchmarks/gates:** H01–H05, A01–A02, BH01–BH05 (UH-3 suite; BH02 split transient-same-path vs cyclic-cycle-or-`P_0·C^k`, per plan v0.1.5), ratified UH-0..UH-8 decisive + OG-1..OG-3 diagnostics (spec v0.1.1 rev.2) — NOT YET RUN. No `REJECTED`/`COUNTEREXAMPLE_FOUND` emitted (no candidates exist).
**Follows WorkPlan.md?** N/A yet. Dependency: BLOCKED on WP-4 (needs derivative/kernel signal + held-out sizes). No deviation.
**Next action:** per-hypothesis Path sub-entries (definition, gates 0–8 verdicts, maximizers/counterexamples, adversarial logs).

---

## WP-6 — Universal proof (both branches) + seal & release (SPEC 15, 16, 17, 18) — status: `PENDING`

**Scope per WorkPlan.md §8:** P15-01..05 lemmas (declared domain, complete case split, no finite premises, independent audit, optional formalization) → P16 telescoping + Levy–Tarjan convention match → P17 negative family only if motif systematic (`T_k,X_k,Y_k`, `f/g`, `g/f→∞`) → P18 `FINAL_RESULT.json` + single claim level + SHA-256 manifest + deterministic archive + clean reproduction + Experiment-0 bundle/Tables A–E/mining report + §36 answers + AI-use declaration.
**Files:** NOT YET CREATED — pending: `math/proof_*.md`, `math/latex/*`, `artifacts/seal/*`, archive, audits, final reports/logs, `scripts/run_phase15-18.sh` + `reproduce_all.sh`.
**Benchmarks/gates:** P01–P02, S01–S03 — NOT YET RUN. Current level remains
`FINITE_INFRASTRUCTURE_ONLY` (WP-1); no higher level claimed.
**Follows WorkPlan.md?** N/A yet. Dependency: BLOCKED on WP-5 (positive needs surviving `H`; negative needs systematic motif; seal needs everything executed). No deviation.
**Next action:** activate P17 only on evidence; otherwise pursue P15/P16 for the best WP-5 survivor; seal exactly what exists — never more.

---

## Deviation log (must stay empty until a real deviation occurs)

| Date (UTC) | WP phase | What deviated from WorkPlan.md | Cause | Impact on gates/claims | Corrective action (new version/ID) | Status |
|---|---|---|---|---|---|---|
| — | — | NONE TO DATE. Step 0 followed `WorkPlan.md §0` verbatim; WP-1 executed per `WorkPlan.md` §3 with evidence (no deviation). | — | — | — | — |

*Rules: any deviation gets a row within the same editing session; the WP-phase section above gains a `DEVIATED` flag + cross-reference; silent deviation is forbidden (AI policy). Post-holdout hypothesis/feature edits are deviations by definition and create new IDs per WorkPlan §9.*

---

## Stop/failure ledger (STOP-01..16 + gate failure labels; preserved, never deleted)

| Date (UTC) | Size / scope | Label emitted | Trigger (exact) | Artifact preserved | Follow-up |
|---|---|---|---|---|---|
| — | — | NONE TO DATE. WP-1/WP-2/WP-3 runs executed 2026-09-21 (all gates green, stresses green); no stop/failure label emitted. WP-1 bugs (B1–B6), WP-2 dev issues (reverse-index bug, GC-thrash stall, n=7 LP hang), WP-3 dev issues (FPATH incompleteness B7, audit brute-force hang, zst-load bug, thin trajectories) were passing-control/development findings fixed pre-seal, not stops. | — | — |

---

## Hypothesis & counterexample ledger (WP-4/5; failures preserved forever)

| ID | Definition (frozen) | Discovery / holdout | Gate verdicts | Killer counterexample / witness | Status |
|---|---|---|---|---|---|
| — | NONE YET. No hypotheses formed before WP-4. | — | — | — | — |

---

## Per-size exact-results table (§22 primary summary; filled only from sealed artifacts)

```text
n | C_n | |R_n| | b_n* (p/q) | subtype (top-level) | #forced | #FORCED_DELTA | #crit SCCs | verifier
--|-----|-------|------------|---------------------|---------|---------------|------------|----------
2 |   2 |     4 | 1/1        | EXACT_BN_MIXED      |       2 |             4 |          1 | PASS
3 |   5 |    19 | 1/1        | EXACT_BN_MIXED      |       5 |            17 |          4 | PASS
4 |  14 |   196 | 3/2        | EXACT_BN_CYCLIC     |      14 |            12 |          6 | PASS
5 |  42 |  1764 | 8/5        | EXACT_BN_CYCLIC     |      42 |             8 |          1 | PASS
6 | 132 | 17424 | 8/5        | EXACT_BN_CYCLIC     |     132 |            84 |         11 | PASS
7 | 429 |184041 | 23/14      | EXACT_BN_CYCLIC     |     429 |            10 |          1 | PASS
8 |1430 |2044900| — (RESOURCE_LIMIT_NO_CLAIM) | — | — | — | — | N/A (observation only)
```

*No decimal `b_n*` column will ever appear without an explicit "display-only" label (spec §34). No row is filled from expectations — only from `bn_certificate.json` + `verify_bn_certificate PASS`. The `subtype` column uses the `criticality_subtype` namespace (`TRANSIENT`/`CYCLIC`/`MIXED`/`CLASSIFICATION_INCOMPLETE`); the corresponding `top_level_status` (`EXACT_BN_*`) is recorded with the verifier verdict, per plan v0.1.1.*

---

## Claim-level tracker (only WP-6 may advance this; fail-closed)

- **Current truthful level:** `FINITE_EXACT_BN_RESULTS` (advanced 2026-09-21:
exact finite-`n` subsequence overheads with two-sided certificates +
canonical `U/V/G` potentials, all independently verified for n=2..7 —
exactly what this level words. No theorem-level claim.)
- History: 2026-09-21 advanced NO LEVEL → `FINITE_INFRASTRUCTURE_ONLY` on the
  evidence in the WP-1 entry (30/30 gate checks + 8 sealed tree universes +
  stress `wp1_stress.json`); same day advanced → `FINITE_EXACT_BN_RESULTS`
  on the WP-2 entry (sealed `b_n*` n=2..7) plus WP-3 entry (canonical `U/V/G`
  + forced geometry, gates 07/08 green, audits PASS).

---

## Next 3 actions (always concrete)

1. WP-4 Step 1: freeze `F-v0.1` feature definitions + state-only extractor
   (F01 static audit, F02 sanity, F03 mirrors) over every `s ∈ R_n` →
   Path sub-entry.
2. WP-4 Step 2: forced-derivative datasets (`ΔF` vs `ΔH`) + exact
   sparse-combination/atom searches with discovery/holdout split + equation
   basis witnesses (D01–D03) → Path sub-entry.
3. WP-4 Step 3: kernel identification/ablation with transition-preservation
   tests (K01–K03) + mining report skeleton → Path sub-entry; no theorem
   claimed (mining success ≠ theorem).

*End of Path.md — updated every session work is done; mirrored 1:1 with WorkPlan.md phases so adherence is checkable line-by-line.*
