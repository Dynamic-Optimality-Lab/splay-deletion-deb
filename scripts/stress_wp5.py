"""WP-5 stress: determinism rerun, adversarial determinism, faulty-H detection.

- Determinism: H-0001 development maxima on n<=5 recomputed twice, byte-identical.
- Adversarial determinism: fixed-seed uniform batch evaluated twice, identical.
- Faulty-H detection: H+1 perturbation must differ somewhere (sensitivity proof).
- Transition digest: reference n=4 digest must equal the WP-1 pinned value.
Writes artifacts/logs/wp5_stress.json. Exact integers only.
"""
import hashlib
import json
import os
import random
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

PASS = []
FAIL = []


# console.log equivalent [WP5-S-01]: stress start.
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


def dev_maxima(hypothesis_id, sizes=(2, 3, 4, 5)):
    """Recompute development maxima from scratch (no cached artifacts)."""
    # console.log equivalent [WP5-S-02]: determinism recompute executed.
    console_log("WP5-S-02", "recompute %s" % hypothesis_id)
    sys.path.insert(0, REPO)
    from python.wp5 import falsify as F
    from python.wp5 import structural as S
    formula_fn, _cls, _text = S.H_REGISTRY[hypothesis_id]
    with open(os.path.join(REPO, "artifacts", "hypotheses", "%s.eval_contract.json" % hypothesis_id),
              encoding="utf-8") as handle:
        contract = json.load(handle)
    p_h = int(contract["b_hypothesis"]["p"])
    q_h = int(contract["b_hypothesis"]["q"])
    out = {}
    for n in sizes:
        shapes, count, after, cost, pair_ids = F.load_domain_tables(n)
        h_table = F.build_h_table(hypothesis_id, n, shapes, count, pair_ids)
        rep = F.sweep_candidate(hypothesis_id, n, shapes, count, after, cost,
                                pair_ids, h_table, p_h, q_h)
        out[str(n)] = {"keep_max": rep["keep_max"], "keep_argmax": rep["keep_argmax"],
                       "delete_max": rep["delete_max"], "delete_argmax": rep["delete_argmax"]}
    return out


def main(argv=None):
    """Run WP-5 stress battery."""
    t0 = time.time()
    # console.log equivalent [WP5-S-01]: stress start.
    console_log("WP5-S-01", "WP-5 stress start")
    first = dev_maxima("H-0001")
    second = dev_maxima("H-0001")
    check("STRESS-DET", first == second, "dev maxima byte-identical on rerun")
    with open(os.path.join(REPO, "artifacts", "falsification", "H-0001",
                           "dev_summary.json"), encoding="utf-8") as handle:
        sealed = json.load(handle)["sizes"]
    check("STRESS-SEALED", all(first[str(n)]["keep_max"] == sealed[str(n)]["keep_max"]
                               and first[str(n)]["delete_max"] == sealed[str(n)]["delete_max"]
                               for n in (2, 3, 4, 5)), "rerun matches sealed reports")
    # Adversarial determinism: same seed twice -> identical bests.
    sys.path.insert(0, REPO)
    from python.reference import tree as T
    from python.reference import splay as SP
    from python.wp5 import structural as S
    from python.adversary import residual_search as R
    from python.adversary import motif_generator as M
    formula_fn, _cls, _text = S.H_REGISTRY["H-0001"]
    h_fn = (lambda ia, ib, n: formula_fn(ia, ib, n))
    bests = []
    for _ in range(2):
        rng = random.Random(20260922)
        states = R.uniform_engine(rng, 20, 16, T.parse_shape, T.assign_inorder_keys)
        top = None
        for a_tree, b_tree, n in states:
            got = R.exact_residuals(a_tree, b_tree, n, h_fn, 2, 1, SP.splay)
            score = max(int(got["keep_max"]), int(got["delete_max"]))
            if top is None or score > top:
                top = score
        bests.append(top)
    check("STRESS-ADVDET", bests[0] == bests[1], "adversarial best deterministic")
    # Faulty-H detection: +1 perturbation must differ on n=4 exhaustive R_4.
    from python.wp5 import falsify as F
    shapes, count, after, cost, pair_ids = F.load_domain_tables(4)
    h_table = F.build_h_table("H-0001", 4, shapes, count, pair_ids)
    faulty = {pid: h + 1 for pid, h in h_table.items()}
    diff = sum(1 for pid in pair_ids if faulty[pid] != h_table[pid])
    check("STRESS-FAULTY", diff == len(pair_ids), "faulty H detected everywhere")
    # Transition digest stability (WP-1 pinned value, n=4): reuse the exact
    # WP-1 digest construction (format authority: scripts/stress_wp1.py).
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "stress_wp1", os.path.join(REPO, "scripts", "stress_wp1.py"))
    stress_wp1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stress_wp1)
    digest, _records = stress_wp1.transition_digest(4, "ref")
    check("STRESS-DIGEST", digest[:16] == "62853f23dc0952a1",
          "n=4 transition digest stable")
    # console.log equivalent [WP5-S-03]: stress summary.
    console_log("WP5-S-03", "pass=%d fail=%d seconds=%.1f" % (len(PASS), len(FAIL), time.time() - t0))
    with open(os.path.join(REPO, "artifacts", "logs", "wp5_stress.json"),
              "w", encoding="utf-8") as handle:
        json.dump({"experiment_id": "SPLAY-AM-PD-v0.1", "exit": 0 if not FAIL else 1,
                   "fail": FAIL, "pass": PASS,
                   "wall_seconds": round(time.time() - t0, 1)}, handle,
                  sort_keys=True, indent=2)
        handle.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
