"""FPATH source/target orientation regression (SA-02 pre-flight, step 2).

Frozen criterion for edge source_state_id -> target_state_id:
    U[source_state_id] + L(edge) - V[target_state_id] == 0
where L = p*a - q*y (exact integer).

This file MUST use explicit `source_state_id` / `target_state_id` names.
Ambiguous single-letter `s`/`t` variable names are FORBIDDEN in this file
(enforced by test_fpath_no_ambiguous_names below scanning its own bytes).

Checks:
  ORIENT-01  sealed FPATH == correct-orientation set for every certified n.
  ORIENT-02  swapped orientation disagrees somewhere on full edge set
             (proves the test is orientation-sensitive, not vacuous).
  ORIENT-03  every sealed FPATH edge is zero-reduced tight
             (U[target]-U[source]==L) — corollary of the criterion.
  ORIENT-04  no ambiguous s/t naming in this file (self-scan).
  ORIENT-05  hand-worked unit case with explicit integers.

Exit 0 iff all pass. Step-logged. Read-only: never writes sealed artifacts.
"""

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


PASS = []
FAIL = []


def check(test_id, cond, detail=""):
    if cond:
        PASS.append(test_id)
        console_log(test_id, "PASS %s" % detail)
    else:
        FAIL.append(test_id)
        console_log(test_id, "FAIL %s" % detail)


def load_integer_table(path, field):
    import zstandard as zstd
    import json as json_mod
    with open(path, "rb") as handle:
        rows = json_mod.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    return {row["pair_id"]: int(row[field]) for row in rows}


def sealed_b_value(cert_dir):
    import json as json_mod
    with open(os.path.join(cert_dir, "bn_certificate.json"), encoding="utf-8") as handle:
        cert = json_mod.load(handle)
    return int(cert["b"]["p"]), int(cert["b"]["q"])


def test_orientation_per_size(target_size):
    from python.audit import graph as audit_graph
    import zstandard as zstd
    import json as json_mod
    base = os.path.join(REPO, "artifacts")
    cert_dir = os.path.join(base, "certificates", "n%d" % target_size)
    pot_dir = os.path.join(base, "potentials", "n%d" % target_size)
    crit_dir = os.path.join(base, "critical", "n%d" % target_size)
    tables = audit_graph.build_tables(target_size)
    reach = audit_graph.build_reachability(tables)
    prime_p, prime_q = sealed_b_value(cert_dir)
    table_U = load_integer_table(os.path.join(pot_dir, "U.json.zst"), "U_scaled")
    table_V = load_integer_table(os.path.join(pot_dir, "V.json.zst"), "V_scaled")
    with open(os.path.join(crit_dir, "forced_delta_edges.json.zst"), "rb") as handle:
        sealed_rows = json_mod.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    sealed_fpath_keys = set(
        (row["source_pair_id"], row["mode"], row["key"])
        for row in sealed_rows if "FPATH" in row["provenance"]
    )
    correct_orientation_keys = set()
    swapped_orientation_keys = set()
    correct_full_count = 0
    swapped_full_count = 0
    tight_ok = True
    for source_state_id in reach.pair_ids:
        for mode_code in (audit_graph.KEEP, audit_graph.DELETE):
            mode_name = "KEEP" if mode_code == audit_graph.KEEP else "DELETE"
            for access_key in range(1, target_size + 1):
                target_state_id, access_cost, paired_cost = audit_graph.successor(
                    tables, source_state_id, mode_code, access_key)
                scaled_slack = prime_p * access_cost - prime_q * paired_cost
                correct_holds = (
                    table_U[source_state_id] + scaled_slack - table_V[target_state_id] == 0
                )
                swapped_holds = (
                    table_U[target_state_id] + scaled_slack - table_V[source_state_id] == 0
                )
                if correct_holds:
                    correct_full_count += 1
                if swapped_holds:
                    swapped_full_count += 1
                is_zero_reduced = (scaled_slack == table_U[target_state_id] - table_U[source_state_id])
                if correct_holds and is_zero_reduced:
                    correct_orientation_keys.add((source_state_id, mode_name, access_key))
                if swapped_holds and is_zero_reduced:
                    swapped_orientation_keys.add((source_state_id, mode_name, access_key))
    # ORIENT-01: sealed FPATH equals correct-orientation zero-reduced set.
    check(
        "ORIENT-01-n%d" % target_size,
        sealed_fpath_keys == correct_orientation_keys,
        "n=%d sealed=%d correct=%d" % (target_size, len(sealed_fpath_keys), len(correct_orientation_keys)),
    )
    # ORIENT-03: every sealed FPATH edge is tight.
    for row in sealed_rows:
        if "FPATH" not in row["provenance"]:
            continue
        source_state_id = row["source_pair_id"]
        target_state_id = row["target_pair_id"]
        scaled = int(row["scaled_slack"])
        if table_U[target_state_id] - table_U[source_state_id] != scaled:
            tight_ok = False
    check("ORIENT-03-n%d" % target_size, tight_ok, "n=%d tight" % target_size)
    return correct_full_count, swapped_full_count


def test_hand_worked_unit():
    # Explicit integers: source U=5, edge L=3, target V=8 -> 5+3-8==0 (FPATH).
    # Swapped: U[target]=7, V[source]=2 -> 7+3-2==8 != 0 (not FPATH).
    source_U = 5
    target_U = 7
    source_V = 2
    target_V = 8
    edge_L = 3
    correct_value = source_U + edge_L - target_V
    swapped_value = target_U + edge_L - source_V
    check("ORIENT-05", correct_value == 0 and swapped_value != 0,
          "correct=%d swapped=%d" % (correct_value, swapped_value))


def test_no_ambiguous_names():
    import ast as ast_mod
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        own_text = handle.read()
    tree = ast_mod.parse(own_text)
    bad = []
    for node in ast_mod.walk(tree):
        if isinstance(node, ast_mod.Name) and node.id in ("s", "t"):
            bad.append("Name:%s@%d" % (node.id, node.lineno))
        if isinstance(node, ast_mod.arg) and node.arg in ("s", "t"):
            bad.append("arg:%s@%d" % (node.arg, node.lineno))
        if isinstance(node, (ast_mod.FunctionDef, ast_mod.AsyncFunctionDef)):
            if node.name in ("s", "t"):
                bad.append("func:%s@%d" % (node.name, node.lineno))
    check("ORIENT-04", len(bad) == 0, "bad=%s" % (bad[:5],))


def main(argv=None):
    console_log("ORIENT-00", "FPATH orientation regression begin")
    totals = {}
    for target_size in (2, 3, 4, 5, 6, 7):
        correct_full_count, swapped_full_count = test_orientation_per_size(target_size)
        totals[target_size] = (correct_full_count, swapped_full_count)
    # ORIENT-02: orientation-sensitive somewhere (full edge sets differ).
    sensitive = any(corr != swap for (corr, swap) in totals.values())
    check("ORIENT-02", sensitive, str(totals))
    test_hand_worked_unit()
    test_no_ambiguous_names()
    console_log("ORIENT-99", "pass=%d fail=%d" % (len(PASS), len(FAIL)))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
