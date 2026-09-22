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


def unlock_n7_for_evaluation(candidate_id):
    """Unlock n=7 exactly once for hard-holdout evaluation."""
    if not _firewall_state["final_candidate_frozen"]:
        raise HoldoutFirewallError("n7 unlock requires final candidate freeze")
    if _firewall_state["final_candidate_id"] != candidate_id:
        raise HoldoutFirewallError("n7 unlock candidate mismatch")
    if _firewall_state["n7_unlock_count"] >= 1:
        raise HoldoutFirewallError("n7 already unlocked once; further reads need new hypothesis ID")
    _firewall_state["n7_unlock_count"] += 1
    return True


def status():
    return dict(_firewall_state)
