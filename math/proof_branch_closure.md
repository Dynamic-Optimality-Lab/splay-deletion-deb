# Positive-branch closure (SPEC 15/16, WP-6)

Status: `CLOSED_NO_SUBJECT`. This document records why no P15 lemma is
proved. It is a closure record, not a proof.

## Premise check

P15 requires a surviving universal hypothesis: UH-0 through UH-8 all
decisive-PASS for one frozen `H`. Frozen verdicts
(`artifacts/hypotheses/H-000{1..6}.uh.json`, `H-*.uh4.json`):

| ID | UH-4 | UH-5 |
|----|------|------|
| H-0001 | REJECTED (UPPER from n=5) | REJECTED_EARLIER_AT_UH4 |
| H-0002 | REJECTED (UPPER from n=4) | REJECTED_EARLIER_AT_UH4 |
| H-0003 | REJECTED (UPPER from n=4) | REJECTED_EARLIER_AT_UH4 |
| H-0004 | REJECTED (LOWER from n=5) | REJECTED_EARLIER_AT_UH4 |
| H-0005 | REJECTED (LOWER from n=5) | REJECTED_EARLIER_AT_UH4 |
| H-0006 | REJECTED (UPPER from n=3) | REJECTED_EARLIER_AT_UH4 |

Survivor set: empty.

## Lemma dispositions

- P15-01 (well-definedness on declared domain): VACUOUS_NO_SUBJECT.
- P15-02 (`H(T,T)=0`): VACUOUS_NO_SUBJECT (finite diagonal zeros hold
  6/6 at UH-1 but are development evidence, never premises).
- P15-03 (`H>=0`): VACUOUS_NO_SUBJECT (same; UH-2 finite only).
- P15-04 (KEEP): VACUOUS_NO_SUBJECT (all six fail exact KEEP residuals).
- P15-05 (DELETE): VACUOUS_NO_SUBJECT (H-0006 fails DELETE at n=3;
  the rest fail earlier gates, which already decide).
- P16 (telescoping): VACUOUS_NO_SUBJECT — no proved lemma supplies
  summable premises. The summation mechanism alone is unit-checked in
  P01 (`math/proof_telescoping_unit.md`) as finite algebra.

## What would reopen the branch

A new hypothesis ID with UH-0..UH-8 all PASS under a new holdout plan
(T18). Nothing in the sealed record qualifies. Machine record:
`artifacts/wp6/positive_branch_closure.json`.
