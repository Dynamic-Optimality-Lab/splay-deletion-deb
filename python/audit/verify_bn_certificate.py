"""Independent b_n* certificate verifier (imports python/audit only).

Re-derives tables + R_n + every edge from the frozen semantics, then checks:
gcd(p,q)=1 with p,q>0; 1<=p/q<=n by cross multiplication; the entire upper
potential (length, nonnegativity, diagonal zeros, every reachable edge);
each lower witness (legality, nonempty, diagonal rooting, exact sums, zero
slack); criticality consistency. Exit 0 iff all checks pass. Step-logged.
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.audit import graph  # noqa: E402

KEEP, DELETE = graph.KEEP, graph.DELETE


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def mode_of(name):
    """Mode string to frozen mode code."""
    return KEEP if name == "KEEP" else DELETE


def main(argv=None):
    """Verify a sealed b_n* certificate independently."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--cert-dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    # console.log equivalent [WP2-AUD-B-01]: independent re-derivation begin.
    console_log("WP2-AUD-B-01", "re-deriving certificate inputs n=%d" % args.n)
    checks = {}
    tables = graph.build_tables(args.n)
    reach = graph.build_reachability(tables)
    with open(os.path.join(args.cert_dir, "bn_certificate.json"), encoding="utf-8") as f:
        cert = json.load(f)
    p, q = int(cert["b"]["p"]), int(cert["b"]["q"])
    checks["reduced"] = p > 0 and q > 0 and math.gcd(p, q) == 1
    checks["bracket"] = q <= p <= args.n * q
    checks["count"] = cert["reachable_pair_count"] == len(reach.pair_ids)
    import zstandard as zstd
    with open(os.path.join(args.cert_dir, cert["upper_certificate"]["file"]), "rb") as f:
        rows = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    pot = {r["pair_id"]: int(r["P"]) for r in rows}
    ok = len(pot) == len(reach.pair_ids)
    c = tables.tree_count
    for pid in reach.pair_ids:
        if pot.get(pid, -1) < 0:
            ok = False
        a_id, b_id = divmod(pid, c)
        if a_id == b_id and pot.get(pid) != 0:
            ok = False
    # console.log equivalent [WP2-AUD-B-02]: upper potential full-edge sweep.
    console_log("WP2-AUD-B-02", "upper sweep over %d states" % len(reach.pair_ids))
    for pid in reach.pair_ids:
        for mode in (KEEP, DELETE):
            for key in range(1, args.n + 1):
                tgt, a, y = graph.successor(tables, pid, mode, key)
                if pot[tgt] - pot[pid] > p * a - q * y:
                    ok = False
    checks["upper"] = ok

    def sums(edges):
        sa = sy = 0
        for (s, mode, key, t) in edges:
            tgt, a, y = graph.successor(tables, s, mode, key)
            if tgt != t:
                return None
            sa += a
            sy += y
        return sa, sy

    seen = set()
    wit_ok = True
    for low in cert["lower_certificates"]:
        if low["type"] == "zero_slack_path":
            with open(os.path.join(args.cert_dir, low["file"]), encoding="utf-8") as f:
                w = json.load(f)
            edges = [(e["source"], mode_of(e["mode"]), e["key"], e["target"]) for e in w["edges"]]
            r = sums(edges)
            a0, b0 = divmod(edges[0][0], c) if edges else (0, 1)
            if not edges or a0 != b0 or r is None or r[0] != w["sum_a"] or r[1] != w["sum_y"]:
                wit_ok = False
            elif r[0] <= 0 or p * r[0] - q * r[1] != 0:
                wit_ok = False
            else:
                seen.add("transient")
        elif low["type"] == "zero_slack_cycle":
            with open(os.path.join(args.cert_dir, low["file"]), encoding="utf-8") as f:
                w = json.load(f)
            cyc = [(e["source"], mode_of(e["mode"]), e["key"], e["target"]) for e in w["cycle"]]
            pre = [(e["source"], mode_of(e["mode"]), e["key"], e["target"]) for e in w["prefix"]]
            r = sums(cyc)
            rp = sums(pre) if pre else (0, 0)
            if not cyc or cyc[0][0] != cyc[-1][3] or r is None or rp is None:
                wit_ok = False
            elif r[0] != w["sum_a_cycle"] or r[1] != w["sum_y_cycle"]:
                wit_ok = False
            elif r[0] <= 0 or p * r[0] - q * r[1] != 0:
                wit_ok = False
            else:
                if pre:
                    a0, b0 = divmod(pre[0][0], c)
                    if a0 != b0 or pre[-1][3] != cyc[0][0]:
                        wit_ok = False
                    else:
                        seen.add("cyclic")
                else:
                    a0, b0 = divmod(cyc[0][0], c)
                    if a0 != b0:
                        wit_ok = False
                    else:
                        seen.add("cyclic")
        else:
            wit_ok = False
    checks["lower"] = wit_ok and bool(seen)
    want = ("EXACT_BN_MIXED" if seen == {"transient", "cyclic"}
            else "EXACT_BN_TRANSIENT" if seen == {"transient"}
            else "EXACT_BN_CYCLIC" if seen == {"cyclic"} else "NONE")
    checks["criticality"] = cert["criticality"] == want
    verdict = "PASS" if all(checks.values()) else "FAIL"
    # console.log equivalent [WP2-AUD-B-03]: verdict.
    console_log("WP2-AUD-B-03", "certificate n=%d %s" % (args.n, verdict))
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify_bn_certificate.json"), "w", encoding="utf-8") as f:
        json.dump({"checks": checks, "n": args.n, "p": str(p), "q": str(q),
                   "verdict": verdict}, f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
