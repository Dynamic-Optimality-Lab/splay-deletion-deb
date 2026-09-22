"""Seed SA-03 WP-5 artifacts (EMPTY candidate set, locked firewall, known aggregates)."""
import hashlib
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(REPO, "artifacts", "wp5", "sa03")
os.makedirs(D, exist_ok=True)


def dump(name, doc):
    p = os.path.join(D, name)
    blob = (json.dumps(doc, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with open(p, "wb") as f:
        f.write(blob)
    print("seed %s sha=%s" % (name, hashlib.sha256(blob).hexdigest()[:16]))


if os.path.exists(os.path.join(D, "n8_firewall.json")):
    raise SystemExit("SEED REFUSED: n8_firewall.json already exists (re-seeding needs a new amendment)")
ledger = json.load(open(os.path.join(REPO, "artifacts", "hypotheses", "hypothesis_ledger.json"),
                        encoding="utf-8"))
by_id = {h["hypothesis_id"]: h["sha256"] for h in ledger["hypotheses"]}

dump("candidate_eras.json", {
    "amendment": "SA-03",
    "era_a_pre_n7": [
        {"hypothesis_id": "H-SA02-B-v1", "sha256": by_id["H-SA02-B-v1"],
         "note": "frozen before SA-02 n7 reveal; historical labels immutable"},
        {"hypothesis_id": "H-SA02-B-v1-final", "sha256": by_id["H-SA02-B-v1-final"],
         "note": "its own n7 evaluation WAS the reveal event (unlock_count 1); immutable"},
    ],
    "era_b_post_n7": [
        {"hypothesis_id": "H-SA02-C-1", "sha256": by_id["H-SA02-C-1"],
         "note": "POST_N7 from birth; heldout_sizes []"},
        {"hypothesis_id": "H-SA02-C-2", "sha256": by_id["H-SA02-C-2"],
         "note": "POST_N7 from birth; heldout_sizes []"},
    ],
    "rule": "every hypothesis created after WP-4 completion is ERA B (POST_N7).",
})

empty_set = {"candidates": []}
empty_hash = hashlib.sha256((json.dumps(empty_set, sort_keys=True) + "\n").encode("utf-8")).hexdigest()
dump("n8_candidate_set.json", {"candidates": [], "set_sha256": empty_hash,
                               "note": "EMPTY at SA-03 freeze: no WP-5 candidate exists yet"})

dump("n8_firewall.json", {"state": "EMPTY",
                          "candidate_set": "artifacts/wp5/sa03/n8_candidate_set.json",
                          "set_sha256": empty_hash, "unlock": None,
                          "note": "initial SA-03 state: detailed n8 blocked; test-vector self-test only"})

dump("n8_known_aggregates.json", {
    "category": "PREVIOUSLY_KNOWN_AGGREGATE_METADATA",
    "n": 8,
    "catalan_C_8": 1430,
    "R_8_size": 2044900,
    "all_pairs_reachable_observed": True,
    "transition_records": 11440,
    "transition_audit": "PASS",
    "reachability_audit": "PASS",
    "forward_sha256": "7c2d8c5d9309da09f6a5f01f8ca0883337825288092e9b6b849a3a84da7cfa5d",
    "inverse_sha256": "3f686c289467510569a83adad472c5d82bf1f0421945e51ad2bc0a2c002a3d20",
    "reachable_sha256": "d6f5e920180cc9ba335a47b7f8a58358af58d8aa49efa233d7caecec88757647",
    "b_8_star": "UNSEALED (RESOURCE_LIMIT_NO_CLAIM)",
    "edge_checks_exact": 32718400,
    "note": "aggregates only; not candidate-selection inputs",
})
print("seed done")
