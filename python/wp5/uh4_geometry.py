"""Fresh canonical b_H=2 geometry for the WP-5 UH-4 compliance repair.

SA-01 greater-than branch (b_H=2 > every sealed b_n*, n=2..7): recompute the
exact reachable Pair-Access canonical potentials U_2/V_2 at the hypothesis's
own universal b_H=2/1 from the sealed transition/reachability tables. These
are a DIFFERENT Bellman problem from the WP-3 b_n* discovery tables and are
written to artifacts/potentials/n{n}/hypothesis_bH/ plus a versioned
companion bH_geometry.v1.json (schema BHG-v0.1).

Exact integer arithmetic only. No floats. Never reads n8/H1 detail records.
Shared b-geometry: computed once per n (property of (R_n, b=2)), not per H.
"""
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from python.reference import canonical as cn  # noqa: E402
from python.reference import solve_small as sv  # noqa: E402

# console.log equivalent [WP5-UH4-02]: geometry module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


B_H_P, B_H_Q = 2, 1
SIZES = (2, 3, 4, 5, 6, 7)
SCHEMA_ID = "BHG-v0.1"

NORMATIVE_FILES = [
    "IMPLEMENTATION_SPEC.md",
    "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.1.md",
    "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.2.md",
    "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.3.md",
    "SPLAY_AM_PD_IMPLEMENTATION_SPEC_v0.1.4.md",
    "WorkPlan.md",
    "Path.md",
]


def verify_normative_hashes():
    """SHA-256 over the frozen normative stack (read-only)."""
    # console.log equivalent [WP5-UH4-01]: normative hash verification.
    console_log("WP5-UH4-01", "verifying normative hashes")
    out = {}
    for name in NORMATIVE_FILES:
        path = os.path.join(REPO, name)
        with open(path, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        out[name] = digest
        # console.log equivalent [WP5-UH4-01]: per-file hash emission.
        console_log("WP5-UH4-01", "%s sha256=%s" % (name, digest))
    return out


def assert_no_holdout_path(*paths):
    """Refuse any n8 / hidden-bank path (defensive; repair uses n<=7 only)."""
    for path in paths:
        low = path.replace("\\", "/").lower()
        if "/n8" in low or "holdout" in low or "hidden" in low:
            raise AssertionError("holdout path refused: %s" % path)


def build_bh_geometry(n):
    """Compute U_2/V_2/G_2 for one n and write hypothesis_bH artifacts."""
    # console.log equivalent [WP5-UH4-03]: b=2 geometry start per n.
    console_log("WP5-UH4-03", "b=2 geometry start n=%d" % n)
    trans_dir = os.path.join(REPO, "artifacts", "transitions", "n%d" % n)
    reach_dir = os.path.join(REPO, "artifacts", "reachability", "n%d" % n)
    assert_no_holdout_path(trans_dir, reach_dir)
    tables = sv.load_tables(trans_dir)
    reach = sv.load_reach(reach_dir, tables.tree_count)
    csr = sv.build_csr(tables, reach)
    # console.log equivalent [WP5-UH4-04]: U_2 computation start/end.
    console_log("WP5-UH4-04", "U_2 computation start n=%d R=%d" % (n, csr.size))
    U, _tight_u = cn.compute_U(csr, B_H_P, B_H_Q)
    console_log("WP5-UH4-04", "U_2 computation end n=%d maxU=%d" % (n, max(U)))
    # console.log equivalent [WP5-UH4-05]: V_2 computation start/end.
    console_log("WP5-UH4-05", "V_2 computation start n=%d R=%d" % (n, csr.size))
    V, _argmax_v = cn.compute_V(csr, B_H_P, B_H_Q)
    console_log("WP5-UH4-05", "V_2 computation end n=%d maxV=%d" % (n, max(V)))
    outdir = os.path.join(REPO, "artifacts", "potentials", "n%d" % n, "hypothesis_bH")
    summary = cn.build_potentials(n, tables, reach, B_H_P, B_H_Q, outdir)
    # console.log equivalent [WP5-UH4-06]: primary canonical verification.
    console_log("WP5-UH4-06", "primary canonical verification n=%d (in-build asserts + witness recompute)" % n)
    for i in range(csr.size):
        if V[i] < 0:
            raise AssertionError("V_2 negative")
        if V[i] > U[i]:
            raise AssertionError("V_2 > U_2")
    # console.log equivalent [WP5-UH4-06]: primary PASS emission.
    console_log("WP5-UH4-06", "primary canonical verification n=%d PASS R=%d" % (n, csr.size))
    companion = {
        "schema": SCHEMA_ID,
        "n": n,
        "b_H": {"p": "2", "q": "1"},
        "b_role": ("universal hypothesis b_H (SA-01 greater-than branch); "
                   "NOT WP-3 b_n* discovery geometry"),
        "reachable_pair_count": csr.size,
        "tree_count": tables.tree_count,
        "state_ordering": "ascending pair_id; pair_id = a_id*tree_count + b_id",
        "arithmetic": "exact integers (Python int); no floating point",
        "construction_method": ("sealed transitions+reachability -> "
                                "solve_small.build_csr -> canonical.compute_U/compute_V "
                                "at b=2/1 -> canonical.build_potentials"),
        "spec_refs": ["WorkPlan.md#7 WP-5 UH-3/UH-4", "SA-01 greater-than branch"],
        "files": {
            "U": {"path": "U.json.zst", "logical_sha256": summary["logical_U_sha256"]},
            "V": {"path": "V.json.zst", "logical_sha256": summary["logical_V_sha256"]},
            "G": {"path": "G.json.zst", "logical_sha256": summary["logical_G_sha256"]},
        },
        "primary_summary": summary,
    }
    with open(os.path.join(outdir, "bH_geometry.v1.json"), "w", encoding="utf-8") as handle:
        json.dump(companion, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP5-UH4-07]: geometry artifacts sealed per n.
    console_log("WP5-UH4-07", "geometry artifacts sealed n=%d R=%d forced=%d" %
                (n, csr.size, summary["forced_count"]))
    return companion


def main(argv=None):
    """Build b=2 geometry for all certified sizes; emit corrective run log head."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="2 3 4 5 6 7")
    args = ap.parse_args(argv)
    normative = verify_normative_hashes()
    companions = {}
    for n in [int(s) for s in args.sizes.split()]:
        companions[str(n)] = build_bh_geometry(n)
    log = {"corrective": "WP-5 UH-4 b_H=2 canonical sandwich compliance repair",
           "normative_sha256": normative,
           "b_H": {"p": "2", "q": "1"},
           "geometry": {n: {"reachable_pair_count": c["reachable_pair_count"],
                            "U_sha256": c["files"]["U"]["logical_sha256"],
                            "V_sha256": c["files"]["V"]["logical_sha256"],
                            "G_sha256": c["files"]["G"]["logical_sha256"]}
                        for n, c in companions.items()}}
    os.makedirs(os.path.join(REPO, "artifacts", "logs"), exist_ok=True)
    with open(os.path.join(REPO, "artifacts", "logs", "wp5_uh4_corrective.json"),
              "w", encoding="utf-8") as handle:
        json.dump(log, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP5-UH4-08]: corrective run log head written.
    console_log("WP5-UH4-08", "corrective run log head written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
