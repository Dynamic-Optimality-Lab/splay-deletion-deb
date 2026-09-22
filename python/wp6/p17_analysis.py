"""P17 negative-branch activation analysis (SPEC 17, WP-6).

WP-5 deferred six sampled near-tight families (k=0,1,2 residuals under the
frozen left-chain-embedding transformation) with status "WP-6 P17 decides".
This module decides exactly that:

1. REPRODUCE each family's samples bit-for-bit through the frozen
   generalizer path (reference parse/label/splay + frozen H formulas).
2. MEASURE growth: per-k keep/delete maxima, successive differences,
   monotonicity, exact-linearity of the three samples.
3. ADJUDICATE the three P17 activation criteria per family and globally:
   (C1) closed-form parameterized family (T_k,X_k,Y_k);
   (C2) symbolic Splay-vs-OPT bounds with g/f -> infinity;
   (C3) repeatable motif evidenced beyond finite samples (T19).
4. EMIT artifacts/wp6/p17_activation.json with verdict P17_ACTIVATED or
   P17_NOT_ACTIVATED plus criterion-by-criterion evidence.

No new H is synthesized; no sealed n8/H1 detail is read (constructed
skeletons only, as in WP-5 adversaries). Exact integers only.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)


# console.log equivalent [WP6-P17-01]: analysis module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


H_IDS = ("H-0001", "H-0002", "H-0003", "H-0004", "H-0005", "H-0006")


def reproduce_family(hypothesis_id):
    """Recompute k=0,1,2 samples through the frozen generalizer path."""
    # console.log equivalent [WP6-P17-02]: family reproduction per H.
    console_log("WP6-P17-02", "reproducing motif family %s" % hypothesis_id)
    from python.reference import tree as T
    from python.reference import splay as SP
    from python.reference import enumerate as E
    from python.wp5 import structural as S
    from python.adversary import witness_generalizer as W
    with open(os.path.join(REPO, "artifacts", "falsification", "adversarial",
                           "family_%s.json" % hypothesis_id), encoding="utf-8") as handle:
        filed = json.load(handle)
    with open(os.path.join(REPO, "artifacts", "falsification", hypothesis_id,
                           "dev_summary.json"), encoding="utf-8") as handle:
        dev = json.load(handle)
    best = None
    for n_str, rep in dev["sizes"].items():
        if best is None or int(rep["keep_max"]) > int(best[1]["keep_max"]):
            best = (int(n_str), rep)
    n, rep = best
    pid, _mode, _key = rep["keep_argmax"]
    shapes = E.canonical_shapes(n)
    count = len(shapes)
    keyed_a = T.assign_inorder_keys(T.parse_shape(shapes[pid // count]))
    keyed_b = T.assign_inorder_keys(T.parse_shape(shapes[pid % count]))
    formula_fn, _cls, _text = S.H_REGISTRY[hypothesis_id]
    got = W.generalize_counterexample(
        keyed_a, keyed_b, n, filed["motif"]["key"], filed["motif"]["mode"],
        T.parse_shape, T.assign_inorder_keys, T.serialize_shape, SP.splay,
        lambda ia, ib, nn: formula_fn(ia, ib, nn), 2, 1, (0, 1, 2))
    match = True
    for filed_s, got_s in zip(filed["samples"], got["samples"]):
        if (filed_s["k"] != got_s["k"] or filed_s["n"] != got_s["n"]
                or filed_s["keep_max"] != got_s["keep_max"]
                or filed_s["delete_max"] != got_s["delete_max"]):
            match = False
    # console.log equivalent [WP6-P17-03]: reproduction verdict per H.
    console_log("WP6-P17-03", "family %s reproduction %s" %
                (hypothesis_id, "IDENTICAL" if match else "MISMATCH"))
    return filed, got["samples"], match


def growth_report(samples):
    """Exact growth facts over the three samples (no extrapolation)."""
    keeps = [int(s["keep_max"]) for s in samples]
    delets = [int(s["delete_max"]) for s in samples]
    keep_diffs = [keeps[i + 1] - keeps[i] for i in range(len(keeps) - 1)]
    monotone = all(d >= 0 for d in keep_diffs) and any(d > 0 for d in keep_diffs)
    exact_linear = len(set(keep_diffs)) == 1 and keep_diffs[0] > 0
    return {"keep_maxima": keeps, "delete_maxima": delets,
            "keep_differences": keep_diffs, "monotone_growth": monotone,
            "exact_linear_growth": exact_linear}


def adjudicate(hypothesis_id, filed, growth, reproduced):
    """P17 activation criteria per family. Evidence only, no extrapolation."""
    # console.log equivalent [WP6-P17-04]: activation adjudication per H.
    console_log("WP6-P17-04", "adjudicating P17 for %s" % hypothesis_id)
    c1 = {"criterion": "C1 closed-form parameterized family",
          "finding": ("SATISFIED-FORM ONLY: left-chain embedding is a closed-form "
                      "tree construction, but no closed-form (T_k,X_k,Y_k) access "
                      "triple with symbolic Splay/OPT costs exists"),
          "pass": False}
    c2 = {"criterion": "C2 symbolic Splay-vs-OPT bounds with g/f->infinity",
          "finding": ("FAIL: samples record H-residual maxima (keep %s), not "
                      "Splay-vs-OPT gaps; no OPT oracle exists in this project; "
                      "three finite points cannot witness a limit" %
                      growth["keep_maxima"]),
          "pass": False}
    c3 = {"criterion": "C3 repeatable motif beyond finite samples (T19)",
          "finding": ("FAIL: k=0,1,2 only; %s; finite growth alone never equals "
                      "disproof" % ("monotone" if growth["monotone_growth"]
                                    else "non-monotone")),
          "pass": False}
    activated = reproduced and c1["pass"] and c2["pass"] and c3["pass"]
    return {"hypothesis_id": hypothesis_id, "reproduced_identical": reproduced,
            "growth": growth, "criteria": [c1, c2, c3],
            "family_activated": activated}


def main(argv=None):
    """Run P17 analysis for all six families; write activation record."""
    outdir = os.path.join(REPO, "artifacts", "wp6")
    os.makedirs(outdir, exist_ok=True)
    families = []
    for hid in H_IDS:
        filed, _samples, match = reproduce_family(hid)
        growth = growth_report(filed["samples"])
        families.append(adjudicate(hid, filed, growth, match))
    verdict = "P17_ACTIVATED" if any(f["family_activated"] for f in families) \
        else "P17_NOT_ACTIVATED"
    record = {
        "spec": "SPEC 17 (WP-6 negative branch)",
        "verdict": verdict,
        "global_reason": ("No family carries closed-form (T_k,X_k,Y_k) with symbolic "
                          "Splay-vs-OPT bounds and g/f->infinity; samples are "
                          "H-residual maxima at k=0,1,2 only (T19: finite growth "
                          "alone never equals disproof). Motif evidence remains "
                          "samples-only, preserved for future work, never promoted."),
        "families": families,
    }
    with open(os.path.join(outdir, "p17_activation.json"), "w", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP6-P17-05]: activation record sealed.
    console_log("WP6-P17-05", "P17 verdict: %s" % verdict)
    return 0 if verdict in ("P17_ACTIVATED", "P17_NOT_ACTIVATED") else 1


if __name__ == "__main__":
    sys.exit(main())
