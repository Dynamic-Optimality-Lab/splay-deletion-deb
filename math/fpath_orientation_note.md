# FPATH source/target orientation — formal note (SA-02 pre-flight audit)

**Status:** normative derivation for the SA-02 pre-flight FPATH audit.
**Scope:** freezes explicit names `source -> target` for one directed edge
`e : source_state_id -> target_state_id`.
No sealed WP-1/WP-2/WP-3 artifact is altered by this note.
**Date (UTC):** 2026-09-22
**Trigger:** SA-02 pre-flight step 2 (audit the FPATH source/target condition
before any WP-4 coefficient fitting).

---

## 1. Frozen definitions

- At certified `b = p/q` (reduced), integer-scaled edge slack
  `L(e) = p*a(e) - q*y(e)` where `a(e) = c(A,x)`, `y(e) = c(B,x)` (KEEP) or
  `y(e) = 0` (DELETE).
- `U(source_state_id) = min_{diagonal ⇝ source} ΣL` (minimum prefix slack,
  attained by a simple diagonal-rooted path at valid `b`; diagonal value 0).
- `V(target_state_id) = max_{target ⇝ *} ΣW` with `W = -L` and the empty
  continuation allowed, so `V >= 0`.
  Hence the minimum continuation slack from `target` is
  `min_{target ⇝ *} ΣL = -V(target_state_id)`,
  attained (empty path gives 0; no positive-regret cycle exists at valid `b`,
  so a simple attaining path exists).

## 2. Derivation (exact criterion)

Fix one directed edge `e : source_state_id -> target_state_id` with scaled
slack `L(e)`.

Consider any diagonal-rooted finite path that uses `e` exactly at the
junction `prefix + [e] + suffix`, where `prefix : diagonal ⇝ source` and
`suffix : target ⇝ *` (possibly empty). Its scaled total is

```text
L(prefix) + L(e) + L(suffix).
```

Minimising independently over all legal `prefix` and `suffix` (the two sides
of `e` are independent once `e` is fixed):

```text
min_total(e) = min_prefix + L(e) + min_suffix
             = U(source_state_id) + L(e) + (-V(target_state_id))
             = U(source_state_id) + L(e) - V(target_state_id).
```

Therefore:

- `min_total(e) >= 0` always at valid `b` (every diagonal-rooted path has
  nonnegative total; the prefix+e+suffix family is a subset).
- `e` belongs to *some* zero-total diagonal-rooted finite path **iff**
  `min_total(e) == 0`, i.e. **iff**

```text
U(source_state_id) + L(e) - V(target_state_id) == 0.
```

Both optima are attained, so equality is witnessed by the concrete
`U`-optimal prefix to `source`, `e` itself, and the `V`-optimal suffix from
`target` (the construction used by `find_transient` / corridor code).
A corollary used by the implementation: equality implies
`U(target) == U(source) + L(e)` (zero-reduced tightness), because
`V(target) <= U(target) <= U(source)+L(e) = V(target)`.

The reversed textual form `U[target] + L(e) - V[source] == 0` is **not** the
derived criterion. It swaps the prefix optimum (which belongs at `source`)
with the suffix optimum (which belongs at `target`).

## 3. Implementation inspection (verdict: behaviour CORRECT, names AMBIGUOUS)

Inspected at commit `bd658be` (WP-3 `GATED_PASS`):

- `python/reference/critical.py:build_zero_graph` (lines 69-79):
  loop variable `i` is the **source** index (`csr.off[i]` outgoing),
  `j = csr.tgt[e]` is the **target** index.
  Zero-reduced gate `w == U[j]-U[i]` is `L == U(target)-U(source)` (correct).
  FPATH gate `U[i] + w - V[j] == 0` is
  `U(source) + L(e) - V(target) == 0` (**correct behaviour**).
- `python/reference/solve_small.py:find_transient` (lines 695-699):
  `i` source, `j` target, gate `U[i] + ... - V[j] != 0` → continue.
  Same correct orientation.
- `python/reference/critical.py:build_critical` diagonal-start block
  (line 261): `U[f] + ... - V[j]` with `f` source diagonal, `j` target →
  correct orientation.
- `python/audit/verify_critical_objects.py` (line 107):
  `U[pid] + w - V[tgt] == 0` with `pid` source, `tgt` target → correct.
  Independent verifier therefore enforces the same correct orientation.

Textual (naming-only) reversals found, all in comments/docstrings, none in
executed gates:

- `python/reference/critical.py` line 59 docstring:
  `FPATH rule (complete): U[t]+L(e)-V[s] == 0` — if `t` reads as target and
  `s` as source, the two symbols are swapped relative to §2.
- `python/reference/solve_small.py` lines 685-686 docstring:
  `U[t]+L(e)-V[s] == 0` — same ambiguous `t/s` naming.
- `python/reference/critical.py` lines 4-5 docstring:
  `FPATH = edges with U[t]+L(e) == 0` — sufficient-only shorthand, not the
  complete rule (complete rule needs the `-V[source-side]` term at `target`).
- `Path.md` WP-3 entry (line ~374):
  ``complete rule is `U[t]+L(e)-V[s]==0` `` — same swapped naming in prose.
- `python/reference/solve_small.py:tight_pred_lists` uses `s` for the
  **target** index and `t` for the **source** predecessor (reverse-index
  convention), opposite to the forward-loop convention. This is the root
  cause of the ambiguous prose: `s/t` mean opposite ends in different
  functions.

Evidence that behaviour is correct and naming is the only defect:

- Recomputed over all reachable edges for `n=2..7` from sealed `U/V`:
  `U(source)+L-V(target)==0` reproduces the sealed `FPATH`/`on_zero_path`
  sets exactly (`4,15,0,0,0,0` for `n=2..7`); the swapped form disagrees on
  `2,12,20,28,...` non-zero-reduced edges (e.g. `n=2`: `src=1 tgt=3 KEEP k=1`
  has correct `False` vs swapped `True`, non-zero-reduced, correctly
  excluded from sealed `FPATH`). On the zero-reduced subgraph the two forms
  coincide for the sealed sizes (all observed differences are non-zero),
  which is why the prose reversal never corrupted a sealed set — but the
  full-edge comparison proves orientation is load-bearing in general.
- Both independent verifiers (`verify_critical_objects.py`, `verify_uv.py`)
  use the correct orientation; all WP-3 `CR-AUD`/`UV-AUD` checks are `PASS`.

## 4. Decision (fail-closed)

- **No WP-3 reseal required.** Sealed `U/V/G`, `forced_delta_edges`,
  `paths/canonical_paths`, `sccs/canonical_cycles`, `below_optimum`,
  `bn_certificate` bytes and hashes are **unchanged**. The defect is
  variable-naming in prose/comments, not edge behaviour.
- **Required follow-up (this SA-02 package):**
  (a) this note (derivation + verdict);
  (b) regression test `tests/test_fpath_orientation.py` using only explicit
  `source_state_id` / `target_state_id` field names (ambiguous `s/t`
  forbidden in that file by scan);
  (c) comment-only clarifications in code docstrings that name
  `source/target` explicitly (no logic change; verified by re-running the
  regression test + `CR-AUD` comparison).
- If any future run shows behaviour actually reversed
  (`U[target]+L-V[source]` matching sealed sets while the correct form does
  not), that run must emit `FPATH_ORIENTATION_FAIL`, halt WP-4, generate a
  new WP-3 repair run with old/new hashes recorded, update `Path.md`, and
  not start WP-4 until WP-3 is resealed. That branch was **not** taken.

## 5. Exact counts referenced (sealed WP-3, commit `bd658be`)

- Transient corridors (canonical zero paths): `2,5,0,0,0,0` for `n=2..7`.
- `FORCED_DELTA` edges: `4,17,12,8,84,10`.
- Sealed `FPATH` (`on_zero_path`): `4,15,0,0,0,0`.
- Sealed `FCYCLE` (`on_zero_cycle`): `4,15,12,8,84,10`
  (for `n>=4`, 100% of `FORCED_DELTA` is cyclic; see SA-02 trigger).
