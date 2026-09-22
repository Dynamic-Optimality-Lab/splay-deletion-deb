# P01 telescoping unit (finite mechanism check, not a theorem)

Gate P01 checks the summation mechanism of telescoping as pure algebra
over exact integers on one concrete certified path. Scope is explicitly
`FINITE_MECHANISM_CHECK`: it establishes that *if* exact local step
identities held along a KEEP/DELETE encoding, their sum would telescope.
It proves nothing about arbitrary `n` (INV-036) and is never cited as a
lemma premise.

## Instance

- Domain: reachable pairs `R_4` (196 states), sealed tables.
- Potential: H-0001 depth-sum evaluated exactly per state.
- Path: pid 0 --K1--> s1 --D4--> s2 --K2--> s3 --D3--> s4
  (each step forward-closed in `R_4`, checked at runtime).
- Local identity per step: `e_i = H(s_{i+1}) - H(s_i)`, exact integer.

## Identity

`sum_i e_i = H(s_4) - H(s_0)` holds by cancellation of the three
interior terms. Machine record `artifacts/wp6/p01_telescope.json`
stores every step `(from, to, mode, key, local)`, the telescoped sum,
the endpoint difference, and the boolean comparison (PASS).

## Non-goals (explicit)

No case partition (root/zig/LL/RR/LR/RL) is discharged here; no domain
declaration (`ALL_PAIRS` vs `REACHABLE_PAIRS`) is made; no cost-convention
match is performed; no `b`-universality argument is given. Those belong
to P15/P16 proper and are VACUOUS_NO_SUBJECT in this run.
