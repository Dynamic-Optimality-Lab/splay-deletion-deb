"""WP-5 phase driver: freeze -> develop-gate -> verify -> adversarial -> holdout.

Stage 12 (this module, run_phase12): freeze H-0001..H-0003, UH-0..UH-3,
development UH-5 sweeps on revealed n<=7, OG diagnostics, n<=4 mutation
controls, per-candidate dev reports, ledger verdicts.
Stage 13 (run_phase13): shared U_{b_H},V_{b_H} tables (survivors only),
UH-4, independent H05 sweeps + transition re-derivation + agreement.
Stage 14 (run_phase14): adversarial campaigns, UH-8 verdicts, and — only if
survivors exist — frozen-set holdout consumption (n8 EV-8, H1 fresh, UH-6).

Usage: python -m python.wp5.run_phase --stage 12|13|14
Exact integer arithmetic throughout. Deterministic (fixed seeds, sorted I/O).
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

# console.log equivalent [WP5-RUN-01]: phase driver started.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


DEV_SIZES = (2, 3, 4, 5, 6, 7)
CANDIDATES = ("H-0001", "H-0002", "H-0003", "H-0004", "H-0005", "H-0006")


def load_ledger():
    with open(os.path.join(REPO, "artifacts", "hypotheses", "hypothesis_ledger.json"),
              encoding="utf-8") as handle:
        return json.load(handle)


def save_ledger(ledger):
    with open(os.path.join(REPO, "artifacts", "hypotheses", "hypothesis_ledger.json"),
              "w", encoding="utf-8") as handle:
        json.dump(ledger, handle, sort_keys=True, indent=2)
        handle.write("\n")


def set_ledger_status(hypothesis_id, status):
    ledger = load_ledger()
    for entry in ledger["hypotheses"]:
        if entry["hypothesis_id"] == hypothesis_id:
            entry["status"] = status
    save_ledger(ledger)


def check_freeze_preconditions():
    """Refuse the freeze if synthesis isolation or holdout states are off-nominal.

    Orchestration-side gate (this driver is explicitly excluded from the
    synthesis token scan; documented in static_audit.ORCHESTRATION_FILES).
    """
    # console.log equivalent [WP5-RUN-05]: freeze preconditions checked.
    console_log("WP5-RUN-05", "checking synthesis isolation + holdout states")
    from python.wp5 import static_audit as AUD
    hits = AUD.audit_synthesis_tree(REPO) + AUD.audit_self(REPO)
    if hits:
        raise AssertionError("synthesis isolation audit failed: %s" % hits)
    from python.n8_holdout import n8_firewall as N8FW
    from python.holdout_bank import h1_firewall as H1FW
    if N8FW.read_state().get("state") != N8FW.EMPTY:
        raise AssertionError("n8 firewall not EMPTY at freeze")
    if H1FW.read_state().get("state") != H1FW.EMPTY:
        raise AssertionError("H1 firewall not EMPTY at freeze")
    with open(os.path.join(REPO, "artifacts", "wp5", "sa03", "n8_candidate_set.json"),
              encoding="utf-8") as handle:
        if json.load(handle).get("candidates", [None]) != []:
            raise AssertionError("n8 candidate set not EMPTY at freeze")
    # console.log equivalent [WP5-RUN-06]: preconditions green.
    console_log("WP5-RUN-06", "preconditions green (isolation clean, both firewalls EMPTY)")


def read_uh(hypothesis_id):
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.uh.json" % hypothesis_id),
              encoding="utf-8") as handle:
        return json.load(handle)


def write_uh(hypothesis_id, gates):
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.uh.json" % hypothesis_id),
              "w", encoding="utf-8") as handle:
        json.dump(gates, handle, sort_keys=True, indent=2)
        handle.write("\n")


def write_phase_log(stage, summary):
    import time
    logdir = os.path.join(REPO, "artifacts", "logs")
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, "phase%s.json" % stage), "w", encoding="utf-8") as handle:
        json.dump({"experiment_id": "SPLAY-AM-PD-v0.1", "phase": "SPEC-%s" % stage,
                   "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "summary": summary}, handle, sort_keys=True, indent=2)
        handle.write("\n")


def uh_skeleton(hypothesis_id):
    return {"hypothesis_id": hypothesis_id,
            "UH-0": "PENDING", "UH-1": "PENDING", "UH-2": "PENDING",
            "UH-3": "PENDING", "UH-4": "PENDING", "UH-5": "PENDING",
            "UH-6": "PENDING", "UH-7": "PENDING", "UH-8": "PENDING",
            "OG-1": "PENDING", "OG-2": "PENDING", "OG-3": "PENDING"}


def write_uh(hypothesis_id, gates):
    path = os.path.join(REPO, "artifacts", "hypotheses", "%s.uh.json" % hypothesis_id)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(gates, handle, sort_keys=True, indent=2)
        handle.write("\n")


def stage12(resweep_only=False):
    """Freeze + UH-0..UH-3 + development UH-5 + OG + mutations.

    resweep_only=True regenerates ONLY deterministic dev evidence
    (n{n}.json sweeps, dev_summary, mutations) without touching frozen
    H files, uh.json verdicts, or ledger entries (used when the evidence
    record format is enriched; maxima are asserted identical).
    """
    from python.wp5 import candidates as C
    from python.wp5 import falsify as F
    from python.wp5 import mutation as M
    from python.wp5 import structural as S
    # console.log equivalent [WP5-RUN-02]: stage 12 begin.
    console_log("WP5-RUN-02", "stage 12 begin (resweep_only=%s)" % resweep_only)
    check_freeze_preconditions()
    if not resweep_only:
        C.main()
    p_h, q_h = (int(v) for v in S.B_H)
    for hyp_id in CANDIDATES:
        gates = uh_skeleton(hyp_id)
        gates["UH-0"] = "PASS"
        fdir = os.path.join(REPO, "artifacts", "falsification", hyp_id)
        os.makedirs(fdir, exist_ok=True)
        dev = {"hypothesis_id": hyp_id, "sizes": {}}
        rejected_at = None
        old_summary = None
        old_path = os.path.join(fdir, "dev_summary.json")
        if resweep_only:
            if not os.path.exists(old_path):
                raise AssertionError("resweep needs a prior dev_summary for %s" % hyp_id)
            with open(old_path, encoding="utf-8") as handle:
                old_summary = json.load(handle)
        domains = {}
        for n in DEV_SIZES:
            shapes, count, after, cost, pair_ids = F.load_domain_tables(n)
            h_table = F.build_h_table(hyp_id, n, shapes, count, pair_ids)
            domains[n] = (shapes, count, after, cost, pair_ids, h_table)
        for n in DEV_SIZES:
            shapes, count, after, cost, pair_ids, h_table = domains[n]
            rep = F.sweep_candidate(hyp_id, n, shapes, count, after, cost,
                                    pair_ids, h_table, p_h, q_h)
            with open(os.path.join(fdir, "n%d.json" % n), "w", encoding="utf-8") as handle:
                json.dump(rep, handle, sort_keys=True, indent=2)
                handle.write("\n")
            dev["sizes"][str(n)] = {
                "uh1_count": rep["uh1_count"], "uh2_count": rep["uh2_count"],
                "keep_max": rep["keep_max"], "keep_argmax": rep["keep_argmax"],
                "delete_max": rep["delete_max"], "delete_argmax": rep["delete_argmax"]}
            if rejected_at is None:
                if rep["uh1_count"] > 0:
                    rejected_at = ("UH-1", rep)
                elif rep["uh2_count"] > 0:
                    rejected_at = ("UH-2", rep)
                elif int(rep["keep_max"]) > 0 or int(rep["delete_max"]) > 0:
                    rejected_at = ("UH-5", rep)
        with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.bH_feasibility.json" % hyp_id),
                  encoding="utf-8") as handle:
            bh = json.load(handle)
        gates["UH-3"] = ("PASS" if all(r["verdict"] == "PASS" for r in bh["records"])
                         else "REJECTED")
        if gates["UH-3"] != "PASS":
            rejected_at = ("UH-3", None)
        gates["UH-1"] = "PASS" if all(dev["sizes"][str(n)]["uh1_count"] == 0 for n in DEV_SIZES) else "REJECTED"
        gates["UH-2"] = "PASS" if all(dev["sizes"][str(n)]["uh2_count"] == 0 for n in DEV_SIZES) else "REJECTED"
        gates["UH-5"] = "PASS" if all(int(dev["sizes"][str(n)]["keep_max"]) <= 0
                                      and int(dev["sizes"][str(n)]["delete_max"]) <= 0
                                      for n in DEV_SIZES) else "REJECTED"
        og = {}
        for n in DEV_SIZES:
            shapes, count, _after, _cost, _pairs, h_table = domains[n]
            og[str(n)] = F.og2_og3_material(hyp_id, n, h_table)
        og["mirror_probe"] = {}
        for n in (4, 5, 6):
            shapes, count, _after, _cost, pair_ids, _h = domains[n]
            og["mirror_probe"][str(n)] = F.mirror_probe(
                hyp_id, n, shapes, count, pair_ids)
        ood = {}
        for n in (2, 3, 4, 5):
            shapes, count, after, cost, _pairs, h_table = domains[n]
            ood[str(n)] = F.out_of_domain_panel(
                hyp_id, n, shapes, count, after, cost, h_table, p_h, q_h)
        dev["og"] = og
        dev["out_of_domain"] = ood
        with open(os.path.join(fdir, "dev_summary.json"), "w", encoding="utf-8") as handle:
            json.dump(dev, handle, sort_keys=True, indent=2)
            handle.write("\n")
        formula_fn, _cls, _text = S.H_REGISTRY[hyp_id]
        mut = M.run_mutation_suite(hyp_id, formula_fn, p_h, q_h, fdir)
        dev["mutations"] = mut
        with open(os.path.join(fdir, "dev_summary.json"), "w", encoding="utf-8") as handle:
            json.dump(dev, handle, sort_keys=True, indent=2)
            handle.write("\n")
        if resweep_only:
            if dev["sizes"] != old_summary["sizes"]:
                raise AssertionError("resweep maxima drift for %s (refusing)" % hyp_id)
            # console.log equivalent [WP5-RUN-08]: resweep verified identical.
            console_log("WP5-RUN-08", "resweep %s maxima identical" % hyp_id)
            continue
        gates["OG-1"] = "REPORTED"
        gates["OG-2"] = "REPORTED"
        gates["OG-3"] = "REPORTED"
        write_uh(hyp_id, gates)
        if rejected_at is not None:
            set_ledger_status(hyp_id, "REJECTED at %s (development, preserved)" % rejected_at[0])
        else:
            set_ledger_status(hyp_id, "DEV-PASS (UH-0..UH-3,UH-5 green on n<=7)")
        # console.log equivalent [WP5-RUN-03]: candidate development gated.
        console_log("WP5-RUN-03", "dev verdict %s rejected_at=%s" % (
            hyp_id, rejected_at[0] if rejected_at else None))
    # console.log equivalent [WP5-RUN-04]: stage 12 complete.
    console_log("WP5-RUN-04", "stage 12 complete")


def main(argv=None):
    import argparse
    import time
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("12", "13", "14"), required=True)
    parser.add_argument("--sweeps-only", action="store_true",
                        help="regenerate deterministic dev evidence without re-freezing")
    args = parser.parse_args(argv)
    t0 = time.time()
    if args.stage == "12":
        stage12(resweep_only=args.sweeps_only)
        write_phase_log("12", {"candidates": list(CANDIDATES),
                               "resweep_only": args.sweeps_only,
                               "wall_seconds": round(time.time() - t0, 1)})
    elif args.stage == "13":
        from python.wp5 import run_verify as _v
        _v.stage13()
        write_phase_log("13", {"wall_seconds": round(time.time() - t0, 1)})
    else:
        from python.wp5 import run_adversarial as _a
        survivors = _a.stage14()
        write_phase_log("14", {"survivors": survivors,
                               "wall_seconds": round(time.time() - t0, 1)})
    # console.log equivalent [WP5-RUN-07]: phase log sealed.
    console_log("WP5-RUN-07", "stage %s log sealed" % args.stage)
    return 0


if __name__ == "__main__":
    sys.exit(main())
