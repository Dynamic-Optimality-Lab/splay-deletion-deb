"""WP-5 stage 13: UH-4 sandwich tables (survivors only) + independent H05 verification.

Shared U_{b_H},V_{b_H} tables are computed ONCE (all survivors share b_H=2)
into artifacts/potentials/n{n}/hypothesis_bH/ and independently re-verified
via the audit-side verifier before any UH-4 verdict is recorded. Independent
H05 sweeps + transition re-derivation + exact agreement run for every frozen
candidate regardless of development outcome.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-VRF-01]: verification stage started.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


def dev_passed(hypothesis_id):
    from python.wp5.run_phase import read_uh
    gates = read_uh(hypothesis_id)
    return all(gates[k] == "PASS" for k in ("UH-0", "UH-1", "UH-2", "UH-3", "UH-5"))


def build_bh_tables(p_h, q_h, sizes, out_root=None):
    """Shared canonical U_{b_H},V_{b_H} tables + independent re-verification.

    Production writes under artifacts/potentials/n{n}/hypothesis_bH/; tests
    pass a temp out_root (inputs still read from sealed production paths).
    """
    # console.log equivalent [WP5-VRF-02]: b_H canonical tables computed.
    console_log("WP5-VRF-02", "building U/V at b=%d/%d" % (p_h, q_h))
    sys.path.insert(0, REPO)
    from python.reference import pair_graph as PG
    from python.reference import solve_small as SS
    from python.reference import canonical as CN
    import zstandard as zstd
    for n in sizes:
        outdir = os.path.join(REPO, "artifacts", "potentials", "n%d" % n, "hypothesis_bH") \
            if out_root is None else os.path.join(out_root, "n%d" % n)
        os.makedirs(outdir, exist_ok=True)
        tables = PG.build_tables(n)
        reach = PG.build_reachability(tables)
        csr = SS.build_csr(tables, reach)
        dist_u, _tight = CN.compute_U(csr, p_h, q_h)
        dist_v, _arg = CN.compute_V(csr, p_h, q_h)
        for name, dist in (("U_bH", dist_u), ("V_bH", dist_v)):
            rows = [{"pair_id": pid, "%s_scaled" % name.split("_")[0]: str(val)}
                    for pid, val in zip(csr.pids, dist)]
            blob = (json.dumps(rows, sort_keys=True) + "\n").encode("utf-8")
            with open(os.path.join(outdir, "%s.json.zst" % name), "wb") as handle:
                handle.write(zstd.ZstdCompressor(level=19).compress(blob))
        # console.log equivalent [WP5-VRF-03]: tables independently re-verified.
        console_log("WP5-VRF-03", "re-verifying n=%d" % n)
        _reverify_bh_tables(n, outdir, csr.pids, p_h, q_h)
        from python.audit import verify_bh_tables as VBH
        code = VBH.main(["--n", str(n), "--pot-dir", outdir,
                         "--p", str(p_h), "--q", str(q_h),
                         "--out", os.path.join(outdir, "audit")])
        assert code == 0, "audit b_H verification failed at n=%d" % n
    # console.log equivalent [WP5-VRF-04]: b_H tables sealed + verified.
    console_log("WP5-VRF-04", "b_H tables sealed + verified")


def _reverify_bh_tables(n, pot_dir, pids, p_h, q_h):
    """Reference-side recheck: lengths, diagonal zeros, edge inequalities, V<=U."""
    import zstandard as zstd
    sys.path.insert(0, REPO)
    from python.reference import pair_graph as PG
    tables = PG.build_tables(n)
    reach = PG.build_reachability(tables)
    with open(os.path.join(pot_dir, "U_bH.json.zst"), "rb") as handle:
        rows_u = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    with open(os.path.join(pot_dir, "V_bH.json.zst"), "rb") as handle:
        rows_v = json.loads(zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))
    table_u = {int(r["pair_id"]): int(r["U_scaled"]) for r in rows_u}
    table_v = {int(r["pair_id"]): int(r["V_scaled"]) for r in rows_v}
    assert set(table_u) == set(pids) and set(table_v) == set(pids)
    from python.reference import enumerate as E
    count = len(E.canonical_shapes(n))
    for pid in pids:
        a_id = pid // count
        b_id = pid % count
        if a_id == b_id:
            assert table_u[pid] == 0 and table_v[pid] == 0
        assert table_v[pid] <= table_u[pid]
        for key in range(1, n + 1):
            for mode in (0, 1):
                tgt, a_cost, y_cost = PG.pair_successor(tables, pid, mode, key)
                slack = p_h * a_cost - q_h * y_cost
                assert table_u[tgt] - table_u[pid] <= slack
                assert table_v[tgt] - table_v[pid] <= slack


def uh4_check(hypothesis_id, sizes):
    """V_{b_H} <= H <= U_{b_H} over R_n (decisive)."""
    # console.log equivalent [WP5-VRF-05]: UH-4 sandwich checked.
    console_log("WP5-VRF-05", "UH-4 %s" % hypothesis_id)
    sys.path.insert(0, REPO)
    from python.wp5 import falsify as F
    from python.wp5 import structural as S
    formula_fn, _cls, _text = S.H_REGISTRY[hypothesis_id]
    bad = []
    for n in sizes:
        shapes, count, _after, _cost, pair_ids = F.load_domain_tables(n)
        import zstandard as zstd
        pot_dir = os.path.join(REPO, "artifacts", "potentials", "n%d" % n, "hypothesis_bH")
        with open(os.path.join(pot_dir, "U_bH.json.zst"), "rb") as handle:
            table_u = {int(r["pair_id"]): int(r["U_scaled"]) for r in json.loads(
                zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))}
        with open(os.path.join(pot_dir, "V_bH.json.zst"), "rb") as handle:
            table_v = {int(r["pair_id"]): int(r["V_scaled"]) for r in json.loads(
                zstd.ZstdDecompressor().decompress(handle.read()).decode("utf-8"))}
        sys.path.insert(0, REPO)
        from python.reference import tree as T
        infos = [S.tree_info(T.assign_inorder_keys(T.parse_shape(s))) for s in shapes]
        for pid in pair_ids:
            h_state = formula_fn(infos[pid // count], infos[pid % count], n)
            if not (table_v[pid] <= h_state <= table_u[pid]):
                bad.append([n, pid])
                break
        if bad:
            break
    return bad


def independent_verify(hypothesis_id, sizes):
    """H05: transition re-derivation + independent sweeps + exact agreement."""
    # console.log equivalent [WP5-VRF-06]: independent verification executed.
    console_log("WP5-VRF-06", "independent verify %s" % hypothesis_id)
    sys.path.insert(0, REPO)
    from python.wp5_independent import independent as IND
    from python.wp5 import structural as S
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.eval_contract.json" % hypothesis_id),
              encoding="utf-8") as handle:
        contract = json.load(handle)
    p_h = int(contract["b_hypothesis"]["p"])
    q_h = int(contract["b_hypothesis"]["q"])
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.json" % hypothesis_id),
              encoding="utf-8") as handle:
        formula_id = json.load(handle)["formula_id"]
    out = {"hypothesis_id": hypothesis_id, "sizes": {}}
    agree = True
    for n in sizes:
        keyed, _after, _cost, _pairs = IND.load_sealed_universe(n, REPO)
        trans = IND.verify_transitions(keyed, _after, _cost, n)
        rep = IND.sweep_candidate(formula_id, n, REPO, p_h, q_h, keyed=keyed)
        with open(os.path.join(REPO, "artifacts", "falsification", hypothesis_id,
                               "n%d.json" % n), encoding="utf-8") as handle:
            primary = json.load(handle)
        match = all(rep[k] == primary[k] for k in (
            "keep_max", "keep_argmax", "delete_max", "delete_argmax",
            "keep_pos_count", "delete_pos_count",
            "uh1_count", "uh2_count"))
        match = match and len(rep["keep_cex"]) == len(primary["keep_cex"]) \
            and len(rep["delete_cex"]) == len(primary["delete_cex"])
        for side in ("keep_cex", "delete_cex"):
            if rep[side] and primary[side]:
                match = match and rep[side][0][:3] == primary[side][0][:3]
        out["sizes"][str(n)] = {"transitions": trans, "agreement": match, "report": rep}
        agree = agree and match and trans["mismatches"] == 0
    out["agreement_all"] = agree
    with open(os.path.join(REPO, "artifacts", "falsification", hypothesis_id,
                           "independent.json"), "w", encoding="utf-8") as handle:
        json.dump(out, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP5-VRF-07]: agreement verdict recorded.
    console_log("WP5-VRF-07", "agreement %s %s" % (hypothesis_id, agree))
    return agree


def stage13(sizes=(2, 3, 4, 5, 6, 7)):
    """UH-4 tables for survivors; H05 independent verification for all."""
    from python.wp5 import structural as S
    from python.wp5.run_phase import CANDIDATES, write_uh, read_uh, set_ledger_status
    p_h, q_h = (int(v) for v in S.B_H)
    survivors = [h for h in CANDIDATES if dev_passed(h)]
    # console.log equivalent [WP5-VRF-08]: survivor set recorded.
    console_log("WP5-VRF-08", "survivors=%s" % (survivors,))
    if survivors:
        build_bh_tables(p_h, q_h, sizes)
        for hyp_id in survivors:
            bad = uh4_check(hyp_id, sizes)
            gates = read_uh(hyp_id)
            if bad:
                gates["UH-4"] = "REJECTED"
                write_uh(hyp_id, gates)
                set_ledger_status(hyp_id, "REJECTED at UH-4 (sandwich witness n=%d pid=%d)" % (
                    bad[0][0], bad[0][1]))
            else:
                gates["UH-4"] = "PASS"
                write_uh(hyp_id, gates)
    else:
        # console.log equivalent [WP5-VRF-09]: no-survivor branch recorded.
        console_log("WP5-VRF-09", "no survivors; UH-4 tables omitted (moot post-rejection)")
    for hyp_id in CANDIDATES:
        agree = independent_verify(hyp_id, sizes)
        gates = read_uh(hyp_id)
        already_out = any(str(gates[k]).startswith("REJECTED") for k in
                          ("UH-1", "UH-2", "UH-3", "UH-4", "UH-5"))
        if not agree:
            gates["UH-7"] = "REJECTED"
            write_uh(hyp_id, gates)
            set_ledger_status(hyp_id, "REJECTED at UH-7 (independent disagreement)")
        elif already_out:
            gates["UH-7"] = "AGREEMENT-VERIFIED (candidate already REJECTED; not survival)"
            write_uh(hyp_id, gates)
        else:
            gates["UH-7"] = "PASS"
            write_uh(hyp_id, gates)
    # console.log equivalent [WP5-VRF-10]: stage 13 complete.
    console_log("WP5-VRF-10", "stage 13 complete")
