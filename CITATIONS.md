# Citations (frozen source ledger)

Local copies and hashes: `external/MANIFEST.json`, `external/papers/`.

## L1 — Sleator and Tarjan (1985)

Daniel D. Sleator and Robert Endre Tarjan. "Self-Adjusting Binary Search
Trees." Journal of the ACM, 32(3):652-686, 1985. DOI: 10.1145/3828.3835.

Sections relied upon: definition of bottom-up splaying (zig, zig-zig, zig-zag),
amortized `O(log n)` access lemma statement. Access restricted (ACM paywall);
no local copy is redistributed. Reliance is limited to the widely reproduced
algorithmic definition, which is additionally cross-checked by hand fixtures
and three independent implementations in WP-1.

## L2 — Levy and Tarjan (arXiv:1907.06310v3)

Caleb C. Levy and Robert E. Tarjan. "A Foundation for Proving Splay is
Dynamically Optimal." arXiv:1907.06310v3.

Sections relied upon: Splay cost convention used for approximate monotonicity;
definition of approximate monotonicity; monotonicity-to-optimality bridge;
`G_4` strong-connectivity statement and `G_3` non-connectivity note;
subsequence-overhead / competitive-ratio equivalence.

## L3 — Chmel et al. (2026, arXiv:2607.18498)

Petr Chmel, Bernhard Haeupler, Richard Hladik, Michal Koucky, Antti Roeyskoe,
Vaclav Rozhon, Ondrej Sladky, and Robert E. Tarjan. "Splay trees are almost
dynamically optimal." arXiv:2607.18498, 2026.

Sections relied upon: current competitive-ratio theorem context
(`O(log log n (log log log n)^2)`); structural feature ideas for WP-4.
Context only; not a logical premise of the paired-game correctness proof.
