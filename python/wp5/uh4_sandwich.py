"""Primary UH-4 sandwich evaluation at b_H=2 (WP-5 compliance repair).

For every frozen candidate H-0001..H-0006 and every reachable state of every
certified n=2..7, checks V_2(s) <= H(s) <= U_2(s) exactly against the
fresh independently-verified b=2 canonical geometry (never U_{b_n*}).
Writes artifacts/hypotheses/H-*.uh4.json (schema UH4-v0.1) and updates the
H-*.uh.json ladder records honestly: UH-4 PASS preserves UH-5 REJECTED as
decisive; UH-4 FAIL becomes the first rejection with the UH-5 counterexample
preserved as supplementary evidence. Frozen H formulas/b_H/IDs untouched;
existing UH-5 counterexamples never rewritten.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from python.wp5 import falsify as F  # noqa: E402
from python.wp5 import structural as S  # noqa: E402

# console.log equivalent [WP5-UH4-14]: sandwich module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


H_IDS = ("H-0001", "H-0002", "H-0003", "H-0004", "H-0005", "H-0006")
SIZES = (2, 3, 4, 5, 6, 7)
SCHEMA_ID = "UH4-v0.1"


def load_uv(n):
    """Load independently-verified U_2/V_2 tables (exact ints keyed by pair_id)."""
    import zstandard as zstd
    base = os.path.join(REPO, "artifacts", "potentials", "n%d" % n, "hypothesis_bH")
    if "holdout" in base.replace("\\", "/").lower():
        raise AssertionError("holdout path refused")
    with open(os.path.join(base, "U.json.zst"), "rb") as handle:
        u_rows = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    with open(os.path.join(base, "V.json.zst"), "rb") as handle:
        v_rows = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    U = {r["pair_id"]: int(r["U_scaled"]) for r in u_rows}
    V = {r["pair_id"]: int(r["V_scaled"]) for r in v_rows}
    return U, V


def evaluate_candidate(hypothesis_id):
    """Full UH-4 matrix for one frozen candidate. Returns (uh4_record, verdict)."""
    from python.reference import enumerate as E
    per_n = []
    overall_fail = False
    for n in SIZES:
        # console.log equivalent [WP5-UH4-14]: candidate UH-4 start per H/n.
        console_log("WP5-UH4-14", "candidate UH-4 start %s n=%d" % (hypothesis_id, n))
        U, V = load_uv(n)
        shapes, count, _after, _cost, pair_ids = F.load_domain_tables(n)
        assert pair_ids == sorted(pair_ids)
        assert set(U) == set(pair_ids) and set(V) == set(pair_ids)
        h_table = F.build_h_table(hypothesis_id, n, shapes, count, pair_ids)
        lower = 0
        upper = 0
        max_lower_margin = 0
        max_upper_margin = 0
        first = None
        for pid in pair_ids:
            h = h_table[pid]
            u = U[pid]
            v = V[pid]
            if h < v:
                lower += 1
                margin = v - h
                if margin > max_lower_margin:
                    max_lower_margin = margin
                if first is None:
                    a_id, b_id = divmod(pid, count)
                    first = {"pair_id": pid, "kind": "LOWER",
                             "A_shape": shapes[a_id], "B_shape": shapes[b_id],
                             "H": h, "U_2": u, "V_2": v, "signed_diff": h - v}
            if h > u:
                upper += 1
                margin = h - u
                if margin > max_upper_margin:
                    max_upper_margin = margin
                if first is None:
                    a_id, b_id = divmod(pid, count)
                    first = {"pair_id": pid, "kind": "UPPER",
                             "A_shape": shapes[a_id], "B_shape": shapes[b_id],
                             "H": h, "U_2": u, "V_2": v, "signed_diff": h - u}
        status = "PASS" if (lower == 0 and upper == 0) else "FAIL"
        if status == "FAIL":
            overall_fail = True
        per_n.append({"n": n, "states_checked": len(pair_ids),
                      "lower_violations": lower, "upper_violations": upper,
                      "max_lower_margin": max_lower_margin,
                      "max_upper_margin": max_upper_margin,
                      "first_violation": first, "status": status})
        # console.log equivalent [WP5-UH4-15]: sandwich completion per H/n.
        console_log("WP5-UH4-15", "sandwich complete %s n=%d lower=%d upper=%d %s" %
                    (hypothesis_id, n, lower, upper, status))
    verdict = "FAIL" if overall_fail else "PASS"
    record = {"schema": SCHEMA_ID, "hypothesis_id": hypothesis_id,
              "b_H": {"p": "2", "q": "1"},
              "geometry": "artifacts/potentials/n{n}/hypothesis_bH (b=2 canonical; NOT b_n*)",
              "per_n": per_n, "verdict": verdict}
    return record, verdict


def freeze_and_update_ladder(hypothesis_id, record, verdict):
    """Write H-*.uh4.json; update H-*.uh.json with honest first-failure order."""
    hyp_dir = os.path.join(REPO, "artifacts", "hypotheses")
    uh4_path = os.path.join(hyp_dir, "%s.uh4.json" % hypothesis_id)
    with open(uh4_path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP5-UH4-16]: counterexample freeze if any.
    if verdict == "FAIL":
        first_n = next(r for r in record["per_n"] if r["status"] == "FAIL")
        console_log("WP5-UH4-16", "counterexample frozen %s n=%d pid=%d kind=%s" %
                    (hypothesis_id, first_n["n"],
                     first_n["first_violation"]["pair_id"],
                     first_n["first_violation"]["kind"]))
    else:
        # console.log equivalent [WP5-UH4-16]: no-counterexample emission.
        console_log("WP5-UH4-16", "no UH-4 counterexample %s (PASS all n)" % hypothesis_id)
    uh_path = os.path.join(hyp_dir, "%s.uh.json" % hypothesis_id)
    with open(uh_path, encoding="utf-8") as handle:
        ladder = json.load(handle)
    assert ladder["UH-5"] == "REJECTED", "UH-5 scientific verdict must be preserved"
    ladder["UH-4-artifact"] = "%s.uh4.json" % hypothesis_id
    if verdict == "PASS":
        ladder["UH-4"] = "PASS"
    else:
        ladder["UH-4"] = "REJECTED"
        ladder["UH-5"] = ("REJECTED_EARLIER_AT_UH4 "
                          "(first decisive rejection at UH-4; UH-5 counterexample "
                          "preserved as supplementary falsification evidence)")
    with open(uh_path, "w", encoding="utf-8") as handle:
        json.dump(ladder, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return ladder


def main(argv=None):
    """Evaluate all six frozen candidates; report verdict table."""
    verdicts = {}
    for hid in H_IDS:
        record, verdict = evaluate_candidate(hid)
        freeze_and_update_ladder(hid, record, verdict)
        verdicts[hid] = verdict
    for hid in H_IDS:
        # console.log equivalent [WP5-UH4-15]: verdict-table emission.
        console_log("WP5-UH4-15", "UH-4 verdict %s: %s" % (hid, verdicts[hid]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
