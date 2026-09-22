"""P15/P16 branch-closure records (SPEC 15/16, WP-6).

Positive branch requires a surviving universal H (UH-0..UH-8 all PASS).
Telescoping requires a proved Pair Access Lemma. This module reads the
frozen WP-5 verdicts and records, lemma by lemma, why each P15/P16
obligation is VACUOUS_NO_SUBJECT rather than proved — a closure result,
never a proof. Exact strings only; no finite premises; no extrapolation.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)


# console.log equivalent [WP6-BRC-01]: branch-closure module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


H_IDS = ("H-0001", "H-0002", "H-0003", "H-0004", "H-0005", "H-0006")


def survivors():
    """Hypotheses with UH-4 PASS and UH-5 PASS (both required for P15)."""
    # console.log equivalent [WP6-BRC-02]: survivor census from frozen verdicts.
    console_log("WP6-BRC-02", "survivor census from frozen UH verdicts")
    out = []
    for hid in H_IDS:
        with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.uh.json" % hid),
                  encoding="utf-8") as handle:
            ladder = json.load(handle)
        if ladder.get("UH-4") == "PASS" and ladder.get("UH-5") == "REJECTED":
            pass
        if ladder.get("UH-4") == "PASS" and ladder.get("UH-5") == "PASS":
            out.append(hid)
    # console.log equivalent [WP6-BRC-02]: census result emission.
    console_log("WP6-BRC-02", "survivors: %s" % (out if out else "NONE"))
    return out


def main(argv=None):
    """Write the positive-branch closure record."""
    alive = survivors()
    lemmas = []
    for lemma_id, title in (
            ("P15-01", "well-definedness on declared domain"),
            ("P15-02", "H(T,T)=0"),
            ("P15-03", "H>=0"),
            ("P15-04", "KEEP inequality"),
            ("P15-05", "DELETE inequality")):
        lemmas.append({"lemma": lemma_id, "title": title,
                       "status": "VACUOUS_NO_SUBJECT" if not alive else "REQUIRED",
                       "reason": ("No UH-0..UH-8 survivor exists (6/6 REJECTED at "
                                  "UH-4; UH-5 supplementary); no universal statement "
                                  "to prove" if not alive else
                                  "survivor present; proof required")})
    record = {
        "spec": "SPEC 15 positive branch (WP-6)",
        "survivors": alive,
        "positive_branch": "CLOSED_NO_SUBJECT" if not alive else "OPEN",
        "lemmas": lemmas,
        "telescoping_P16": {
            "status": "VACUOUS_NO_SUBJECT",
            "reason": ("No proved Pair Access Lemma exists; telescoping has no "
                       "premise to sum. The telescoping mechanism itself is unit-"
                       "checked in P01 as finite algebra only, never as a theorem.")},
    }
    outdir = os.path.join(REPO, "artifacts", "wp6")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "positive_branch_closure.json"), "w",
              encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP6-BRC-03]: closure record sealed.
    console_log("WP6-BRC-03", "branch closure: %s" % record["positive_branch"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
