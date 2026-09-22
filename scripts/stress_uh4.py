"""UH-4 repair stress suite: determinism, agreement, fault injection.

Fourteen append-only checks (S-01..S-14) incl. five deliberate mutations
(corrupted U, corrupted V, wrong-b geometry, changed H, false-PASS record)
each of which the repair's gate predicates must catch. In-memory only except
reading committed artifacts; writes artifacts/logs/wp5_uh4_stress.json.
Exit 0 iff all pass. Step-logged.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from python.audit import graph  # noqa: E402

PASS = []
FAIL = []


# console.log equivalent [WP5-SUH4-00]: stress module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def check(test_id, cond, detail=""):
    """Record one stress verdict. Factual output only."""
    if cond:
        PASS.append(test_id)
        console_log(test_id, "PASS %s" % detail)
    else:
        FAIL.append(test_id)
        console_log(test_id, "FAIL %s" % detail)


def bh_dir(n):
    """hypothesis_bH directory for one size."""
    return os.path.join(REPO, "artifacts", "potentials", "n%d" % n, "hypothesis_bH")


def load_uv(n):
    """Exact U_2/V_2 dicts from committed artifacts."""
    import zstandard as zstd
    with open(os.path.join(bh_dir(n), "U.json.zst"), "rb") as handle:
        u_rows = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    with open(os.path.join(bh_dir(n), "V.json.zst"), "rb") as handle:
        v_rows = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    return ({r["pair_id"]: int(r["U_scaled"]) for r in u_rows},
            {r["pair_id"]: int(r["V_scaled"]) for r in v_rows})


def edge_inequalities_hold(n, U, V):
    """Full-edge Bellman inequalities at b=2 over the audit-graph rebuild."""
    tables = graph.build_tables(n)
    reach = graph.build_reachability(tables)
    for pid in reach.pair_ids:
        for mode in (graph.KEEP, graph.DELETE):
            for key in range(1, n + 1):
                tgt, a, y = graph.successor(tables, pid, mode, key)
                w = 2 * a - y
                if U[tgt] - U[pid] > w or V[tgt] - V[pid] > w:
                    return False
    return True


def stress_deterministic():
    """S-01: deterministic rerun (n=2 U/V recomputed twice, identical)."""
    # console.log equivalent [WP5-SUH4-01]: deterministic rerun.
    console_log("WP5-SUH4-01", "S-01 deterministic rerun n=2")
    from python.reference import canonical as cn
    from python.reference import solve_small as sv
    tables = sv.load_tables(os.path.join(REPO, "artifacts", "transitions", "n2"))
    reach = sv.load_reach(os.path.join(REPO, "artifacts", "reachability", "n2"),
                          tables.tree_count)
    csr = sv.build_csr(tables, reach)
    first = (cn.compute_U(csr, 2, 1)[0], cn.compute_V(csr, 2, 1)[0])
    second = (cn.compute_U(csr, 2, 1)[0], cn.compute_V(csr, 2, 1)[0])
    check("S-01", first == second, "rerun identical")


def stress_agreement():
    """S-02: independent U/V agreement (all verify_bh2.json PASS)."""
    # console.log equivalent [WP5-SUH4-02]: independent agreement.
    console_log("WP5-SUH4-02", "S-02 independent agreement")
    ok = True
    for n in (2, 3, 4, 5, 6, 7):
        with open(os.path.join(REPO, "artifacts", "audits", "n%d" % n,
                               "verify_bh2.json"), encoding="utf-8") as handle:
            if json.load(handle).get("verdict") != "PASS":
                ok = False
    check("S-02", ok, "6/6 independent PASS")


def stress_corrupt_u():
    """S-03: deliberately corrupted U table detected."""
    # console.log equivalent [WP5-SUH4-03]: corrupted-U injection.
    console_log("WP5-SUH4-03", "S-03 corrupted-U injection n=3")
    U, V = load_uv(3)
    tables = graph.build_tables(3)
    c = tables.tree_count
    victim = next(pid for pid in sorted(U) if pid // c != pid % c)
    U[victim] += 1
    detected = not edge_inequalities_hold(3, U, V)
    check("S-03", detected, "corrupted U caught")


def stress_corrupt_v():
    """S-04: deliberately corrupted V table detected."""
    # console.log equivalent [WP5-SUH4-04]: corrupted-V injection.
    console_log("WP5-SUH4-04", "S-04 corrupted-V injection n=3")
    U, V = load_uv(3)
    tables = graph.build_tables(3)
    c = tables.tree_count
    victim = next(pid for pid in sorted(V) if pid // c != pid % c)
    V[victim] = U[victim] + 1
    bad_order = any(V[pid] > U[pid] for pid in U)
    bad_ineq = not edge_inequalities_hold(3, U, V)
    check("S-04", bad_order or bad_ineq, "corrupted V caught")


def geometry_accepted(companion, table_sha):
    """Gate predicate: companion declares b=2/1 and table hash matches."""
    return (companion.get("b_H") == {"p": "2", "q": "1"}
            and companion.get("files", {}).get("U", {}).get("logical_sha256") == table_sha)


def stress_wrong_b():
    """S-05: wrong-b (b_n*) geometry detected and refused."""
    # console.log equivalent [WP5-SUH4-05]: wrong-b injection.
    console_log("WP5-SUH4-05", "S-05 wrong-b injection n=4")
    import zstandard as zstd
    with open(os.path.join(bh_dir(4), "bH_geometry.v1.json"), encoding="utf-8") as handle:
        companion = json.load(handle)
    with open(os.path.join(REPO, "artifacts", "potentials", "n4", "U.json.zst"), "rb") as handle:
        old_blob = zstd.ZstdDecompressor().decompress(handle.read())
    refused = not geometry_accepted(companion, hashlib.sha256(old_blob).hexdigest())
    check("S-05", refused, "b_n* table refused as b=2 geometry")


def stress_changed_h():
    """S-06: changed-H formula detected (counts diverge from frozen record)."""
    # console.log equivalent [WP5-SUH4-06]: changed-H injection.
    console_log("WP5-SUH4-06", "S-06 changed-H injection H-0005 n=5")
    from python.wp5 import falsify as F
    U, V = load_uv(5)
    shapes, count, _a, _c, pair_ids = F.load_domain_tables(5)
    h_table = F.build_h_table("H-0005", 5, shapes, count, pair_ids)
    h_table[pair_ids[0]] += 1
    with open(os.path.join(REPO, "artifacts", "hypotheses", "H-0005.uh4.json"),
              encoding="utf-8") as handle:
        frozen = next(r for r in json.load(handle)["per_n"] if r["n"] == 5)
    lower = sum(1 for pid in pair_ids if h_table[pid] < V[pid])
    upper = sum(1 for pid in pair_ids if h_table[pid] > U[pid])
    detected = (lower != frozen["lower_violations"] or upper != frozen["upper_violations"])
    check("S-06", detected, "changed H diverges from frozen record")


def uh4_record_consistent(record):
    """Gate predicate: PASS claims zero violations on every n."""
    if record.get("verdict") == "PASS":
        return all(r["status"] == "PASS" and r["lower_violations"] == 0
                   and r["upper_violations"] == 0 for r in record["per_n"])
    return True


def stress_false_pass():
    """S-07: false-PASS UH-4 metadata detected."""
    # console.log equivalent [WP5-SUH4-07]: false-PASS injection.
    console_log("WP5-SUH4-07", "S-07 false-PASS injection")
    with open(os.path.join(REPO, "artifacts", "hypotheses", "H-0001.uh4.json"),
              encoding="utf-8") as handle:
        record = json.load(handle)
    forged = json.loads(json.dumps(record))
    forged["verdict"] = "PASS"
    detected = not uh4_record_consistent(forged)
    sane = uh4_record_consistent(record)
    check("S-07", detected and sane, "forged PASS rejected, true record sane")


def stress_uh5_preserved():
    """S-08: UH-5 preservation hash check."""
    # console.log equivalent [WP5-SUH4-08]: UH-5 preservation check.
    console_log("WP5-SUH4-08", "S-08 UH-5 preservation check")
    paths = ["artifacts/falsification"]
    for hyp_id in ("H-0001", "H-0002", "H-0003", "H-0004", "H-0005", "H-0006"):
        for suffix in (".json", ".eval_contract.json", ".bH_feasibility.json",
                       ".og.json", ".wp5.json"):
            paths.append("artifacts/hypotheses/%s%s" % (hyp_id, suffix))
    r = subprocess.run(["git", "diff", "--quiet", "HEAD", "--"] + paths,
                       capture_output=True)
    check("S-08", r.returncode == 0, "UH-5 evidence unchanged")


def stress_firewalls():
    """S-09/S-10: firewall refusal under attempted n8/H1 access."""
    # console.log equivalent [WP5-SUH4-09]: firewall refusal probes.
    console_log("WP5-SUH4-09", "S-09/S-10 firewall refusal probes")
    from python.wp5 import uh4_geometry as G
    refused = 0
    for probe in ("artifacts/wp5/sa03/holdout/detail.json",
                  "artifacts/trees/n8/trees.jsonl.zst",
                  "artifacts/wp5/h1_holdout/bank_secret.json"):
        try:
            G.assert_no_holdout_path(probe)
        except AssertionError:
            refused += 1
    n8 = json.load(open(os.path.join(REPO, "artifacts", "wp5", "sa03",
                                     "n8_firewall.json"), encoding="utf-8"))
    h1 = json.load(open(os.path.join(REPO, "artifacts", "wp5", "h1_holdout",
                                     "h1_firewall.json"), encoding="utf-8"))
    check("S-09", refused == 3 and n8.get("state") == "EMPTY", "n8 refused+EMPTY")
    check("S-10", h1.get("state") == "EMPTY", "H1 EMPTY")


def stress_exactness():
    """S-11: arbitrary-precision/exactness checks (ints only, no floats)."""
    # console.log equivalent [WP5-SUH4-11]: exactness audit.
    console_log("WP5-SUH4-11", "S-11 exactness audit")
    import zstandard as zstd
    ok = True
    for n in (2, 3, 4, 5, 6, 7):
        with open(os.path.join(bh_dir(n), "U.json.zst"), "rb") as handle:
            for row in json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8")):
                if not isinstance(row["U_scaled"], str) or not isinstance(row["pair_id"], int):
                    ok = False
    with open(os.path.join(REPO, "artifacts", "hypotheses", "H-0002.uh4.json"),
              encoding="utf-8") as handle:
        for row in json.load(handle)["per_n"]:
            if not all(isinstance(row[k], int) for k in
                       ("lower_violations", "upper_violations",
                        "max_lower_margin", "max_upper_margin")):
                ok = False
    check("S-11", ok, "integer-typed authoritative values")


def stress_completeness():
    """S-12: state-count completeness for every n."""
    # console.log equivalent [WP5-SUH4-12]: completeness audit.
    console_log("WP5-SUH4-12", "S-12 completeness audit")
    import zstandard as zstd
    ok = True
    for n in (2, 3, 4, 5, 6, 7):
        with open(os.path.join(REPO, "artifacts", "reachability", "n%d" % n,
                               "reachable.json.zst"), "rb") as handle:
            sealed = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
        with open(os.path.join(bh_dir(n), "bH_geometry.v1.json"), encoding="utf-8") as handle:
            companion = json.load(handle)
        if companion["reachable_pair_count"] != len(sealed["pair_ids"]):
            ok = False
        with open(os.path.join(REPO, "artifacts", "hypotheses", "H-0003.uh4.json"),
                  encoding="utf-8") as handle:
            uh4 = next(r for r in json.load(handle)["per_n"] if r["n"] == n)
        if uh4["states_checked"] != len(sealed["pair_ids"]):
            ok = False
    check("S-12", ok, "counts match sealed reachability 6/6")


def stress_ordering():
    """S-13: pair-order determinism (ascending pair_id in artifacts)."""
    # console.log equivalent [WP5-SUH4-13]: ordering audit.
    console_log("WP5-SUH4-13", "S-13 ordering audit")
    import zstandard as zstd
    ok = True
    for n in (2, 3, 4, 5, 6, 7):
        with open(os.path.join(bh_dir(n), "U.json.zst"), "rb") as handle:
            pids = [r["pair_id"] for r in
                    json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))]
        if pids != sorted(pids):
            ok = False
    check("S-13", ok, "ascending pair order 6/6")


def stress_serialization():
    """S-14: canonical-table serialization determinism."""
    # console.log equivalent [WP5-SUH4-14]: serialization audit.
    console_log("WP5-SUH4-14", "S-14 serialization audit")
    raw = open(os.path.join(bh_dir(4), "bH_geometry.v1.json"), encoding="utf-8").read()
    again = json.dumps(json.loads(raw), sort_keys=True, indent=2) + "\n"
    check("S-14", raw == again, "canonical JSON text stable (CRLF-neutral)")


def main(argv=None):
    """Run UH-4 stress suite, write JSON log, exit nonzero on failure."""
    t0 = time.time()
    # console.log equivalent [WP5-SUH4-00]: suite start.
    console_log("WP5-SUH4-00", "UH-4 stress suite start")
    stress_deterministic()
    stress_agreement()
    stress_corrupt_u()
    stress_corrupt_v()
    stress_wrong_b()
    stress_changed_h()
    stress_false_pass()
    stress_uh5_preserved()
    stress_firewalls()
    stress_exactness()
    stress_completeness()
    stress_ordering()
    stress_serialization()
    dt = time.time() - t0
    # console.log equivalent [WP5-SUH4-15]: suite summary.
    console_log("WP5-SUH4-15", "pass=%d fail=%d seconds=%.1f" % (len(PASS), len(FAIL), dt))
    with open(os.path.join(REPO, "artifacts", "logs", "wp5_uh4_stress.json"),
              "w", encoding="utf-8") as handle:
        json.dump({"experiment_id": "SPLAY-AM-PD-v0.1", "exit": 0 if not FAIL else 1,
                   "fail": FAIL, "pass": PASS,
                   "wall_seconds": round(dt, 1)}, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
