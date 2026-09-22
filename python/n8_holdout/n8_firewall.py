"""n=8 holdout firewall: EMPTY -> SET_FROZEN -> UNLOCKED_ONCE (SA-03 normative).

Fail-closed state machine over an explicit state file. The SA-02 n6/n7
firewall (`python/mining/holdout_firewall.py`) is left byte-identical;
this module governs ONLY detailed-n8 candidate-evaluation paths.

Detailed-n8 substrings blocked pre-unlock: transition records, reachable
state list, tree-pair structures, per-edge costs, residuals, candidate
evaluations, maximizers, counterexamples, n8 structural feature tables.

Machinery self-test exception (SA-03.11, tested): when the candidate set is
EMPTY (nothing exists to adapt), the frozen SA-03 self-test may run the
sweep machinery with the degenerate H=0 TEST VECTOR; outputs stay in memory
/ test temp and NEVER enter artifacts/wp5/sa03/holdout/. Any other detailed
read pre-unlock raises N8FirewallError.
"""
import hashlib
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROD_STATE = os.path.join(REPO, "artifacts", "wp5", "sa03", "n8_firewall.json")
PROD_SET = os.path.join(REPO, "artifacts", "wp5", "sa03", "n8_candidate_set.json")

EMPTY, SET_FROZEN, UNLOCKED = "EMPTY", "SET_FROZEN", "UNLOCKED_ONCE"

DETAILED_N8_SUBSTRINGS = (
    "forward.bin", "inverse.bin", "reachable.json",
    "transition records", "reachable state list", "tree-pair",
    "per-edge costs", "residuals_", "candidate residuals",
    "maximizer", "counterexample", "candidate evaluation",
    "feature_table", "edge_deltas",
)


class N8FirewallError(AssertionError):
    pass


def _is_detailed_n8(path_text):
    text = str(path_text)
    has_n8 = ("n8" in text or "n_8" in text or "/8/" in text or "holdout" in text
              or "wp5/sa03" in text)
    has_detail = any(s in text for s in DETAILED_N8_SUBSTRINGS)
    return has_n8 and has_detail


def read_state(state_path=PROD_STATE):
    if not os.path.exists(state_path):
        raise N8FirewallError("no n8 firewall state at %s (refusing)" % state_path)
    with open(state_path, encoding="utf-8") as f:
        return json.load(f)


def _write_state(state_path, doc):
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    blob = (json.dumps(doc, sort_keys=True) + "\n").encode("utf-8")
    with open(state_path, "wb") as f:
        f.write(blob)
    return hashlib.sha256(blob).hexdigest()


def guard_n8_read(path_text, purpose="candidate evaluation", state_path=PROD_STATE,
                  test_vector=False):
    """Fail-closed gate for detailed-n8 reads.

    Raises N8FirewallError unless the firewall is UNLOCKED, or unless this is
    the frozen SA-03 machinery self-test (test_vector=True) running while the
    candidate set is EMPTY.
    """
    if not _is_detailed_n8(path_text):
        return True
    st = read_state(state_path)
    if st.get("state") == UNLOCKED:
        return True
    if test_vector and st.get("state") == EMPTY:
        cands = []
        try:
            with open(st.get("candidate_set", PROD_SET), encoding="utf-8") as f:
                cands = json.load(f).get("candidates", [])
        except FileNotFoundError:
            cands = []
        if cands == []:
            return True
    raise N8FirewallError(
        "N8_FIREWALL_BLOCKS: detailed n8 forbidden pre-unlock: %s (%s, state=%s)"
        % (path_text, purpose, st.get("state")))


def _set_hash(candidates):
    blob = (json.dumps({"candidates": candidates}, sort_keys=True) + "\n").encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def init_empty_state(state_path=PROD_STATE, set_path=PROD_SET):
    """One-time seeding of the EMPTY state. Refuses if state file exists."""
    if os.path.exists(state_path):
        raise N8FirewallError("seed refused: state file already exists")
    _write_state(state_path, {"state": EMPTY, "candidate_set": set_path,
                              "set_sha256": None, "unlock": None})
    return True


def freeze_candidate_set(candidates, state_path=PROD_STATE, set_path=PROD_SET):
    """Freeze the COMPLETE n8 candidate set. Refuses empty sets and non-EMPTY states."""
    if not candidates:
        raise N8FirewallError("cannot freeze an empty n8 candidate set")
    st = read_state(state_path)
    if st.get("state") != EMPTY:
        raise N8FirewallError("candidate set already frozen (state=%s)" % st.get("state"))
    seen = set()
    for c in candidates:
        for k in ("hypothesis_id", "sha256"):
            if k not in c:
                raise N8FirewallError("candidate entry missing %s" % k)
        if c["hypothesis_id"] in seen:
            raise N8FirewallError("duplicate hypothesis_id in set")
        seen.add(c["hypothesis_id"])
    doc = {"candidates": list(candidates), "set_sha256": _set_hash(list(candidates))}
    os.makedirs(os.path.dirname(set_path), exist_ok=True)
    with open(set_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, sort_keys=True, indent=2)
        f.write("\n")
    _write_state(state_path, {"state": SET_FROZEN, "candidate_set": set_path,
                              "set_sha256": doc["set_sha256"], "unlock": None})
    return doc["set_sha256"]


def unlock(candidate_id, state_path=PROD_STATE, set_path=PROD_SET):
    """Unlock n8 exactly once for one frozen-set member. Records set hash."""
    st = read_state(state_path)
    if st.get("state") != SET_FROZEN:
        raise N8FirewallError("n8 unlock requires SET_FROZEN (state=%s)" % st.get("state"))
    with open(set_path, encoding="utf-8") as f:
        cur = json.load(f)
    if _set_hash(cur.get("candidates", [])) != cur.get("set_sha256"):
        raise N8FirewallError("candidate set changed after freeze (internal mismatch)")
    if cur.get("set_sha256") != st.get("set_sha256"):
        raise N8FirewallError("candidate set changed after freeze (hash mismatch)")
    ids = [c["hypothesis_id"] for c in cur.get("candidates", [])]
    if candidate_id not in ids:
        raise N8FirewallError("unknown hypothesis_id for n8 unlock")
    _write_state(state_path, {"state": UNLOCKED, "candidate_set": set_path,
                              "set_sha256": cur["set_sha256"],
                              "unlock": {"candidate_id": candidate_id, "unlock_count": 1}})
    return True


def assert_set_unchanged(state_path=PROD_STATE, set_path=PROD_SET):
    """Detect post-unlock candidate-set modification (SA03-08).

    Two independent checks: the file's stored hash must match the frozen
    hash AND must match a recomputation over the file's own candidate list
    (catches additions that forget to rehash as well as rehashed tampering).
    """
    st = read_state(state_path)
    with open(set_path, encoding="utf-8") as f:
        cur = json.load(f)
    if _set_hash(cur.get("candidates", [])) != cur.get("set_sha256"):
        raise N8FirewallError("POST-UNLOCK CANDIDATE-SET MODIFICATION DETECTED (internal)")
    if cur.get("set_sha256") != st.get("set_sha256"):
        raise N8FirewallError("POST-UNLOCK CANDIDATE-SET MODIFICATION DETECTED (frozen)")
    return True


def status(state_path=PROD_STATE):
    return read_state(state_path)
