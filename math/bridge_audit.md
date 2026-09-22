# P02 Levy-Tarjan bridge audit (bridge not invoked)

With no proved Pair Access Lemma, the bridge from approximate
monotonicity to dynamic optimality has no premise. This audit records
the five convention checkpoints as GAPs (never waived) and concludes
`BRIDGE_NOT_INVOKED`. Machine record:
`artifacts/wp6/p02_bridge_audit.json`.

1. Variant: no line-by-line match of project Splay semantics against
   the Levy-Tarjan paper text was performed. GAP.
2. Cost: project costs are exact access depths (`c=depth+1`, INV-004);
   no mechanical match against bridge cost conventions. GAP.
3. Subsequence: no subsequence-encoding correspondence proof. GAP.
4. Initial-tree: diagonal-start pairs do not discharge the bridge's
   initial-tree requirements. GAP.
5. Constant-independence: no universal `(H,b_H)` certificate exists,
   so independence of any constant is moot. GAP.

Final theorem form (`Splay(X) <= C·OPT(X)+O(n)` or matched variant) is
therefore neither stated nor approached. No crossing in either
direction is claimed on the basis of this audit.
