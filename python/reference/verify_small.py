"""Reference-side re-verification of a sealed b_n* certificate.

Reloads tables, reachability, and certificate artifacts; recomputes every
edge from the tables; rechecks the upper potential on all edges and both
lower-witness families. Returns a verdict dict (no printing except via the
caller). The fully independent check lives in python/audit/.
"""

import hashlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.reference import pair_graph as pg  # noqa: E402
from python.reference import solve_small as sv  # noqa: E402

KEEP, DELETE = pg.KEEP, pg.DELETE


def load_json(path):
    """Load a JSON artifact."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_potential(path):
    """Load integer potential table {pair_id: P} from .json.zst."""
    import zstandard as zstd
    with open(path, "rb") as f:
        rows = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
    return {r["pair_id"]: int(r["P"]) for r in rows}


def mode_of(name):
    """Mode string to frozen mode code."""
    return KEEP if name == "KEEP" else DELETE


def verify(n, tables_dir, reach_dir, cert_dir):
    """Re-verify a sealed certificate. Returns (verdict, details)."""
    details = []
    tables = sv.load_tables(tables_dir)
    reach = sv.load_reach(reach_dir, tables.tree_count)
    cert = load_json(os.path.join(cert_dir, "bn_certificate.json"))
    p, q = int(cert["b"]["p"]), int(cert["b"]["q"])
    if math.gcd(p, q) != 1 or p <= 0 or q <= 0:
        return "FAIL", ["p/q not reduced positive"]
    details.append("reduced ok")
    if not (q <= p <= n * q):
        return "FAIL", ["bracket violated"]
    details.append("bracket ok")
    if cert["reachable_pair_count"] != len(reach.pair_ids):
        return "FAIL", ["reachable count mismatch"]
    pot = load_potential(os.path.join(cert_dir, cert["upper_certificate"]["file"]))
    if len(pot) != len(reach.pair_ids):
        return "FAIL", ["potential table incomplete"]
    for pid in reach.pair_ids:
        if pot[pid] < 0:
            return "FAIL", ["negative potential"]
        a_id, b_id = divmod(pid, reach.tree_count)
        if a_id == b_id and pot[pid] != 0:
            return "FAIL", ["diagonal potential nonzero"]
    details.append("potential nonneg+diagonal ok")
    csr = sv.build_csr(tables, reach)
    for i in range(csr.size):
        for e in range(csr.off[i], csr.off[i + 1]):
            j = csr.tgt[e]
            w = p * int(csr.am[e]) - q * int(csr.ym[e])
            if pot[csr.pids[j]] - pot[csr.pids[i]] > w:
                return "FAIL", ["upper edge violation"]
    details.append("upper all-edges ok")
    seen = set()
    for low in cert["lower_certificates"]:
        if low["type"] == "zero_slack_path":
            w = load_json(os.path.join(cert_dir, low["file"]))
            edges = [(e["source"], mode_of(e["mode"]), e["key"], e["target"]) for e in w["edges"]]
            if not edges:
                return "FAIL", ["empty transient witness"]
            a0, b0 = divmod(edges[0][0], reach.tree_count)
            if a0 != b0:
                return "FAIL", ["transient witness not diagonal-rooted"]
            sa, sy = sv.edge_sums(csr, edges)
            if sa != w["sum_a"] or sy != w["sum_y"] or sa <= 0 or p * sa - q * sy != 0:
                return "FAIL", ["transient witness sums wrong"]
            seen.add("transient")
        elif low["type"] == "zero_slack_cycle":
            w = load_json(os.path.join(cert_dir, low["file"]))
            cyc = [(e["source"], mode_of(e["mode"]), e["key"], e["target"]) for e in w["cycle"]]
            pre = [(e["source"], mode_of(e["mode"]), e["key"], e["target"]) for e in w["prefix"]]
            if not cyc or cyc[0][0] != cyc[-1][3]:
                return "FAIL", ["cycle not closed"]
            if pre:
                a0, b0 = divmod(pre[0][0], reach.tree_count)
                if a0 != b0 or pre[-1][3] != cyc[0][0]:
                    return "FAIL", ["cycle prefix invalid"]
            else:
                a0, b0 = divmod(cyc[0][0], reach.tree_count)
                if a0 != b0:
                    return "FAIL", ["cycle unreachable (no prefix, not diagonal)"]
            sa, sy = sv.edge_sums(csr, cyc)
            if sa != w["sum_a_cycle"] or sy != w["sum_y_cycle"] or sa <= 0:
                return "FAIL", ["cycle sums wrong"]
            if p * sa - q * sy != 0:
                return "FAIL", ["cycle slack nonzero"]
            seen.add("cyclic")
    if not seen:
        return "FAIL", ["no lower witness"]
    details.append("lower witnesses ok: %s" % sorted(seen))
    want = ("EXACT_BN_MIXED" if seen == {"transient", "cyclic"}
            else "EXACT_BN_TRANSIENT" if seen == {"transient"} else "EXACT_BN_CYCLIC")
    if cert["criticality"] != want:
        return "FAIL", ["criticality mismatch"]
    details.append("criticality ok")
    digest = hashlib.sha256(json.dumps(cert, sort_keys=True).encode()).hexdigest()
    details.append("cert_sha=%s" % digest[:16])
    return "PASS", details
