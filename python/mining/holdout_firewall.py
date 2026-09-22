"""SA-02 holdout firewall (normative, fail-closed).

Before final Track-B candidate freeze, mining code MUST refuse to load
detailed n=7 for hypothesis generation, and initial fitting code MUST refuse
detailed n=6 until the initial candidate is frozen.

Detailed n=7 (forbidden before final freeze):
  forced_delta_edges, critical cycles, trajectories, feature deltas,
  candidate residuals, per-edge provenance.
Detailed n=6 (forbidden during initial fit):
  cycle anatomy, forced deltas / residuals for fitting.

Aggregate metadata already known from sealed WP-3 summaries (b_7*=23/14,
counts, subtype; b_6*=8/5, counts) is NOT detailed structure and remains
loadable; it is ledgered as PREVIOUSLY KNOWN in contamination_ledger.json.

Unlock: exactly once, requires frozen final candidate ID + recorded hash.
Any post-n7 candidate change -> new hypothesis ID, loses untouched claim.
"""

import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_firewall_state = {
    "initial_candidate_frozen": False,
    "initial_candidate_id": None,
    "final_candidate_frozen": False,
    "final_candidate_id": None,
    "n7_unlock_count": 0,
}

DETAILED_N7_SUBSTRINGS = (
    "forced_delta_edges",
    "canonical_cycles",
    "critical",
    "trajectories",
    "edge_deltas",
    "candidate residuals",
    "residuals_",
    "per-edge provenance",
)

DETAILED_N6_SUBSTRINGS = (
    "cycle_anatomy",
    "forced_delta",
    "edge_deltas",
    "residuals_",
)


class HoldoutFirewallError(AssertionError):
    pass


def reset_for_tests():
    _firewall_state.update({
        "initial_candidate_frozen": False,
        "initial_candidate_id": None,
        "final_candidate_frozen": False,
        "final_candidate_id": None,
        "n7_unlock_count": 0,
    })


def freeze_initial_candidate(candidate_id):
    if not candidate_id:
        raise HoldoutFirewallError("initial freeze requires non-empty candidate ID")
    _firewall_state["initial_candidate_frozen"] = True
    _firewall_state["initial_candidate_id"] = candidate_id


def freeze_final_candidate(candidate_id):
    if not candidate_id:
        raise HoldoutFirewallError("final freeze requires non-empty candidate ID")
    if not _firewall_state["initial_candidate_frozen"]:
        raise HoldoutFirewallError("final freeze requires initial freeze first")
    _firewall_state["final_candidate_frozen"] = True
    _firewall_state["final_candidate_id"] = candidate_id


def _initial_frozen_on_disk():
    import json as json_mod
    cand = os.path.join(REPO, "artifacts", "hypotheses", "H-SA02-B-v1.json")
    if os.path.exists(cand):
        try:
            with open(cand, encoding="utf-8") as f:
                json_mod.load(f)
            return True
        except Exception:
            return False
    return False


def _final_frozen_on_disk():
    import glob as glob_mod
    pats = [
        os.path.join(REPO, "artifacts", "hypotheses", "H-SA02-B-*-final.json"),
        os.path.join(REPO, "artifacts", "hypotheses", "H-SA02-B-v1-final.json"),
    ]
    for pat in pats:
        if glob_mod.glob(pat):
            return True
    return False


def hydrate_from_files():
    """Load persistent freeze state from sealed hypothesis files (production).

    Tests use reset_for_tests + explicit in-memory freezes and must NOT call
    this (keeps unit tests isolated from on-disk production freezes).
    """
    import glob as glob_mod
    import json as json_mod
    if _initial_frozen_on_disk() and not _firewall_state["initial_candidate_frozen"]:
        _firewall_state["initial_candidate_frozen"] = True
        _firewall_state["initial_candidate_id"] = "H-SA02-B-v1"
    finals = glob_mod.glob(os.path.join(REPO, "artifacts", "hypotheses", "H-SA02-B-*-final.json"))
    if finals and not _firewall_state["final_candidate_frozen"]:
        try:
            with open(finals[0], encoding="utf-8") as f:
                doc = json_mod.load(f)
            _firewall_state["final_candidate_frozen"] = True
            _firewall_state["final_candidate_id"] = doc.get("hypothesis_id", finals[0])
        except Exception:
            pass
    unlock_path = os.path.join(REPO, "artifacts", "audits", "n7_unlock.json")
    if os.path.exists(unlock_path):
        try:
            with open(unlock_path, encoding="utf-8") as f:
                doc = json_mod.load(f)
            _firewall_state["n7_unlock_count"] = int(doc.get("unlock_count", 1))
        except Exception:
            _firewall_state["n7_unlock_count"] = 1


def _is_detailed_n7_path(path_text):
    text = str(path_text)
    has_n7 = ("n7" in text or "n_7" in text or "/7/" in text or "holdout" in text)
    has_detail = any(s in text for s in DETAILED_N7_SUBSTRINGS)
    return has_n7 and has_detail


def _is_detailed_n6_path(path_text):
    text = str(path_text)
    has_n6 = ("n6" in text or "n_6" in text or "/6/" in text)
    has_detail = any(s in text for s in DETAILED_N6_SUBSTRINGS)
    return has_n6 and has_detail


def guard_load(path_text, purpose="hypothesis generation"):
    """Fail-closed gate called before any artifact read for fitting.

    Raises HoldoutFirewallError on prohibited reads.
    Production processes must call hydrate_from_files() at startup to load
    persistent freeze state; unit tests use reset_for_tests + explicit
    in-memory freezes and never hydrate (isolation).
    """
    if _is_detailed_n7_path(path_text) and not _firewall_state["final_candidate_frozen"]:
        raise HoldoutFirewallError(
            "HOLDOUT_FIREWALL_BLOCKS_N7: detailed n=7 forbidden before final freeze: %s (%s)"
            % (path_text, purpose)
        )
    return True


def guard_initial_fit_load(path_text):
    """Additional gate for initial Track-B fitting (blocks detailed n=6)."""
    guard_load(path_text, purpose="initial fitting")
    if _is_detailed_n6_path(path_text) and not _firewall_state["initial_candidate_frozen"]:
        raise HoldoutFirewallError(
            "HOLDOUT_FIREWALL_BLOCKS_N6_DURING_FIT: detailed n=6 forbidden during initial fit: %s"
            % (path_text,)
        )
    return True


def unlock_n7_for_evaluation(candidate_id, write_file=True):
    """Unlock n=7 exactly once for hard-holdout evaluation.

    write_file=False is for unit tests only (in-memory once-only without
    touching the production unlock record).
    """
    import json as json_mod
    if not _firewall_state["final_candidate_frozen"]:
        raise HoldoutFirewallError("n7 unlock requires final candidate freeze")
    if _firewall_state["final_candidate_id"] != candidate_id:
        raise HoldoutFirewallError("n7 unlock candidate mismatch")
    if _firewall_state["n7_unlock_count"] >= 1:
        raise HoldoutFirewallError("n7 already unlocked once; further reads need new hypothesis ID")
    if write_file:
        unlock_path = os.path.join(REPO, "artifacts", "audits", "n7_unlock.json")
        if os.path.exists(unlock_path):
            raise HoldoutFirewallError("n7 already unlocked once; further reads need new hypothesis ID")
    _firewall_state["n7_unlock_count"] += 1
    if not write_file:
        return True
    os.makedirs(os.path.dirname(unlock_path), exist_ok=True)
    with open(unlock_path, "w", encoding="utf-8") as f:
        json_mod.dump({"candidate_id": candidate_id, "unlock_count": 1}, f, sort_keys=True)
        f.write("\n")
    return True


def status():
    return dict(_firewall_state)


# WP-4 completion marker (additive; changes no existing gate behavior).
# The n=7 hard holdout was consumed exactly once by H-SA02-B-v1-final
# (record artifacts/audits/n7_unlock.json). From commit 072b211 onward:
N7_STATUS = "PREVIOUSLY_REVEALED_AFTER_H-SA02-B-v1-final_FREEZE"


def require_post_n7_label(candidate_id):
    """Fail-closed label gate for every post-reveal candidate family.

    Any hypothesis ID created after commit 072b211 MUST be recorded with
    n7_status = PREVIOUSLY_REVEALED_AFTER_H-SA02-B-v1-final_FREEZE and MUST
    NOT claim n=7 as an untouched holdout. Returns the mandatory label
    string; raises HoldoutFirewallError for the consumed untouched IDs
    (fresh claims under H-SA02-B-v1* are forbidden).
    """
    if candidate_id in ("H-SA02-B-v1", "H-SA02-B-v1-final"):
        raise HoldoutFirewallError(
            "untouched n=7 already consumed by %s; new work needs a new hypothesis ID "
            "with POST-n7-DEVELOPMENT labeling" % candidate_id
        )
    return N7_STATUS
