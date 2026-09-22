# WP-6 terminal answers (reconstructed from WorkPlan §8 / §12 / §§18–19)

Note: the full SPEC §§25–36 question text is not present in the frozen
repository file set. The 15 questions below are reconstructed from the
normative acceptance gates (WorkPlan §8 scope/files/gates, §12 "WP-6
done", IMPLEMENTATION_SPEC §§14/18/19) and answered with artifact
evidence. No question is answered from expectation; every answer points
at a sealed or logged record.

1. What is the single true claim level? `FINITE_EXACT_BN_RESULTS`
   (`artifacts/seal/FINAL_RESULT.json`, schema-validated).
2. Why not higher? Zero UH survivors (6/6 REJECTED at UH-4); no proved
   lemma (P15 closed); no proved unbounded family (P17 not activated).
3. Why not lower? Exact `b_n*` sealed for n=2..7 with independent PASS,
   canonical potentials and critical derivatives complete — all verified
   (S02 18/18).
4. Positive branch status? `CLOSED_NO_SUBJECT` (P15-01..05 vacuous;
   `artifacts/wp6/positive_branch_closure.json`).
5. Telescoping status? Mechanism unit-checked as finite algebra (P01
   PASS); no premises to sum (P16 vacuous).
6. Levy–Tarjan bridge status? `BRIDGE_NOT_INVOKED`; five convention
   gaps recorded, never waived (`artifacts/wp6/p02_bridge_audit.json`).
7. Negative branch status? `P17_NOT_ACTIVATED`; six families reproduced
   identical, all three activation criteria fail each
   (`artifacts/wp6/p17_activation.json`).
8. Holdout status? n8 firewall EMPTY, H1 firewall EMPTY; nothing
   consumed; repair and WP-6 code reference no holdout detail.
9. What was independently verified? b_n* certs, U/V/G tables, critical
   objects (S02 18/18); b=2 geometry (UH4, 6/6); UH-4 verdicts 36/36
   cells; FINAL_RESULT recompute identical (S01 + INV-040).
10. Exactness status? S03 zero violations in sealed exact fields
    (string-encoded integers; only `forced_fraction` display floats).
11. Reproduction status? S01 PASS: fresh worktree rebuild n=2..6
    byte-identical 15/15; sealed n=7 cert verified; result recomputed
    identical (`artifacts/logs/reproduce.json`).
12. Threat/invariant status? T1–T22 all COVERED; INV-035..040 all HOLDS
    (`artifacts/wp6/s02_s03_sweep.json`).
13. Release integrity? Deterministic archive
    `SPLAY-AM-PD-v0.1.tar.zst` + `.sha256`; 778-entry MANIFEST.sha256
    (777 members + archive; manifest never lists itself); normative_spec_set embedded (v0.1 +
    SA-01..SA-04 pins).
14. AI-use declaration (§29)? All WP-6 code, analysis, and prose were
    produced by an AI coding agent under the owner's frozen-plan
    instruction; every computation was executed (not asserted) with
    exit-zero evidence; no cost/reachability semantics were changed, no
    hypothesis mutated unversioned, no counterexample suppressed, no
    finite evidence promoted. Human review: owner-gated via commit
    history and this record.
15. What remains open? A future hypothesis ID with full UH survival
    (new holdout plan per T18) could reopen P15; a future Splay/OPT gap
    family with symbolic bounds could reopen P17. This seal advances
    neither and blocks neither — it records exactly what exists.
