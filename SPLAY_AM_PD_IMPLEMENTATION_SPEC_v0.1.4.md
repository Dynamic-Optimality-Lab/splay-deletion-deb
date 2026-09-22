# SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.4 — Ratified Amendment SA-04

**Document type:** ratified amendment to the frozen implementation specification
**Parent documents:**
`SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.md`
(SHA-256 `29070d39f54d40c3f8b1ccdde8b588545749dc3f60e8949c430036a0185f1565`)
as ratified-amended by `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md`
(amendment SA-01, rev.2;
SHA-256 `8B77278FF98F6AB5A3AA4D929A5787735F269647D5E3088CF4288F8ACF8C7726`),
`SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md`
(amendment SA-02;
SHA-256 `79C58ED0278A6F81FE42685955C2D50EEF9A6744CCD0A701B6FE8DF96EE41CDF`),
and `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3.md`
(amendment SA-03;
SHA-256 `BB407FAC46DB30FA58F8833E513152FC10182AC931AFD84DDB0C29B0217E25E1`)
**Amendment ID:** SA-04 — n8 Canary Contamination Correction and Replacement Holdout Protocol
**Ratified:** 2026-09-22, by owner direction, on a post-freeze audit finding in
the SA-03 execution report, BEFORE any WP-5 candidate synthesis.
**Scope:** corrects the provenance of the n8 holdout (canary-contaminated, no
longer fresh) and freezes the replacement hidden holdout bank
HOLDOUT-H1-v0.1 with its firewall, evaluation, and UH-6 semantics. Everything
not mentioned here is unchanged from v0.1 + SA-01 + SA-02 + SA-03. SA-01,
SA-02, and SA-03 are not edited retroactively. SA-04 applies only where
explicitly stated; everywhere else prior specs and the WorkPlan remain
normative.

---

## SA-04.1 What happened (frozen finding)

1. SA-03 correctly froze before WP-5 synthesis (commit `ba58a18`).
2. During SA-03 infrastructure verification, the frozen machinery self-test
   ran a COMPLETE n=8 evaluation with the degenerate `H = 0` test vector
   (`b_H = 23/14`).
3. That canary exposed detailed n=8 outputs beyond aggregate metadata —
   exact residual maxima, argmaxes, counts, and counterexample samples
   (recorded in §SA-04.2).
4. Therefore `n = 8` is no longer scientifically pristine as an untouched
   candidate-selection holdout for POST_N7 synthesis.
5. This finding occurred BEFORE any POST_N7 WP-5 candidate was synthesized
   (candidate set EMPTY, n8 firewall `EMPTY`, no `H-SA03-*`/`H-SA05-*` ID
   exists). The contamination is therefore containable without invalidating
   any candidate-development result — there is none to invalidate.
6. This is NOT a failure of the mathematics: every exposed residual is an
   exact integer-scaled value, and n=8 remains valid for exact falsification
   and exhaustive validation.
7. It IS a holdout-provenance issue, repaired here append-only and
   fail-closed: SA-03 stays byte-frozen; this amendment reclassifies n8 and
   installs the replacement.

---

## SA-04.2 Permanent n8 reclassification (frozen)

```text
N8_STATUS = PARTIALLY_REVEALED_CANARY_CONTAMINATED
```

Exactly what the SA-03 canary revealed (recovered from test code, frozen
gates, and execution outputs — nothing inferred):

- test vector: `H` identically 0 (infrastructure only; never a hypothesis,
  never ledgered as one), `b_H = 23/14` (UH-3-passing on sealed n=2..7)
- KEEP residual maximum (scaled by `q_H = 14`): `89` (= `14·8 − 23·1`),
  argmax `(source 1429, KEEP, key 8)`, positive count `3,944,504`
- DELETE residual maximum (scaled): `-23` (= `-23·1`), argmax
  `(source 0, DELETE, key 8)`, positive count `0`
- normalization violations: `0`; nonnegativity violations: `0`
- first preserved KEEP counterexamples (lex order): `(7,KEEP,8,+5)`,
  `(14,KEEP,8,+5)` (policy: lex-first 16 per mode + exact counts)
- code paths: `python/n8_holdout/sweep.py::sweep_pair_access` (primary) and
  `python/n8_holdout/independent.py::sweep_ind` (clean-room twin), full
  `R_8` (2,044,900 states) × 16 edges = 32,718,400 checks each, byte-exact
  agreement on maxima/argmaxes/counts/counterexamples
- files read: `artifacts/transitions/n8/forward.bin.zst`,
  `artifacts/reachability/n8/reachable.json.zst` (via the authorized
  test-vector path with EMPTY candidate set); files written: none under
  `artifacts/wp5/sa03/holdout/` (in-memory/test-temp only)
- commits: canary executed pre-`ba58a18` during SA-03 verification;
  classified here, post-`ba58a18`, pre-synthesis

Contamination-ledger vocabulary (frozen):
`KNOWN_BEFORE_SA03` (SA-03 aggregates) vs `REVEALED_BY_SA03_CANARY` (the
list above) vs `STILL_QUARANTINED` (every other detailed-n8 record: full
transition rows beyond what the maxima imply, the state list, per-edge
costs beyond argmax rows, unpreserved counterexamples, any feature table).

Consequences (frozen): n8 must never again be described as `FRESH`,
`UNTOUCHED`, or the sole UH-6 holdout for new candidates. The n8 firewall
stays ACTIVE against any FURTHER detailed inspection during synthesis; the
leaked canary facts are development-visible (they cannot be unseen); all
other n8 detail stays blocked until final candidate freeze. After freeze,
every serious candidate still undergoes the full exact n8 sweep, labeled
`N8_CONTAMINATED_EXHAUSTIVE_VALIDATION` — never `FRESH_HOLDOUT`. Any exact
n8 counterexample still REJECTS (contamination touches evidentiary
independence, never the mathematics of a counterexample). Passing n8 is
strong finite evidence but does NOT discharge the fresh UH-6 requirement.

---

## SA-04.3 Replacement holdout HOLDOUT-H1-v0.1 (frozen)

Before WP-5 synthesis, a new hidden bank is generated and frozen:

- bank ID `HOLDOUT-H1-v0.1`; sizes `n ∈ {9,10,12,16,24,32}` (above the
  development enumeration regime); exactly 20,000 reachable states per size;
  120,000 total states.
- Every state carries a legal KEEP/DELETE history from a diagonal `(T,T)`,
  so no global `R_n` enumeration is required or performed.
- Later, EVERY key and BOTH modes are tested per state: exactly
  `2·20,000·(9+10+12+16+24+32) = 4,120,000` fresh Pair-Access edge
  evaluations. The count identity is verified from bank metadata, never by
  sampling.
- Generator strata (frozen BEFORE generation; exact per-size counts in
  `prereg/wp5_sa04.yaml`): randomized legal histories; spine initials;
  opposite-spine drives; zig-zag initials; balanced initials; comb initials;
  DELETE-heavy / KEEP-heavy / alternating histories; inflated
  critical-cycle-motif patterns; MIS-inspired structural patterns; mirror
  pairs (mirrored histories, replay-verified). No candidate H touches
  generation; no residual-guided generation; no candidate-specific
  adversarial optimization — the bank is candidate-independent.
- Reproducibility WITHOUT secret exposure: the generation secret is stored
  ONLY in the quarantined bank metadata (never printed, never preregistered,
  synthesis-blocked); independent assurance runs by parse/verify — replay
  every stored history with two independent Splay implementations, confirm
  legality, diagonal reachability, state counts, and the edge-count
  identity — never by regeneration.
- Canonical serialization (sorted keys, newline-terminated JSON, `.zst`
  transport with logical+compressed SHAs); SHA-256 commitment over the
  canonical bank published in the prereg (`bank_commitment_sha256`).
  Commitment procedure: strata frozen in the prereg draft → bank generated
  per draft → commitment embedded → prereg bytes frozen pre-synthesis in the
  SA-04 commit. No synthesis exists at any point of this procedure.

---

## SA-04.4 Hidden-bank firewall (normative)

Synthesis must NOT read: holdout state encodings, history sequences,
initial trees, keys, modes, generator choices, hidden seed/material,
per-size state IDs, or any bank residuals. Published pre-synthesis ONLY:
bank ID, sizes, state count, total future edge count, generator-family
proportions, the SHA-256 commitment, schema version. No individual cases,
no secret material, never. Implementation: `python/holdout_bank/`
firewall with path-based guards + a static audit sweeping current and
future synthesis namespaces for forbidden references; dynamic guards fail
closed on any quarantined-namespace read pre-unlock.

---

## SA-04.5 Post-unlock evaluation (frozen)

After the final candidate set is frozen: (1) unlock the bank once;
(2) verify its hash against the preregistered commitment; (3) evaluate all
candidates (all states, both modes, every key; exact integer-scaled
residuals; maxima/maximizers/counterexample policy as SA-03.8);
(4) independently regenerate-or-parse/verify the bank (here: parse/verify);
(5) confirm every history legal; (6) confirm diagonal reachability via the
stored history; (7) confirm state/edge-count identities; (8) preserve all
failures. No candidate added after unlock (multiplicity rule §SA-04.6, same
frozen set consumes n8-detail and H1-detail; `final_candidate_set_hash`
recorded). Descendants after any reveal: NEW ID, n8 = development, H1 =
development, `untouched_sizes = []`, no fresh-holdout claim, unless a new
genuinely untouched protocol is frozen.

---

## SA-04.6 UH-6 correction (supersedes SA-03 POST_N7 UH-6 only)

UH-0..UH-5 unchanged. Mandatory additional `EV-8 —
N8_CONTAMINATED_EXHAUSTIVE_VALIDATION` (full n8 sweep + independent twin;
any exact failure rejects; never a fresh-holdout pass). UH-6 now means:
**candidate frozen before HOLDOUT-H1-v0.1 reveal + exact evaluation on all
120,000 hidden states and all 4,120,000 transitions + independent
verification** → `UH-6_PASS_FRESH_H1` or `REJECTED`. Passing n8 but failing
H1 ⇒ `REJECTED`. Failing n8 ⇒ `REJECTED` immediately (H1 need not be
consumed where protocol permits). Passing both ⇒ may proceed to UH-7/UH-8.
UH-7 covers EV-8 + H1 with independent tree/Splay/cost/H/residual/history
implementations and exact agreement. UH-8/UH-9 unchanged.

---

## SA-04.7 Adversarial + negative-branch discipline (frozen)

UH-8 generators/engines unchanged (WorkPlan list). n8 counterexamples may
seed NEW explicitly post-holdout descendant families only — never relabeled
as preregistered finds. Failures (candidate, repeated, finite-n8) are NOT
DOC disproofs; WP-6 negative branch still requires a parameterized infinite
`(T_k,X_k,Y_k)` family with proved unbounded ratio.

---

## SA-04.8 Artifacts, schemas, freezing (frozen)

Versioned artifacts (minimum): this amendment; `prereg/wp5_sa04.yaml`
(+ `.sha256`); `artifacts/wp5/h1_holdout/bank_manifest.json` (counts, strata,
serialization, commitment); quarantined `artifacts/wp5/h1_holdout/n{n}/bank.json.zst`
+ `bank_secret.json` (secret material, synthesis-blocked); H1 firewall state;
per-candidate H1 reports (post-unlock only); independent H1 reports;
counterexamples; lineage. WP-4/WP-5-SA-03 namespaces never overwritten.
Schemas (new, total 20 → 22): `schemas/wp5_holdout_bank_v0.1.schema.json`,
`schemas/wp5_holdout_result_v0.1.schema.json`. No silent extension of old
schemas. SA-04 + WorkPlan v0.1.8 + prereg + bank commitment + firewalls +
schemas + tests + Path/CHANGELOG/audits freeze in ONE commit BEFORE any WP-5
H synthesis. No candidate H, no coefficient search, no synthesis in that
commit.

---

## Ratification and hashing record

Ratified 2026-09-22 by owner direction, on the SA-03 canary finding,
post-`ba58a18`, pre-synthesis. The SHA-256 of this file is computed after
writing and recorded externally in `WorkPlan.md` (v0.1.8 header + §8 seal
set), `Path.md` (SA-04 entry), and the §19 final report; it is not
self-embedded. SA-01, SA-02, and SA-03 are untouched. Any further change
requires a new amendment version.
