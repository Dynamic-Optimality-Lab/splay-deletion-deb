# SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1 — Ratified Amendment SA-01

**Document type:** ratified amendment to the frozen implementation specification
**Parent document:** `SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.md`
**Parent SHA-256:** `29070d39f54d40c3f8b1ccdde8b588545749dc3f60e8949c430036a0185f1565`
**Amendment ID:** SA-01
**Ratified:** 2026-09-20, by owner direction on external audit finding
(round-2 audit: universal-`b_H` vs optimum-`b_n*` geometry split)
**Scope:** replaces the single-track application of H-GATE-0..H-GATE-9 with a
ratified two-track ladder, and inserts the `b_H`-feasibility gate UH-3.
Everything not mentioned here is unchanged from v0.1.

---

## SA-01.1 Rationale (frozen)

A universal candidate `(H,b_H)` is validated at one fixed `n`-independent `b_H`.
The WP-3/WP-4 canonical objects `U_{b_n*}`, `V_{b_n*}`, `G_{b_n*}` and the forced
derivative equations `ΔH = l_{b_n*}(e)` belong to the optimum-`b_n*` geometry of
each finite size. A valid universal potential with `b_H > b_n*` carries extra
slack

```text
l_{b_H}(e) = l_{b_n*}(e) + (b_H − b_n*)·a(e),   a(e) ≥ 1,
```

so exact equality at the smaller `b_n*` is not logically necessary for it.
Testing `V_{b_n*} ≤ H ≤ U_{b_n*}` against `b_H` inequalities mixes two different
Bellman problems and can falsely reject a valid universal potential. The
frozen v0.1 ladder (H-GATE-3 mandatory exact forced-derivative agreement,
H-GATE-4 `V ≤ H ≤ U` without a stated `b`, failure at any gate ⇒ `REJECTED`)
therefore cannot govern universal candidates unchanged. This amendment splits
it into two tracks with distinct decision power.

---

## SA-01.2 OPTIMAL-GEOMETRY TRACK (theorem-discovery diagnostics)

```text
OG-1  agreement with forced derivatives ΔH = l_{b_n*}(e) on discovery sizes
OG-2  agreement with U_{b_n*}, V_{b_n*} (canonical sandwich at b_n*)
OG-3  explanation of zero-slack critical corridors (paths/cycles)
```

OG results are discovery evidence. An OG failure is preserved and flagged in
the hypothesis ledger but **never by itself marks a universal Pair-Access
hypothesis `REJECTED`**. OG diagnostics are produced in WP-4 and reported in
WP-5 for every universal hypothesis.

---

## SA-01.3 UNIVERSAL PAIR-ACCESS TRACK (decisive for candidate survival)

```text
UH-0  H well-defined on every tested state (total, state-only function)
UH-1  H(T,T) = 0 on every certified diagonal (exact finite gate). Any nonzero
      value rejects the candidate from the universal Pair-Access track.
      Additive-overhead variants use a different hypothesis class/ID and
      never survive UH-1.
UH-2  H(s) >= 0 for every s in R_n on every certified size (exact finite
      gate). Any negative value is an exact counterexample and rejects the
      universal Pair-Access candidate. The remaining "proof obligation" is
      solely the arbitrary-n nonnegativity proof, which belongs to UH-9.
UH-3  candidate b_H feasible: b_H ≥ b_n* for every certified n (exact, §SA-01.4)
UH-4  V_{b_H} ≤ H ≤ U_{b_H} on small certified states, with U_{b_H}, V_{b_H}
      recomputed at the hypothesis's own b_H (never the b_n* tables)
UH-5  KEEP/DELETE inequalities at b_H: max E_K ≤ 0, max E_D ≤ 0, exactly
UH-6  all exact checks on held-out certified size(s)
UH-7  independent clean-room implementation agrees exactly
UH-8  adversarial large-n search finds no exact counterexample
UH-9  symbolic universal proof complete (WP-6; the only theorem gate)
```

Failure at any UH-0..UH-8 gate freezes the hypothesis as `REJECTED` with the
smallest exact counterexample available (failure artifacts preserved
append-only per the frozen preservation rule). Only UH-9 supports a theorem
claim. The ceiling below UH-9 remains `CANDIDATE_H_SURVIVES_FINITE_TESTS`.

---

## SA-01.4 UH-3 `b_H`-feasibility gate (exact precheck before any `U_{b_H},V_{b_H}` computation)

For a frozen universal candidate `b_H = p_H/q_H` (reduced, from the
hypothesis's `eval_contract.json`) and every certified size `n` with exact
`b_n* = p_n/q_n` (reduced, sealed):

```text
exact comparison:  p_H·q_n ≥ p_n·q_H   (cross multiplication, arbitrary precision)
```

Rule (frozen):

```text
b_H < b_n*  ⇒  REJECT immediately. The b_H slack graph then has a negative
               diagonal-rooted path or reachable negative cycle, so the
               ordinary finite canonical geometry does not exist (future
               regret can be +∞). The failure witness branches on the
               certified b_n* lower-witness type:
               TRANSIENT witness P with Y(P)/A(P) = b_n*: the same path
               has L_{b_H}(P) < 0; the verifier checks
               p_H·sum_a − q_H·sum_y < 0 exactly.
               CYCLIC witness (diagonal prefix P_0 + zero-slack cycle C
               with L_{b_n*}(C) = 0): either the cycle infeasibility
               certificate L_{b_H}(C) < 0 (a negative directed cycle alone
               contradicts the Bellman inequalities and suffices to
               reject), or, when a diagonal-rooted finite negative path is
               requested, P_0·C^k with the exact minimal integer
               k > L_{b_H}(P_0) / (−L_{b_H}(C)); repeat_count k is stored.

b_H = b_n*  ⇒  reuse the WP-3 canonical tables (no recomputation).

b_H > b_n*  ⇒  compute fresh U_{b_H}, V_{b_H} (independently re-verified).
```

Artifact (per universal hypothesis):

```text
artifacts/hypotheses/H-*.bH_feasibility.json
```

containing for every certified `n` one record:

```text
n
b_H: {p, q}            (decimal integer strings, reduced)
b_n_star: {p, q}       (decimal integer strings, reduced, sealed)
comparison: "p_H*q_n >= p_n*q_H -> true|false"   (exact boolean)
verdict: "PASS" | "FAIL"
failure_witness: null | { type: "reused_bn_witness",
                          witness_kind: "transient_path" | "cycle"
                                        | "prefix_plus_cycles",
                          repeat_count: null | "<exact integer k, only for
                                         prefix_plus_cycles>",
                          witness_file, witness_sha256,
                          slack_under_bH_num, slack_under_bH_den,
                          negative: true }
```

No `U_{b_H}`/`V_{b_H}` computation for any `n` may begin before every record in
this file reads `PASS`. A single `FAIL` rejects the universal candidate
immediately (UH-3), before any sandwich or residual work.

---

## SA-01.5 Mapping from the v0.1 H-GATE ladder (normative)

```text
v0.1 H-GATE-0  →  UH-0   (well-defined)
v0.1 H-GATE-1  →  UH-1   (identity normalization)
v0.1 H-GATE-2  →  UH-2   (nonnegativity)
v0.1 H-GATE-3  →  OG-1   (diagnostic; discovery evidence for universal candidates)
v0.1 H-GATE-4  →  OG-2 at b_n* (diagnostic) AND UH-4 at b_H (decisive)
v0.1 H-GATE-5  →  UH-5   (KEEP/DELETE at b_H)
v0.1 H-GATE-6  →  UH-6   (held-out)
v0.1 H-GATE-7  →  UH-7   (independent implementation)
v0.1 H-GATE-8  →  UH-8   (adversarial)
v0.1 H-GATE-9  →  UH-9   (symbolic proof)
```

References to "H-GATE-0..8 in order" in plans and reports are read as the UH-0..UH-8
order for universal Pair-Access hypotheses, with OG-1..OG-3 reported alongside.

---

## SA-01.6 What is unchanged

All v0.1 definitions (key universe, tree universe, depth/cost conventions,
bottom-up Splay cases, pair states, KEEP/DELETE transitions, edge identity and
order, `R_n` domain and closure, regret/slack arithmetic, `b_n*` certificate,
canonical potentials, critical objects, feature discipline, kernel tests,
adversarial design, proof decomposition, telescoping, negative branch, seal
rules, threat model, test matrix, invariants, logging, claim levels) are
unchanged. This amendment only re-homes hypothesis validation into the two
tracks above and inserts the UH-3 precheck.

---

## Ratification and hashing record

Ratified 2026-09-20 by owner direction following the round-2 external audit.
The SHA-256 of this file is computed after writing and recorded externally in
`WorkPlan.md` (header) and `Path.md` (round-3 entry); it is not self-embedded.
Any further change to this amendment requires a new amendment version.
