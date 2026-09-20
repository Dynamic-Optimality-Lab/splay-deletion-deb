# FORMAL_NOTES.md — Phase-0 Proof Obligations T0-01..T0-14

**Status ledger:** all fourteen theorems PROVED below (author line-by-line
review 2026-09-20). REVIEWED: all fourteen (proof text reviewed; T0-01..T0-04,
T0-06, T0-11..T0-13 additionally backed by the WP-1 gate suite where marked).
**Binding gates:** T0-GATE-A (T0-13 PROVED+REVIEWED before `q ≤ n·|R_n|` use),
T0-GATE-B (all PROVED+REVIEWED before any Phase-06 `b_n*` seal).
Notation follows IMPLEMENTATION_SPEC.md. All arithmetic exact.

## T0-01 Path-to-(X,Y) correspondence — PROVED, REVIEWED

Claim: diagonal-rooted KEEP/DELETE paths biject with triples
`(T, X, Y ⪯ X)` (up to the fixed initial tree).
Proof: induction on path length. Base: length 0, `X = Y = ∅`. Step: edge
`e` with key `x` extends `X` by `x` always; extends `Y` by `x` iff KEEP.
Pair-state update matches the recursive Splay-tree definition by §7, so the
constructed `(A,B)` equal the true full/subsequence trees. QED. [test-backed: M04]

## T0-02 Path costs equal Splay costs — PROVED, REVIEWED

Claim: `Σ_{e∈P} a(e) = Splay(X(P),T)`, `Σ y(e) = Splay(Y(P),T)`.
Proof: induction. `A_i` after `i` steps equals the full-history Splay tree
(T0-01), so `a(e_{i+1}) = c(A_i, x_{i+1})` is exactly the next Splay access
cost; same for `B` on KEEP edges, and DELETE contributes `0 =` no
subsequence access. Summation gives the identities. QED. [test-backed: M04]

## T0-03 Fixed-n path formulation — PROVED, REVIEWED

Claim: `b_n* = sup_{nonempty P from Δ} Σy/Σa`.
Proof: T0-01 gives a bijection between admissible `(T,X≠∅,Y⪯X)` and nonempty
diagonal-rooted paths; T0-02 shows costs agree termwise. Sup SMA over
identical ratio multisets coincide. Denominator `> 0` since `a(e) ≥ 1`. QED.

## T0-04 Sanity `1 ≤ b_n* ≤ n` — PROVED, REVIEWED

Claim: every exact output satisfies the bracket.
Proof: lower — `Y = X` gives ratio 1. Upper — each retained access costs
`≤ n`, each full access `≥ 1`, `|Y| ≤ |X|`, so `Σy ≤ n·Σa`. QED.
[test-backed: E01]

## T0-05 Valid b iff normalized pair potential exists — PROVED, REVIEWED

Claim: `b` valid (all diagonal-rooted `L_b(P) ≥ 0`) iff `F_{n,b} ≠ ∅`.
Proof (⇐): telescope any diagonal-rooted path:
`Σℓ_b = Σ(H diff) = H(end) − H(start) = H(end) ≥ 0`. (⇒): validity implies
no diagonal-reachable negative cycle (else repeat for arbitrarily negative
paths), so shortest-path distances `U_b` from the diagonal super-source are
finite; `U_b ≥ 0`, `U_b = 0` on diagonals, and path extension gives
`U_b(t) ≤ U_b(s) + ℓ_b(e)`. Hence `U_b ∈ F_{n,b}`. QED.

## T0-06 U/V definitions and Bellman inequalities — PROVED, REVIEWED

Claim: `U_b`, `V_b` satisfy `U(t)−U(s) ≤ ℓ_b(e)`, `V(t)−V(s) ≤ ℓ_b(e)`,
`V ≥ 0`, and the `V` Bellman equation with empty continuation.
Proof: `U` by path extension as in T0-05. `V`: stopping immediately yields
`0`, so `V ≥ 0`; any first edge `e` plus an optimal continuation gives
`V(s) ≥ −ℓ_b(e) + V(s')`, and some outgoing edge (or stopping) attains the
supremum over a finite graph, giving the equation. QED.

## T0-07 Sandwich `V ≤ H ≤ U` — PROVED, REVIEWED

Claim: every `H ∈ F_{n,b}` satisfies `V_b(s) ≤ H(s) ≤ U_b(s)` pointwise.
Proof: `H(s) ≤ U_b(s)`: telescope `H` along a shortest diagonal path to `s`
(`U` is its total slack; diagonal value 0). `H(s) ≥ V_b(s)`: for any
continuation path, telescoping `H` gives `H(s) ≥ −L_b(P) + H(end) ≥ −L_b(P)`;
take sup over continuations. QED.

## T0-08 U,V feasible at valid b — PROVED, REVIEWED

Claim: at valid `b`, `U_b, V_b ∈ F_{n,b}`.
Proof: `U` by T0-05. `V`: T0-06 gives edge inequalities and `V ≥ 0`; on a
diagonal `d`, validity gives `W_b(P) ≤ 0` for all continuations while the
empty continuation gives `0`, so `V_b(d) = 0`. QED.

## T0-09 Zero-slack path forcing — PROVED, REVIEWED

Claim: a diagonal-rooted zero-slack path forces every edge derivative and
every path-state value across all feasible `H`.
Proof: residuals `r_H(e) = ℓ_b(e) − ΔH(e) ≥ 0` sum to total slack `0`, so
each is `0`: `ΔH = ℓ_b` on every edge. Prefix/suffix optimality then gives
`U = V = H` at each path state. QED.

## T0-10 Zero-slack cycle forcing — PROVED, REVIEWED

Claim: a zero-slack directed cycle forces every cycle-edge derivative
across all feasible `H` (states need not be forced).
Proof: residual sum around the cycle is `0` with nonnegative terms, so each
residual is `0`. No state claim: constant shifts around the cycle are
unconstrained by the cycle alone. QED.

## T0-11 Walk decomposition — PROVED, REVIEWED

Claim: every finite walk = simple path + multiset of cycles, additively in
`(a, y)`.
Proof: while a vertex repeats, excise the directed cycle between repeats;
repeat until simple. Edge multisets partition, so `(a, y)` sums split
additively. QED. [test-backed: E01–E03 graph finiteness]

## T0-12 Rationality — PROVED, REVIEWED

Claim: `b_n* ∈ ℚ`.
Proof: by T0-11, any walk ratio is a positive-denominator (`a > 0`)
weighted average of its simple-path/cycle component ratios; hence the
supremum over walks equals the maximum over finitely many simple
diagonal paths and reachable simple cycles (the cyclic case being possibly
asymptotic via repetition). Integer `(a, y)` give rational component
ratios; finite max of rationals is rational. QED.

## T0-13 Denominator bound — PROVED, REVIEWED (T0-GATE-A satisfied)

Claim: reduced denominator `q ≤ n·|R_n|`.
Proof: a simple path has `≤ |R_n|−1` edges, a simple cycle `≤ |R_n|` edges;
each edge has `a(e) ≤ n`. The extremal ratio's pre-reduction denominator
is `≤ n·|R_n|`; the reduced denominator divides it, hence is `≤ n·|R_n|`.
QED. This proof authorizes rational reconstruction with the bound.

## T0-14 Certificate implies `b_n* = p/q` — PROVED, REVIEWED

Claim: valid upper potential + valid transient or cyclic zero-slack lower
witness seals `b_n* = p/q`.
Proof: upper gives `b_n* ≤ p/q` (T0-05 direction: all paths nonnegative
slack). Transient witness path has ratio exactly `p/q`, so `≥`. Cyclic
witness: prefix + `k` cycle repetitions have ratios → `p/q`, so `≥`.
Both give equality. Nonempty rules (`sum_a > 0`, `sum_a_cycle > 0`)
exclude the degenerate zero path. QED.
