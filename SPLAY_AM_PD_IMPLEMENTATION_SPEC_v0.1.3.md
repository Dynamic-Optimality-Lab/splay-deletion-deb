# SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3 — Ratified Amendment SA-03

**Document type:** ratified amendment to the frozen implementation specification
**Parent documents:**
`SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.md`
(SHA-256 `29070d39f54d40c3f8b1ccdde8b588545749dc3f60e8949c430036a0185f1565`)
as ratified-amended by `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md`
(amendment SA-01, rev.2;
SHA-256 `8B77278FF98F6AB5A3AA4D929A5787735F269647D5E3088CF4288F8ACF8C7726`)
and `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md`
(amendment SA-02;
SHA-256 `79C58ED0278A6F81FE42685955C2D50EEF9A6744CCD0A701B6FE8DF96EE41CDF`)
**Amendment ID:** SA-03 — Post-n7 Universal-Candidate Validation Protocol
**Ratified:** 2026-09-22, by owner direction, triggered AFTER WP-4 completed
(WP-4 `GATED_PASS` at commit `4c5eaf7`; claim level `FINITE_EXACT_BN_RESULTS`).
**Scope:** defines the validation/holdout semantics for NEW WP-5 universal
candidates created after the legitimate SA-02 n7 reveal. Everything not
mentioned here is unchanged from v0.1 + SA-01 + SA-02. SA-01 is not edited
retroactively. SA-02 is not edited retroactively. SA-03 applies only where
explicitly stated; everywhere else the base spec, SA-01, SA-02, and the
existing WorkPlan remain normative.

---

## SA-03.1 Trigger and non-retroactivity (frozen)

1. SA-03 was triggered AFTER WP-4 completed (`GATED_PASS`, commit `4c5eaf7`).
2. Detailed `n = 7` critical geometry and candidate performance were
   legitimately revealed under SA-02: `H-SA02-B-v1-final` was frozen, `n = 7`
   was unlocked exactly once
   (record `artifacts/audits/n7_unlock.json`: `candidate_id`
   `H-SA02-B-v1-final`, `unlock_count` 1), evaluated (max residual `139/35`,
   FAIL, preserved), and ledgered
   (`N7_REVEALED_ONCE_AFTER_FINAL_FREEZE`, then
   `N7_PREVIOUSLY_REVEALED_POST_H_SA02_B_V1_FINAL`).
3. Therefore no hypothesis created after WP-4 completion may claim `n = 7`
   as an untouched holdout. This status is permanent for this experiment.
4. This is NOT retroactive contamination of earlier candidates: ERA-A
   candidates frozen before the SA-02 n7 reveal (e.g. the historical
   Track-B candidate) keep their historical holdout labels/results,
   immutable.
5. SA-03 modifies only the validation/holdout semantics for NEW WP-5
   candidates (ERA B, §SA-03.2).
6. SA-01 remains authoritative for OG/UH logic except where SA-03 explicitly
   refines UH-6 for post-n7 hypotheses (§SA-03.6).
7. SA-02 remains authoritative for WP-4 provenance (tracks, firewall,
   manifests, mining results, failure preservation).

---

## SA-03.2 Candidate eras (frozen provenance classes)

### ERA A — PRE-n7 candidates

Candidates genuinely frozen before the SA-02 n7 reveal. Their existing
holdout labels/results remain historically correct and immutable. They are
never re-labeled, never re-evaluated as though fresh, never rehabilitated.

### ERA B — POST-n7 candidates

Every hypothesis created after WP-4 completion belongs here. Required
metadata on every ERA-B record:

```text
candidate_era  = POST_N7
n7_status      = REVEALED_DEVELOPMENT_DATA
untouched_sizes MUST NOT contain 7
```

Any use of `n = 7` for synthesis, diagnosis, motif extraction, feature
invention, coefficient choice, `b_H` choice, or candidate revision is
permitted ONLY as DEVELOPMENT evidence and MUST be ledgered honestly
(ledger category `N7_AS_DEVELOPMENT_DATA`, naming the exact use).
No future artifact may describe `n = 7` as untouched for ERA B. A test
(`SA03-01`) fails closed on any such claim.

---

## SA-03.3 Fresh holdout: n=8 direct Pair-Access sweep (frozen)

`n = 8` is the fresh candidate-level Pair-Access falsification holdout for
ERA-B hypotheses, with one explicit distinction:

- `b_8*` is NOT sealed (`RESOURCE_LIMIT_NO_CLAIM` stands). Hence `n = 8`
  is NOT an exact-`b_n*` geometry holdout. Claiming otherwise is forbidden.
- WP-2 already generated and independently audited the authoritative finite
  domain: single-tree transition tables (11,440 records = `n·C_n`, forward
  SHA-256 `7c2d8c5d…7cfa`, inverse `3f686c28…3d20`) and reachability
  (`|R_8| = 2,044,900` of 2,044,900 pairs, forward-closed, reachable
  SHA-256 `d6f5e920…57647`; audits `verify_transitions` / `verify_reachability`
  PASS). These are reused, never recomputed ad hoc.

For a candidate frozen as `(H, b_H)`, direct Pair-Access evaluation does NOT
require knowing `b_8*`. The holdout tests, exactly, with no tolerances:

```text
NORMALIZATION:   H(T,T) == 0                        for every diagonal
NONNEGATIVITY:   H(A,B) >= 0                        for every state in R_8
KEEP:            c(B,x) + H(S_xA,S_xB) - H(A,B) <= b_H*c(A,x)
DELETE:          H(S_xA,B) - H(A,B)      <= b_H*c(A,x)
```

All arithmetic exact (integer-scaled residuals; no floating sign tests).
With `|R_8| = 2,044,900` and `2n = 16` outgoing actions, the full local edge
sweep contains exactly `2·n·|R_n| = 32,718,400` reachable directed
Pair-Access checks. Do not sample. A positive residual is an exact finite
counterexample and rejects the candidate (`REJECTED` + smallest preserved
counterexample). A full pass proves ONLY the corresponding exact finite n=8
Pair-Access fact for that frozen candidate — never universality.

Finite-certificate distinction (normative): if normalization +
nonnegativity + every local inequality pass, then `(H, b_H)` itself
constitutes a finite feasible potential at `n = 8` and hence certifies the
finite upper statement `b_8* <= b_H` — but it does NOT identify exact `b_8*`.

---

## SA-03.4 n8 holdout firewall (normative)

Before an ERA-B candidate is finally frozen, candidate-generation/mining
code MUST NOT inspect detailed `n = 8` data. Blocked pre-freeze:

- n8 transition records
- n8 reachable state list
- n8 tree-pair structures
- n8 per-edge costs
- n8 residuals
- n8 candidate evaluations
- n8 maximizers
- n8 counterexamples
- n8 structural feature tables if later created

Previously known aggregate metadata stays visible (it is not a
candidate-selection input):

- `n = 8` exists; Catalan count 1430
- `|R_8| = 2,044,900` (all pairs reachable, observed)
- transition audit PASS + reachability audit PASS (summaries above)
- exact `b_8*` unavailable (resource boundary, `RESOURCE_LIMIT_NO_CLAIM`)

These are recorded as `PREVIOUSLY_KNOWN_AGGREGATE_METADATA`. Implementation:
`python/n8_holdout/n8_firewall.py` (state machine `EMPTY` → `SET_FROZEN` →
`UNLOCKED_ONCE`, hash-bound; modeled on the SA-02 firewall, which is left
byte-identical). Before unlock, deliberate detailed-n8 read attempts MUST
fail (tested). Machinery self-tests under §SA-03.11 are the only authorized
pre-unlock detailed reads, and only with the degenerate `H=0` test vector
while the candidate set is empty (nothing to adapt; outputs never enter
`artifacts/wp5/sa03/holdout/`).

---

## SA-03.5 Post-n7 WP-5 development data (frozen)

For ERA-B synthesis, all already-revealed `n ≤ 7` results may be used as
development/falsification evidence: sealed `b_n*` (n=2..7); `U/V/G`
(n=2..7); critical cycles; forced derivatives; the WP-4 MIS triple; the
12-row extended witness; kernel witnesses; the cycle comparison; the failed
F-v0.1 linear class; the failed 14-atom class; failed historical candidates.
This is NO LONGER a classical train/validation split across `n ≤ 7` — stated
plainly. Purpose of `n ≤ 7`: `STRUCTURAL_DISCOVERY_AND_FALSIFICATION`.
Purpose of `n = 8`: `FRESH_POST_N7_PAIR_ACCESS_HOLDOUT`.

---

## SA-03.6 UH-6 refinement for ERA B only (SA-01 untouched)

UH-0 (well-defined): unchanged. UH-1 (normalization): unchanged on certified
development sizes; repeated at n8 reveal. UH-2 (nonnegativity): unchanged on
development sizes; repeated at n8 reveal. UH-3 (`b_H` feasibility): unchanged
— exact `p_H·q_n ≥ p_n·q_H` for every SEALED `b_n*` (n=2..7) before any
candidate-specific canonical geometry; any FAIL ⇒ immediate `REJECT`. `n=8`
is NOT part of this precheck (`b_8*` unsealed); a full n8 Pair-Access pass
later supplies the finite n8 feasibility upper certificate directly. UH-4
(`b_H` sandwich): unchanged where computed under SA-01; the n8 canonical
sandwich is OPTIONAL (the direct sweep is stronger for falsification and
needs no `b_8*`). UH-5 (KEEP/DELETE at fixed universal `b_H`): development
exhaustive testing on revealed certified sizes `n ≤ 7`.

UH-6 — POST_N7 FRESH HOLDOUT: for ERA B, UH-6 means **candidate frozen
before detailed n8 reveal + complete exact n8 Pair-Access sweep (all
32,718,400 checks) + independent verification**. Any failure ⇒ `REJECTED`.
Any pass ⇒ `UH-6_PASS_FINITE_N8` ONLY. Never label it universal.

UH-7 (independent implementation): the independent package reimplements
parsing/Splay/cost/`H`/residuals from the frozen math text + `b_H` + grammar
+ contract, importing NOTHING from synthesis code (static separation audit);
cross-checked on small `n` before n8, then evaluates n8 independently with
hash/result comparison. UH-8 (adversarial): unchanged. UH-9 (proof):
unchanged, WP-6 only.

---

## SA-03.7 Candidate freeze contract (frozen)

Before n8 reveal, every ERA-B candidate freezes: `hypothesis_id`; complete
mathematical formula for `H`; all tie-breaking rules; normalization
conventions; structural definitions; exact rational `b_H = p_H/q_H`,
gcd-reduced, `q_H > 0`; candidate source hash; evaluation source hash;
schema version; candidate provenance; all `n ≤ 7` development evidence used;
current OG diagnostics; UH-0..UH-5 status; timestamp metadata only; git
commit; SHA-256 manifest. No `b_H` choice/modification after seeing n8. No
atom added, no tie rule changed, no normalization changed, no
semantics-affecting bugfix under the same holdout identity afterward.

---

## SA-03.8 n8 reveal protocol (frozen)

Per final frozen ERA-B candidate: (1) verify freeze hash; (2) unlock n8
once; (3) compute all `H` over `R_8`; (4) verify diagonals; (5) verify `H ≥ 0`
over `R_8`; (6) compute all 32,718,400 residuals; (7–8) record exact maxima
(KEEP/DELETE); (9) record lexicographically first maximizers; (10) preserve
required positive-residual counterexamples per policy (lex-first 16 +
exact counts); (11) independent recompute; (12) compare hashes/results;
(13) seal UH-6/7 outcome. Parallelism only with deterministic shard ordering
+ deterministic reduction. Exact arithmetic only.

---

## SA-03.9 After n8 is revealed (frozen)

FAIL ⇒ freeze `REJECTED` + smallest exact counterexample + maximizer/worst
residual + ledger append; n8 becomes revealed development data for
descendants. Descendants take NEW hypothesis IDs with `untouched_sizes = []`
unless a genuinely new untouched domain is established; n8 is never reused
as a fresh holdout for them. PASS ⇒ may proceed to UH-7/UH-8; at most
`CANDIDATE_H_SURVIVES_FINITE_TESTS` after all finite gates pass — never a
theorem.

---

## SA-03.10 Holdout multiplicity (frozen)

Before n8 unlock, freeze the COMPLETE set of candidates allowed to consume
the holdout (`n8_holdout_candidate_set`: IDs + hashes). Nothing may be added
after the first detailed n8 result. Multiple pre-frozen candidates may all be
evaluated, but multiplicity is reported explicitly — never cherry-pick the
best survivor. Prefer a very small preregistered final set.

---

## SA-03.11 Independent falsifier + machinery self-test (frozen)

`python/n8_holdout/` receives ONLY the frozen H math text, frozen `b_H`,
tree grammar, action contract, candidate ID/hash. It reimplements parsing,
Splay, access cost, `H`, and both residuals, importing NOTHING from synthesis
code (static audit `SA03-SEP`). Cross-check vs the primary evaluator on
small `n` precedes any n8 unlock. The SA-03 freeze self-test runs the full
machinery once with the degenerate `H = 0` TEST VECTOR (`b_H = 23/14`,
UH-3-passing) while the candidate set is EMPTY: this validates edge counting,
maxima/maximizers, counterexample preservation, and primary↔independent
agreement with nothing to adapt and nothing recorded as a hypothesis.

---

## SA-03.12 Adversarial track (frozen, separate)

UH-8 generators/engines stay as WorkPlan specifies (spines, opposite
spines, zig-zag, balanced/spine, root agree/disagree, interval-nesting
extremes, heavy/rank-gap extremes, mirrors, random Catalan, DELETE-diverged
histories, motif inflation, hill-climb, genetic/annealing proposers, SMT/MIP
where exact). Heuristics propose, exact evaluator disposes. n8 holdout
counterexamples MUST NOT be relabeled as preregistered adversarial finds;
they may seed NEW explicitly post-holdout descendant families only.

---

## SA-03.13 Negative-branch discipline (frozen)

Preserved: a failed candidate is NOT a DOC disproof; repeated failure is NOT
a DOC disproof; a finite n8 counterexample is NOT a DOC disproof. Negative
evidence enters WP-6 ONLY as a parameterized infinite family
`(T_k,X_k,Y_k)`, `Y_k ⪯ X_k`, with proved unbounded ratio. Levels never
blurred.

---

## SA-03.14 Artifacts, schemas, freezing (frozen)

Versioned artifacts (minimum): this amendment; `prereg/wp5_sa03.yaml`
(+ `.sha256`); `artifacts/wp5/sa03/candidate_eras.json`;
`artifacts/wp5/sa03/n8_firewall.json` (initial `EMPTY`);
`artifacts/wp5/sa03/n8_known_aggregates.json`;
`artifacts/wp5/sa03/n8_candidate_set.json` (EMPTY at freeze);
per-candidate `artifacts/wp5/sa03/holdout/<id>/…` (only after unlock);
independent reports; counterexamples; residual maxima; post-reveal lineage.
WP-4 namespaces never overwritten. Schemas (new, total 18 → 20):
`schemas/wp5_post_n7_candidate_v0.1.schema.json`,
`schemas/n8_pair_access_holdout_v0.1.schema.json`. No silent extension of old
schemas; reuse proves compatibility. SA-03 + prereg + firewall + schemas +
WorkPlan v0.1.7 freeze in ONE commit BEFORE any WP-5 H synthesis.

---

## Ratification and hashing record

Ratified 2026-09-22 by owner direction, triggered after WP-4 completion
(`4c5eaf7`). The SHA-256 of this file is computed after writing and recorded
externally in `WorkPlan.md` (v0.1.7 header + §8 seal set), `Path.md` (SA-03
entry), and the §22 final report; it is not self-embedded. SA-01 and SA-02
are untouched. Any further change requires a new amendment version.
