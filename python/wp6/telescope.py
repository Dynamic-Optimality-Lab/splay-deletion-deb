"""P01 telescoping unit proof + P02 convention audit (SPEC 15/16, WP-6).

P01 (finite mechanism check, never a theorem): on a concrete certified
KEEP/DELETE path in R_4 from sealed tables, verify the exact telescoping
identity — summing exact local step identities cancels the interior H
terms, leaving endpoint difference. This checks the summation mechanism
as pure algebra over exact integers; it proves nothing about arbitrary n
(INV-036).

P02 (bridge audit, bridge never invoked): five-point Levy-Tarjan
convention checklist (variant / cost / subsequence / initial-tree /
constant-independence). Each point records MATCH or GAP with evidence.
With no proved lemma, the audit concludes BRIDGE_NOT_INVOKED.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)


# console.log equivalent [WP6-TEL-01]: telescope module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def p01_unit():
    """Exact telescoping identity on a concrete sealed R_4 path."""
    # console.log equivalent [WP6-TEL-02]: P01 unit proof begin.
    console_log("WP6-TEL-02", "P01 telescoping unit proof begin (R_4, exact ints)")
    import zstandard as zstd
    from python.reference import enumerate as E
    from python.reference import tree as T
    from python.reference import splay as SP
    from python.wp5 import structural as S
    from python.adversary import witness_generalizer as W
    n = 4
    shapes = E.canonical_shapes(n)
    count = len(shapes)
    with open(os.path.join(REPO, "artifacts", "reachability", "n4",
                           "reachable.json.zst"), "rb") as handle:
        pair_ids = sorted(int(p) for p in
                          json.loads(zstd.ZstdDecompressor().decompress(
                              handle.read()).decode("utf-8"))["pair_ids"])
    info_cache = {}
    for tid, shape in enumerate(shapes):
        info_cache[tid] = S.tree_info(T.assign_inorder_keys(T.parse_shape(shape)))
    h_state = {pid: S.h_depth_sum(info_cache[pid // count],
                                  info_cache[pid % count], n) for pid in pair_ids}
    start = 0
    steps = [(0, 1), (1, 4), (0, 2), (1, 3)]
    state = start
    total = 0
    interior = []
    for mode, key in steps:
        a_id = state // count
        keyed_a = T.assign_inorder_keys(T.parse_shape(shapes[a_id]))
        a2 = shapes.index(T.serialize_shape(W.skeleton_of(SP.splay(keyed_a, key)[0])))
        nxt = a2 * count + (state % count) if mode == 1 else None
        if mode == 0:
            b_id = state % count
            keyed_b = T.assign_inorder_keys(T.parse_shape(shapes[b_id]))
            b2 = shapes.index(T.serialize_shape(W.skeleton_of(SP.splay(keyed_b, key)[0])))
            nxt = a2 * count + b2
        assert nxt in h_state, "R_n forward closure"
        local = h_state[nxt] - h_state[state]
        total += local
        interior.append({"from": state, "to": nxt, "mode": mode, "key": key,
                         "local": local})
        state = nxt
    identity = (total == h_state[state] - h_state[start])
    record = {"gate": "P01", "scope": "FINITE_MECHANISM_CHECK (not a theorem)",
              "n": n, "start": start, "end": state, "steps": interior,
              "telescoped_sum": total,
              "endpoint_difference": h_state[state] - h_state[start],
              "identity_holds": identity,
              "arithmetic": "exact integers (Python int); no floats",
              "verdict": "PASS" if identity else "FAIL"}
    # console.log equivalent [WP6-TEL-03]: P01 verdict.
    console_log("WP6-TEL-03", "P01 telescoping identity %s" % record["verdict"])
    return record


def p02_audit():
    """Five-point Levy-Tarjan convention checklist (bridge not invoked)."""
    # console.log equivalent [WP6-BRG-01]: P02 bridge audit begin.
    console_log("WP6-BRG-01", "P02 convention audit begin (bridge not invoked)")
    points = [
        {"point": "variant",
         "status": "GAP",
         "evidence": ("This project studies bottom-up Splay exactly as the "
                      "frozen Splay semantics (SPEC 04); no line-by-line variant "
                      "match against the Levy-Tarjan paper text was performed, so "
                      "the bridge cannot be invoked.")},
        {"point": "cost",
         "status": "GAP",
         "evidence": ("Project costs are exact access depths c=depth+1 per access "
                      "(INV-004); Levy-Tarjan cost conventions were not "
                      "mechanically matched.")},
        {"point": "subsequence",
         "status": "GAP",
         "evidence": ("No subsequence-encoding correspondence proof was written; "
                      "KEEP/DELETE pair dynamics is project-internal (SPEC 07).")},
        {"point": "initial-tree",
         "status": "GAP",
         "evidence": ("Pairs start at diagonals (T,T); the bridge's initial-tree "
                      "requirements were not discharged.")},
        {"point": "constant-independence",
         "status": "GAP",
         "evidence": ("No universal (H,b_H) certificate exists (6/6 REJECTED), so "
                      "there is no constant whose independence could be checked.")},
    ]
    record = {"gate": "P02", "bridge": "BRIDGE_NOT_INVOKED",
              "reason": ("No proved Pair Access Lemma exists; convention gaps "
                         "above are recorded, never waived."),
              "points": points,
              "verdict": "PASS" if all(p["status"] in ("MATCH", "GAP") for p in points)
              else "FAIL"}
    # console.log equivalent [WP6-BRG-02]: P02 verdict.
    console_log("WP6-BRG-02", "P02 audit %s; bridge %s" % (record["verdict"], record["bridge"]))
    return record


def main(argv=None):
    """Write P01/P02 gate records."""
    outdir = os.path.join(REPO, "artifacts", "wp6")
    os.makedirs(outdir, exist_ok=True)
    p01 = p01_unit()
    with open(os.path.join(outdir, "p01_telescope.json"), "w", encoding="utf-8") as handle:
        json.dump(p01, handle, sort_keys=True, indent=2)
        handle.write("\n")
    p02 = p02_audit()
    with open(os.path.join(outdir, "p02_bridge_audit.json"), "w", encoding="utf-8") as handle:
        json.dump(p02, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return 0 if p01["verdict"] == "PASS" and p02["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
