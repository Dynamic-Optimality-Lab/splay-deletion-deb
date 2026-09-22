# SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2 — Ratified Amendment SA-02

**Document type:** ratified amendment to the frozen implementation specification
**Parent documents:**
`SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.md`
(SHA-256 `29070d39f54d40c3f8b1ccdde8b588545749dc3f60e8949c430036a0185f1565`)
as ratified-amended by `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md`
(amendment SA-01, rev.2;
SHA-256 `8B77278FF98F6AB5A3AA4D929A5787735F269647D5E3088CF4288F8ACF8C7726`)
**Amendment ID:** SA-02 — Adaptive Cycle-Discovery Mining Track
**Ratified:** 2026-09-22, by owner direction on a genuine sealed WP-3 audit
finding observed **before any WP-4 coefficient fitting**.
**Scope:** adds a second WP-4 mining track (Track B) alongside the untouched
original preregistered control (Track A). Everything not mentioned here is
unchanged from v0.1 + SA-01. SA-01 is not edited retroactively. SA-02 applies
only where explicitly stated; everywhere else the base spec, SA-01, and the
existing WorkPlan remain normative.

---

## SA-02.1 Empirical trigger (sealed WP-3 observation, commit `bd658be`)

Sealed WP-3 geometry (`GATED_PASS`, claim level `FINITE_EXACT_BN_RESULTS`):

```text
n | b_n*  | subtype (top-level) | #forced | #FORCED_DELTA | #crit SCCs | corridors
2 | 1/1   | MIXED               |       2 |             4 |          1 | 2
3 | 1/1   | MIXED               |       5 |            17 |          4 | 5
4 | 3/2   | CYCLIC              |      14 |            12 |          6 | 0
5 | 8/5   | CYCLIC              |      42 |             8 |          1 | 0
6 | 8/5   | CYCLIC              |     132 |            84 |         11 | 0
7 | 23/14 | CYCLIC              |     429 |            10 |          1 | 0
```

Sealed provenance breakdown (from `forced_delta_edges.json.zst`):

```text
n=2: FPATH 4,  FCYCLE 4   (all KEEP; DELETE 0)
n=3: FPATH 15, FCYCLE 15  (13 both + 2 FPATH-only + 2 FCYCLE-only detail; all KEEP)
n=4: FPATH 0,  FCYCLE 12  (100% cyclic; all KEEP)
n=5: FPATH 0,  FCYCLE 8   (100% cyclic; all KEEP)
n=6: FPATH 0,  FCYCLE 84  (100% cyclic; all KEEP)
n=7: FPATH 0,  FCYCLE 10  (100% cyclic; all KEEP)
```

For tested nontrivial sizes `n >= 4`, finite critical corridors disappear
(`transient_corridor_count == 0`, consistent with `CYCLIC` seals) and the
nontrivial forced-derivative information is cyclic. The original WP-4
selection protocol reserves **all** FCYCLE edges from coefficient selection.
Applied to the sealed sets, that holdout removes 100% of `n=4`/`n=5`
`FORCED_DELTA` rows (12 + 8 = 20 equations) and all but 2 rows of `n=3`,
leaving Track A discovery-starved precisely where `b_n* > 1`. Recording that
starvation as a result without any permitted cyclic learning would freeze the
experiment into a known-uninformative control. This amendment is the
versioned, fail-closed response: retain the original control untouched
(Track A) and add one explicitly preregistered cycle-discovery track
(Track B) with its own selection/validation/holdout firewall.

This amendment was triggered **before WP-4 coefficient fitting**. No `n=6`
row has participated in any coefficient search at SA-02 freeze time. No
detailed `n=7` edge-level structure has been inspected for hypothesis
generation at SA-02 freeze time (see §SA-02.4).

---

## SA-02.2 What is unchanged

All v0.1 definitions (key/tree universe, depth/cost `c = depth+1`, bottom-up
Splay 5 cases, pair states, KEEP/DELETE transitions, edge identity/order,
`R_n` domain and closure, regret/slack arithmetic `L_{p,q} = p*a - q*y`,
`b_n*` certificate, canonical `U/V/G` and `G == 0` forcing rule, critical
objects and forcing theorems, `FGAP` exact rule, rationality/denominator
bound, exact arithmetic, T0 gates, test matrix, invariants, logging, claim
levels) are unchanged. SA-01 (OG/UH two-track ladder + UH-3 `b_H`-feasibility
gate with BH01–BH05) is unchanged. Splay semantics, cost convention,
reachability domain, `b_n*`, `U/V/G` definitions, forcing theorems, exact
arithmetic, claim levels, and the SA-01 OG/UH architecture are not altered
by SA-02. FPATH orientation is `U(source)+L(e)-V(target) == 0`
(see `math/fpath_orientation_note.md`); SA-02 does not change it.

---

## SA-02.3 Two WP-4 mining tracks (frozen)

### TRACK A — ORIGINAL PREREGISTERED CONTROL (unchanged)

- Selection sizes: `n = 2,3,4,5`.
- Selection rows: forced edges with `reserved_family_holdout == false`.
- Exclusions (all applied): every FCYCLE row (`on_zero_cycle == true`);
  the declared DELETE-only reserve (`mode == DELETE`); the declared
  zig-zag reserve (A-splay rotation signature contains `LR` or `RL`).
- Validation size: `n = 6` (exact re-evaluation only, never fitting).
- Hard size holdout: `n = 7` (untouched until Track-A final candidate freeze,
  if any; post-`n=7` edits create a new hypothesis ID per §SA-02.6).
- Interpretation: Track A is never reinterpreted after seeing its results.
  If it is rank-starved or contains no nontrivial-`b` equations, that is
  recorded as a scientific result. Track A is never "repaired".

### TRACK B — SA-02 CYCLE-DISCOVERY TRACK

- Purpose: allow exact learning from the cyclic forcing WP-3 discovered,
  without contaminating later sizes.
- Selection sizes: `n = 4,5` only.
- Selection rows: **all** FCYCLE `FORCED_DELTA` rows at `n = 4,5`
  (`on_zero_cycle == true`, `forced_delta == true`), i.e. 12 + 8 = 20
  equations at freeze time. No Track-A family exclusion is re-applied.
- For Track B, DELETE/KEEP and zig/zig-zig/zig-zag are **reporting strata**,
  not exclusion masks. Stratification `KEEP/DELETE × FPATH/FCYCLE/FGAP ×
  zig/zig-zig/zig-zag × cost-discrepancy` is always reported, never used to
  silently drop Track-B rows.
- Validation size: `n = 6` (reveal only after the initial Track-B
  candidate/version is frozen; §SA-02.6).
- Hard untouched holdout: `n = 7` (reveal exactly once after the final
  Track-B candidate/version is frozen; §SA-02.6).
- No `n = 6` row may participate in initial coefficient fitting.
- No `n = 7` edge-level forced derivative, cycle anatomy, feature delta,
  residual, or candidate performance may be inspected before the final
  Track-B candidate/version is frozen.

Aggregate facts already known from sealed WP-3 — `b_7* = 23/14`,
forced-edge count 10, SCC count 1, criticality subtype `CYCLIC`
(`EXACT_BN_CYCLIC`), corridor count 0, all-KEEP share — are recorded in the
contamination ledger as PREVIOUSLY KNOWN AGGREGATE METADATA. They are not
permission to inspect detailed `n = 7` structure (per-edge provenances,
cycles, trajectories, feature deltas, residuals).

---

## SA-02.4 Holdout firewall (normative)

Before the final Track-B candidate freeze, mining code MUST refuse to load
detailed `n = 7` for hypothesis generation:

- `forced_delta_edges`
- critical cycles (`canonical_cycles` / `sccs`)
- trajectories
- feature deltas (`edge_deltas`)
- candidate residuals
- per-edge provenance

Implementation: `python/mining/holdout_firewall.py` with explicit
`allow_detailed_n7` gate (default `False`; unlock requires a frozen final
candidate ID + recorded hash). A dedicated test deliberately attempts such a
read and confirms failure (`HOLDOUT_FIREWALL_BLOCKS_N7`).

After the final candidate/version is frozen, `n = 7` is unlocked **exactly
once** for hard-holdout evaluation. Any post-`n=7` candidate change creates a
new hypothesis ID and loses the right to call that same `n = 7` evaluation
untouched. The old evaluation is never erased (append-only).

The same firewall guards initial fitting against `n = 6` detailed reads
(`HOLDOUT_FIREWALL_BLOCKS_N6_DURING_FIT`): Track-B initial fitting code
MUST refuse `n = 6` cycle anatomy / forced deltas / residuals until the
initial candidate/version is frozen. `n = 6` aggregate metadata already known
from WP-3 summaries (`b_6* = 8/5`, counts) is ledgered as previously known;
detailed `n = 6` structure is not inspected until freeze.

---

## SA-02.5 Cycle anatomy (selection sizes only before fitting)

Before Track-B fitting, canonical critical cycles for `n = 4` and `n = 5`
only are anatomized. For every canonical selected cycle the record carries:

state sequence `(A_i,B_i)`, edge index, `source_state_id`, `target_state_id`,
`key`, KEEP/DELETE mode, `a_i`, `y_i`, exact `L_i = p*a_i - q*y_i`,
cumulative scaled slack, A access path, B access path for KEEP, A rotation
signature, B rotation signature for KEEP, structural deltas already permitted
by the frozen feature vocabulary, cycle length, `sum_a`, `sum_y`, `sum_L`
(which must equal zero), reduced `sum_y/sum_a`, multiplier `k`.

For a critical cycle at `b = p/q`, exact verification is required:

```text
p * sum_a == q * sum_y,  sum_L == 0.
```

Since `gcd(p,q) == 1`, the record stores integers `k > 0` with

```text
sum_a == q * k,  sum_y == p * k.
```

`n = 6` cycle anatomy is not inspected until initial Track-B
coefficients/formulas are frozen. `n = 7` cycle anatomy is not inspected
until the final hard-holdout candidate is frozen; after final freeze the
full `n = 7` anatomy is produced and `n = 4/5/6/7` motifs are compared.

---

## SA-02.6 Feature / dataset / search / validation discipline (Track B)

- Feature program `F-v0.1` is unchanged. One state-only feature record is
  generated for every reachable state in every certified size. Extraction
  may depend only on `(A,B,n)` and key order. It MUST NOT read `U/V/G`,
  `b_n*`, criticality labels, BFS witness IDs, cycle membership, or
  forced-edge labels (joined only post-hoc). `F01/F02/F03` preserved.
  State-only definitions and exact arithmetic preserved. No feature may
  directly encode state IDs, cycle IDs, target slacks, canonical potentials,
  or any answer-derived identifier.
- Derivative datasets: for every forced edge
  `Delta F_j = F_j(target) - F_j(source)`, exact target `Delta H = ell_b(e)`
  with scaled form `q * Delta H = L_{p,q}(e)`. Track A and Track B have
  separate immutable manifests + hashes. Track-B selection is `n = 4/5`
  FCYCLE equations only. Validation/holdout datasets remain separate.
- Exact linear search FIRST (exact rationals; no floating fit determines
  acceptance; floats secondary diagnostics only, marked non-authoritative):
  per feature system and track compute rank over Q, nullity, independent
  basis rows, exact solution family if consistent, sparsest candidates under
  frozen domains, exact maximum residual, minimal inconsistent subsystem on
  failure. `n = 7` is never used to choose coefficients.
- Structured nonlinear atoms ONLY after linear exhaustion (existing ladder:
  `min/max`, integer indicators, local-count predicates, per-node sums,
  frozen-breakpoint piecewise integers, other authorized atoms). No
  unrestricted symbolic regression. Every atom has an answer-independent
  mathematical definition. Every candidate revision gets a new
  `hypothesis_id`.
- Validation order (Track B):
  A. Fit on `n = 4,5` only. B. Freeze initial candidate/version. C. Reveal
  `n = 6` and evaluate exactly. D. If `n = 6` causes revision, assign a new
  hypothesis/version and document that `n = 6` has become development
  information. E. Freeze final candidate before `n = 7`. F. Reveal `n = 7`
  exactly once as hard holdout. G. Any change after seeing `n = 7` creates a
  new experiment/hypothesis track; the previous `n = 7` run is never called
  untouched for the revised formula.
- Kernel ablation runs the WorkPlan kernel program unchanged except
  track-separated reporting. No answer-smuggling. `FULL_STATE` remains the
  required positive control. Exact smallest separating witnesses preserved
  on information/preservation loss.

---

## SA-02.7 New artifacts and schemas (normative)

Versioned artifacts (minimum):

- SA-02 normative amendment (this file)
- SA-02 preregistration `prereg/wp4_sa02.yaml` (+ `.sha256`)
- Track-A manifest + Track-B manifest (immutable + hashes)
- cycle-anatomy records (`artifacts/cycle_anatomy/n{n}/`)
- holdout-firewall audit (`artifacts/audits/holdout_firewall_audit.json`)
- contamination ledger (`artifacts/audits/contamination_ledger.json`)
- per-track exact linear-system reports
- per-track inconsistency witnesses (minimal inconsistent subsystems)
- validation (`n = 6`) and holdout (`n = 7`) reports (only when legitimately
  unlocked in order)

New normative schemas (2; total 16 → 18):

- `schemas/wp4_dataset_manifest_v0.1.schema.json`
  (Track-A/Track-B dataset manifests)
- `schemas/cycle_anatomy_v0.1.schema.json`
  (canonical cycle-anatomy records incl. `sum_a = q*k`, `sum_y = p*k`)

No incompatible schema is silently reused. The WorkPlan schema count is
updated from 16 to 18.

---

## SA-02.8 Claim discipline

SA-02 proves no theorem. WP-4 output remains theorem-mining evidence only.
A structural formula fitting Track-B equations must still pass WP-5 UH gates
and ultimately WP-6 symbolic proof before any universal claim. Claim level
does not advance merely because a formula fits. Current justified level
`FINITE_EXACT_BN_RESULTS` is unchanged by the SA-02 freeze itself.

---

## SA-02.9 Execution / commit discipline

The SA-02 amendment + preregistration freeze is its own commit before
coefficient fitting. Only after that commit is frozen may Track-B discovery
begin. "Write the rules" and "see the holdout results" are never combined
into one uncontrolled step. Every failed candidate, inconsistent subsystem,
counterexample, and mutation result is preserved append-only.

---

## Ratification and hashing record

Ratified 2026-09-22 by owner direction following the sealed WP-3 FCYCLE
observation above. The SHA-256 of this file is computed after writing and
recorded externally in `WorkPlan.md` (v0.1.6 header + §8 seal set) and
`Path.md` (SA-02 entry); it is not self-embedded. SA-01 is untouched.
Any further change to this amendment requires a new amendment version.
