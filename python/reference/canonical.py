"""Canonical U^Z / V^Z / G^Z tables with Bellman witnesses (reference side).

U^Z: shortest diagonal-rooted scaled slack (forward queue Bellman-Ford).
V^Z: -min over paths-from-s (empty path allowed), via reverse-graph
propagation from the all-zero initialization. G^Z = U^Z - V^Z must be >= 0
everywhere (else CANONICAL_POTENTIAL_FAIL). Forced <=> G == 0 exactly.
Bellman witnesses: tight predecessor per U state (diagonal-init exception),
tight outgoing edge per V>0 state. All witnesses re-verified by recompute.
"""

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from python.reference import solve_small as sv  # noqa: E402

KEEP, DELETE = 0, 1


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def compute_U(csr, p, q):
    """Exact U^Z via unbounded queue Bellman-Ford. Returns (U, tight_par)."""
    # console.log equivalent [WP3-UV-01]: U computation begin.
    console_log("WP3-UV-01", "U computation begin R=%d" % csr.size)
    verdict, wit, dist = sv.check_validity(csr, p, q)
    if verdict != "VALID":
        raise AssertionError("U requested at invalid b")
    if any(d is None or d < 0 for d in dist):
        raise AssertionError("U violates nonnegativity")
    tight = {}
    for s in range(csr.size):
        for re in range(csr.roff[s], csr.roff[s + 1]):
            t = csr.rsrc[re]
            e = csr.rfwd[re]
            if dist[t] + p * int(csr.am[e]) - q * int(csr.ym[e]) == dist[s]:
                tight[s] = (t, e)
                break
    # console.log equivalent [WP3-UV-02]: U sealed in memory.
    console_log("WP3-UV-02", "U done")
    return dist, tight


def compute_V(csr, p, q):
    """Exact V^Z via reverse propagation. Returns (V, argmax_out).

    Algorithm lives in solve_small.shortest_future (shared with the WP-2
    complete transient rule); this wrapper keeps the WP-3 step logging.
    """
    # console.log equivalent [WP3-UV-03]: V computation begin.
    console_log("WP3-UV-03", "V computation begin R=%d" % csr.size)
    values, argmax = sv.shortest_future(csr, p, q)
    # console.log equivalent [WP3-UV-04]: V sealed in memory.
    console_log("WP3-UV-04", "V done")
    return values, argmax


def _dump_zst(path, obj):
    import zstandard as zstd
    blob = (json.dumps(obj, sort_keys=True) + "\n").encode("utf-8")
    logical = hashlib.sha256(blob).hexdigest()
    with open(path, "wb") as f:
        f.write(zstd.ZstdCompressor(level=19).compress(blob))
    return logical


def build_potentials(n, tables, reach, p, q, outdir):
    """Compute U/V/G + witnesses, verify, write artifacts. Returns summary."""
    os.makedirs(outdir, exist_ok=True)
    csr = sv.build_csr(tables, reach)
    U, tight_u = compute_U(csr, p, q)
    V, argmax_v = compute_V(csr, p, q)
    c = reach.tree_count
    for i, pid in enumerate(csr.pids):
        if V[i] < 0:
            raise AssertionError("V negative")
        a_id, b_id = divmod(pid, c)
        if a_id == b_id and (U[i] != 0 or V[i] != 0):
            raise AssertionError("diagonal canonical value nonzero")
        if V[i] > U[i]:
            raise AssertionError("CANONICAL_POTENTIAL_FAIL: V>U")
    for i in range(csr.size):
        for e in range(csr.off[i], csr.off[i + 1]):
            j = csr.tgt[e]
            w = p * int(csr.am[e]) - q * int(csr.ym[e])
            if U[j] - U[i] > w or V[j] - V[i] > w:
                raise AssertionError("canonical edge inequality violated")
    forced = []
    for i, pid in enumerate(csr.pids):
        g = U[i] - V[i]
        if g == 0:
            forced.append(pid)
    u_rows = [{"U_scaled": str(U[i]), "pair_id": csr.pids[i]} for i in range(csr.size)]
    v_rows = [{"V_scaled": str(V[i]), "pair_id": csr.pids[i]} for i in range(csr.size)]
    g_rows = [{"G_scaled": str(U[i] - V[i]), "forced": (U[i] == V[i]),
               "pair_id": csr.pids[i]} for i in range(csr.size)]
    h_u = _dump_zst(os.path.join(outdir, "U.json.zst"), u_rows)
    h_v = _dump_zst(os.path.join(outdir, "V.json.zst"), v_rows)
    h_g = _dump_zst(os.path.join(outdir, "G.json.zst"), g_rows)
    with open(os.path.join(outdir, "forced_states.json"), "w", encoding="utf-8") as f:
        json.dump({"count": len(forced), "forced_pair_ids": forced}, f, sort_keys=True)
        f.write("\n")
    wit_u = {}
    for i, pid in enumerate(csr.pids):
        a_id, b_id = divmod(pid, c)
        if a_id == b_id and U[i] == 0:
            wit_u[str(pid)] = {"kind": "diagonal-init"}
        elif i in tight_u:
            t, e = tight_u[i]
            wit_u[str(pid)] = {"kind": "tight-predecessor",
                               "mode": int(csr.mom[e]), "key": int(csr.keym[e]),
                               "predecessor": csr.pids[t]}
        else:
            raise AssertionError("missing U Bellman witness")
    wit_v = {}
    for i, pid in enumerate(csr.pids):
        if V[i] > 0:
            if argmax_v[i] is None:
                raise AssertionError("missing V Bellman witness")
            t, e = argmax_v[i]
            if p * int(csr.am[e]) - q * int(csr.ym[e]) + (-V[t]) != -V[i]:
                raise AssertionError("V witness not tight")
            wit_v[str(pid)] = {"key": int(csr.keym[e]),
                               "mode": int(csr.mom[e]), "successor": csr.pids[t]}
    summary = {"G_nonnegative": True, "b": {"p": str(p), "q": str(q)},
               "forced_count": len(forced), "forced_fraction": len(forced) / csr.size,
               "logical_G_sha256": h_g, "logical_U_sha256": h_u, "logical_V_sha256": h_v,
               "max_G": str(max(U[i] - V[i] for i in range(csr.size))),
               "max_U": str(max(U)), "max_V": str(max(V)), "n": n,
               "reachable_pair_count": csr.size}
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, sort_keys=True, indent=2)
        f.write("\n")
    with open(os.path.join(outdir, "bellman_witnesses.json"), "w", encoding="utf-8") as f:
        json.dump({"U": wit_u, "V": wit_v}, f, sort_keys=True)
        f.write("\n")
    # console.log equivalent [WP3-UV-05]: potentials written.
    console_log("WP3-UV-05", "n=%d forced=%d maxU=%s maxV=%s" % (n, len(forced), max(U), max(V)))
    return summary
