"""POST-n7 candidate generation + exact global derivative tests (WP-4 completion).

All candidates here are POST-n7-DEVELOPMENT (n7_status =
PREVIOUSLY_REVEALED_AFTER_H-SA02-B-v1-final_FREEZE). No untouched claims.
H-SA02-B-v1 / H-SA02-B-v1-final are never modified.

Steps:
  R1: single-atom rescue test: [F-v0.1 | {g}] on n456 for each of 14 atoms.
  R2: bounded local search around the dense particular for best n6 max-residual
      (deterministic coordinate steps; labeled bounded, not globally optimal).
  R3: freeze H-SA02-C-1 (canonical 5-support) and H-SA02-C-2 (best local) with
      POST-n7 ledger entries.
  R4: exact global derivative tests n=2..7 stratified by n / FPATH-FCYCLE-FGAP /
      KEEP-DELETE / zig / cost regime / SCC.

Outputs:
  artifacts/hypotheses/single_atom_rescue.json
  artifacts/hypotheses/H-SA02-C-1.json, H-SA02-C-2.json (+ ledger entries)
  artifacts/hypotheses/candidate_global_tests.json
"""
import json
import os
import sys
from fractions import Fraction

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from python.mining import holdout_firewall as firewall
from python.mining.exact_linear import FEATURE_ORDER, b_for_n
from python.mining.nonlinear_atoms import ATOM_NAMES
from python.mining.affine_exhaustion import sp_matrix, sp_vector, residual_vector


def console_log(step_id, msg):
    print("[%s] %s" % (step_id, msg), flush=True)


def load_all_forced():
    """All forced-derivative rows n=2..7 with F-deltas, atom deltas, targets."""
    import zstandard as zstd
    rows = []
    for n in (2, 3, 4, 5, 6, 7):
        firewall.guard_initial_fit_load("artifacts/features/n%d/edge_deltas.json.zst" % n)
        firewall.guard_load("artifacts/features/n%d/edge_deltas.json.zst" % n)
        with open(os.path.join(REPO, "artifacts", "features", "n%d" % n,
                               "edge_deltas.json.zst"), "rb") as f:
            deltas = json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))
        with open(os.path.join(REPO, "artifacts", "features", "n%d" % n,
                               "edge_atom_deltas.json.zst"), "rb") as f:
            ad = {(r["source_state_id"], r["mode"], r["key"]): r["delta_G"]
                  for r in json.loads(zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))}
        with open(os.path.join(REPO, "artifacts", "features", "n%d" % n,
                               "feature_table.json.zst"), "rb") as f:
            ftab = {r["pair_id"]: r for r in json.loads(
                zstd.ZstdDecompressor().decompress(f.read()).decode("utf-8"))}
        from python.mining.nonlinear_atoms import atom_state_values
        p, q = b_for_n(n)
        for r in deltas:
            key = (r["source_state_id"], r["mode"], r["key"])
            g = ad.get(key)
            if g is None:
                # Non-FCYCLE forced rows (only 2, both n=3): pure on-the-fly
                # evaluation of the frozen atom functions on stored state-only
                # vectors. No persisted artifact change.
                a = atom_state_values(ftab[r["source_state_id"]]["scalar"],
                                      ftab[r["source_state_id"]]["vectors"])
                b_ = atom_state_values(ftab[r["target_state_id"]]["scalar"],
                                       ftab[r["target_state_id"]]["vectors"])
                g = {k: b_[k] - a[k] for k in ATOM_NAMES}
            rows.append({
                "n": n, "source_state_id": r["source_state_id"],
                "target_state_id": r["target_state_id"], "mode": r["mode"], "key": r["key"],
                "provenance": sorted(r["provenance"]),
                "a": r["a"], "y": r["y"],
                "target": Fraction(int(r["scaled_slack"]), q),
                "vecF": [int(r["delta_F"][k]) for k in FEATURE_ORDER],
                "vecG": [int(g[k]) for k in ATOM_NAMES],
            })
    rows.sort(key=lambda r: (r["n"], r["source_state_id"], r["mode"], r["key"]))
    return rows


def scc_index():
    """Map (n, state) -> scc_id for states on canonical cycles (else None)."""
    idx = {}
    for n in (4, 5, 6, 7):
        recs = json.load(open(os.path.join(
            REPO, "artifacts", "cycle_anatomy", "n%d" % n, "cycle_anatomy.json"), encoding="utf-8"))
        for r in recs:
            idx.setdefault((n, r["source_state_id"]), r["scc_id"])
    return idx


def zig_of(n, source_state_id, mode, key, shapes_cache):
    from python.reference import tree as ref_tree
    from python.reference import splay as ref_splay
    from python.reference import enumerate as ref_enum
    if n not in shapes_cache:
        shapes_cache[n] = ref_enum.canonical_shapes(n)
    from python.reference import pair_graph as ref_pg
    tables = ref_pg.build_tables(n)
    tc = len(shapes_cache[n])
    a_id = source_state_id // tc
    t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shapes_cache[n][a_id]))
    _t2, _c, cases, _p = ref_splay.splay(t, key)
    s = list(cases)
    if s == ["ZIG"]:
        return "ZIG"
    if s in (["LL"], ["RR"]):
        return "LL/RR"
    if any(x in ("LR", "RL") for x in s):
        return "LR/RL"
    return "MULTI:" + ",".join(s)


def main():
    firewall.hydrate_from_files()
    rows = load_all_forced()
    fcycle456 = [r for r in rows if r["n"] in (4, 5, 6) and "FCYCLE" in r["provenance"]]
    console_log("CAND", "forced rows total=%d, FCYCLE n456=%d" % (len(rows), len(fcycle456)))
    # ---- R1: single-atom rescue ----
    Mf = [r["vecF"] for r in fcycle456]
    t456 = [r["target"] for r in fcycle456]
    rescue = {}
    for j, name in enumerate(ATOM_NAMES):
        M = [vf + [vg[j]] for vf, vg in zip(Mf, [r["vecG"] for r in fcycle456])]
        m = sp_matrix(M)
        b = sp_vector(t456)
        ok = m.rank() == m.row_join(b).rank()
        rescue[name] = ok
    console_log("RESCUE", "single-atom rescues: %s" %
                ([k for k, v in rescue.items() if v] or "NONE"))
    # ---- R2: bounded local search around dense particular ----
    aff = json.load(open(os.path.join(REPO, "artifacts", "hypotheses",
                                      "track_b_affine_space.json"), encoding="utf-8"))
    part = [Fraction(aff["selection"]["particular_solution"][k]) for k in FEATURE_ORDER]
    nulls = [[Fraction(v) for v in nv] for nv in aff["selection"]["nullspace_basis_primitive_int"]]
    dev6 = [(r["vecF"], r["target"]) for r in fcycle456 if r["n"] == 6]

    def maxres(alpha):
        worst = Fraction(0)
        for vf, tg in dev6:
            r = abs(sum(a * x for a, x in zip(alpha, vf)) - tg)
            if r > worst:
                worst = r
        return worst

    best, best_alpha = maxres(part), list(part)
    for nv in nulls:
        for step in (-2, -1, 1, 2):
            cand = [p + step * v for p, v in zip(part, nv)]
            r = maxres(cand)
            if r < best:
                best, best_alpha = r, cand
    console_log("LOCALSEARCH", "bounded single-null-step best n6 max-residual=%s (v1 was 5)" % best)
    # ---- R3: freeze C candidates ----
    hyps = []
    canon5 = aff["sparse_per_domain"]["SIGNED"]["example"]
    c1 = [Fraction(canon5.get(k, "0")) for k in FEATURE_ORDER]
    defs = {
        "H-SA02-C-1": ("canonical 5-support exact n45 solution "
                       "(lexicographically first min-support member over Q)",
                       {k: "%s/%s" % (Fraction(canon5.get(k, "0")).numerator,
                                      Fraction(canon5.get(k, "0")).denominator)
                        for k in FEATURE_ORDER if Fraction(canon5.get(k, "0")) != 0}, c1),
        "H-SA02-C-2": ("bounded-local-search n6-residual minimizer around dense particular "
                       "(single-null-step neighborhood, deterministic; NOT globally optimal)",
                       {k: "%s/%s" % (v.numerator, v.denominator)
                        for k, v in zip(FEATURE_ORDER, best_alpha) if v != 0}, best_alpha),
    }
    ledger = json.load(open(os.path.join(REPO, "artifacts", "hypotheses",
                                         "hypothesis_ledger.json"), encoding="utf-8"))
    import hashlib
    for hid, (desc, coeffs, alpha) in defs.items():
        doc = {"hypothesis_id": hid, "parent_hypothesis": "H-SA02-B-v1-final (superseded line)",
               "definition": desc, "coefficients": coeffs,
               "coefficient_domain": "exact rationals (F-v0.1 linear)",
               "n7_status": firewall.require_post_n7_label(hid),
               "label": "POST-n7-DEVELOPMENT (n7 is falsification data, never untouched holdout)",
               "state_only": True, "uses_history": False, "uses_b_n_star_table": False,
               "discovery_sizes": [4, 5], "development_sizes": [6, 7]}
        blob = (json.dumps(doc, sort_keys=True) + "\n").encode("utf-8")
        doc["sha256"] = hashlib.sha256(blob).hexdigest()
        with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.json" % hid),
                  "w", encoding="utf-8") as f:
            json.dump(doc, f, sort_keys=True, indent=2)
            f.write("\n")
        ledger["hypotheses"] = [h for h in ledger["hypotheses"] if h["hypothesis_id"] != hid]
        ledger["hypotheses"].append({"hypothesis_id": hid, "sha256": doc["sha256"],
                                     "status": "POST-n7-DEVELOPMENT", "definition": desc})
        hyps.append((hid, alpha))
        console_log("FREEZE", "%s sha=%s" % (hid, doc["sha256"][:16]))
    with open(os.path.join(REPO, "artifacts", "hypotheses", "hypothesis_ledger.json"),
              "w", encoding="utf-8") as f:
        json.dump(ledger, f, sort_keys=True, indent=2)
        f.write("\n")
    # ---- R4: global stratified tests ----
    scc = scc_index()
    shapes_cache = {}
    prov_class = lambda p: "FCYCLE" if "FCYCLE" in p else ("FPATH" if "FPATH" in p else
                                                          ("FGAP" if "FGAP" in p else "OTHER"))
    gout = {"n7_status": firewall.N7_STATUS,
            "label": "POST-n7-DEVELOPMENT global tests (all sizes incl. revealed n7 are development data)"}
    for hid, alpha in hyps:
        per_row = []
        for r in rows:
            pred = sum(a * x for a, x in zip(alpha, r["vecF"]))
            res = abs(pred - r["target"])
            per_row.append((r, res))
        sat = sum(1 for _, res in per_row if res == 0)
        worst = max(res for _, res in per_row)
        # Stratify.
        strata = {}
        for r, res in per_row:
            keys = [("n=%d" % r["n"]), ("prov=%s" % prov_class(r["provenance"])),
                    ("mode=%s" % r["mode"]),
                    ("zig=%s" % zig_of(r["n"], r["source_state_id"], r["mode"], r["key"], shapes_cache)),
                    ("cost=%d,%d" % (r["a"], r["y"])),
                    ("scc=%s" % scc.get((r["n"], r["source_state_id"]), "non-canonical"))]
            for k in keys:
                d = strata.setdefault(k, {"n": 0, "sat": 0, "worst": Fraction(0), "worst_row": None})
                d["n"] += 1
                if res == 0:
                    d["sat"] += 1
                if res > d["worst"]:
                    d["worst"] = res
                    d["worst_row"] = "src=%d %s k=%d L=%s/%s" % (
                        r["source_state_id"], r["mode"], r["key"],
                        r["target"].numerator, r["target"].denominator)
        first_ce = next(((r, res) for r, res in per_row if res != 0), (None, None))
        resdist = {}
        for _, res in per_row:
            k = "%s/%s" % (res.numerator, res.denominator)
            resdist[k] = resdist.get(k, 0) + 1
        gout[hid] = {
            "satisfaction_count": "%d/%d" % (sat, len(per_row)),
            "exact_max_residual": "%s/%s" % (worst.numerator, worst.denominator),
            "first_counterexample": ("%s res=%s/%s" % (
                first_ce[0] and ("n=%d src=%d %s k=%d" % (
                    first_ce[0]["n"], first_ce[0]["source_state_id"],
                    first_ce[0]["mode"], first_ce[0]["key"])), first_ce[1].numerator,
                first_ce[1].denominator) if first_ce[0] else None),
            "residual_distribution": resdist,
            "strata": {k: {"n": v["n"], "sat": v["sat"],
                           "worst": "%s/%s" % (v["worst"].numerator, v["worst"].denominator),
                           "worst_row": v["worst_row"]} for k, v in sorted(strata.items())},
            "verdict": "PASS" if worst == 0 else "FAIL (preserved, killed)",
        }
        console_log("GLOBAL", "%s sat=%d/%d max=%s/%s" % (
            hid, sat, len(per_row), worst.numerator, worst.denominator))
    gout["single_atom_rescue"] = {
        "rescued_by": [k for k, v in rescue.items() if v],
        "verdict": "no single authorized atom restores n456 consistency" if not any(rescue.values())
                   else "RESCUED (unexpected)",
    }
    with open(os.path.join(REPO, "artifacts", "hypotheses", "candidate_global_tests.json"),
              "w", encoding="utf-8") as f:
        json.dump(gout, f, sort_keys=True, indent=2)
        f.write("\n")
    console_log("GLOBAL-99", "done")


if __name__ == "__main__":
    main()
