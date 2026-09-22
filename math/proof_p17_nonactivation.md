# P17 non-activation analysis (SPEC 17, WP-6)

Status: `P17_NOT_ACTIVATED`. The six WP-5 sampled families remain
samples-only evidence. This document gives the criterion-by-criterion
reasons. Machine record: `artifacts/wp6/p17_activation.json`
(reproduction IDENTICAL 6/6 through the frozen generalizer path).

## Samples (exact, k=0,1,2 under left-chain embedding)

| H | keep maxima | delete maxima | monotone |
|---|-------------|---------------|----------|
| H-0001 | 6, 5, 6 | -2, 3, 6 | no |
| H-0002 | 13, 19, 26 | 12, 16, 22 | yes (diffs 6, 7) |
| H-0003 | 13, 19, 26 | 12, 16, 22 | yes (diffs 6, 7) |
| H-0004 | 10, 8, 7 | -2, -2, -2 | no |
| H-0005 | 9, 8, 7 | -2, -2, -2 | no |
| H-0006 | 7, 5, 8 | 3, 4, 7 | no |

## Why no family activates P17

C1 (closed-form `(T_k,X_k,Y_k)`): the left-chain embedding is a
closed-form *tree* construction, but P17 needs a closed-form access
triple with symbolic Splay/OPT costs. None exists in the record.

C2 (symbolic `Splay(X_k)<=f(k)`, `Splay(Y_k)>=g(k)`, `g/f->infinity`):
the samples record H-residual maxima, not Splay-vs-OPT gaps. This
project has no OPT oracle and no Splay/OPT gap data at any size.
Three finite points cannot witness a limit in any case.

C3 (repeatable motif beyond finite samples, T19): k=0,1,2 only, and
four of six families are non-monotone. Finite growth alone never
equals disproof — even the monotone H-0002/H-0003 legs (diffs 6, 7,
not exactly linear) stay finite observations.

## Consequence

No `DYNAMIC_OPTIMALITY_DISPROVED` claim. The families are preserved
(`artifacts/falsification/adversarial/family_H-*.json`) as
`POTENTIAL_UNBOUNDED_PATTERN_FOUND (samples only)` for future work.
A future activation would need: an OPT-side quantity, symbolic bounds,
and a limit argument — none of which this data supplies.
