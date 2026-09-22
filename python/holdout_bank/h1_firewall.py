"""H1 hidden-bank firewall (SA-04 normative).

Quarantined namespace: artifacts/wp5/h1_holdout/ (bank records, secret
material) plus the generator's hidden seed. Blocked pre-unlock for
candidate synthesis: state encodings, history sequences, initial trees,
keys, modes, generator choices, hidden seed/material, per-size state IDs,
bank residuals. Published (aggregate-only) metadata stays visible via
explicit metadata_*() accessors — never individual cases.

Static blocking: assert_no_holdout_access() sweeps source namespaces for
forbidden references (run against current tree at freeze; future synthesis
namespaces get the same sweep). Dynamic blocking: guard_bank_read() fails
closed on any quarantined-namespace path pre-unlock.
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BANK_DIR = os.path.join(REPO, "artifacts", "wp5", "h1_holdout")
STATE_FILE = os.path.join(BANK_DIR, "h1_firewall.json")

EMPTY, UNLOCKED = "EMPTY", "UNLOCKED_ONCE"

# Substrings marking quarantined (detailed, hidden) bank content.
QUARANTINED_SUBSTRINGS = (
    "h1_holdout", "bank.json", "bank_secret", "holdout_bank",
    "bank residuals", "bank_residuals", "history_sequences",
)

# Aggregate-only metadata files explicitly publishable pre-unlock.
AGGREGATE_FILES = (
    "bank_manifest.json",
)

# Forbidden tokens for synthesis namespaces (static audit).
FORBIDDEN_TOKENS = (
    "holdout_bank", "h1_holdout", "bank.json", "bank_secret",
    "HOLDOUT-H1", "HOLDOUT_H1",
)


class H1FirewallError(AssertionError):
    pass


def read_state(state_path=STATE_FILE):
    if not os.path.exists(state_path):
        raise H1FirewallError("no H1 firewall state at %s (refusing)" % state_path)
    with open(state_path, encoding="utf-8") as f:
        return json.load(f)


def _is_quarantined(path_text):
    text = str(path_text)
    return any(s in text for s in QUARANTINED_SUBSTRINGS)


def guard_bank_read(path_text, purpose="candidate synthesis", state_path=STATE_FILE):
    """Fail-closed gate for quarantined bank reads. Aggregate manifest paths pass."""
    base = os.path.basename(str(path_text))
    if base in AGGREGATE_FILES:
        return True
    if not _is_quarantined(path_text):
        return True
    st = read_state(state_path)
    if st.get("state") == UNLOCKED:
        return True
    raise H1FirewallError(
        "H1_FIREWALL_BLOCKS: hidden bank forbidden pre-unlock: %s (%s, state=%s)"
        % (path_text, purpose, st.get("state")))


def metadata_bank_id(state_path=STATE_FILE):
    read_state(state_path)
    return "HOLDOUT-H1-v0.1"


def assert_no_holdout_access(source_dirs, repo_root=REPO):
    """Static audit: no forbidden holdout references in given source dirs.

    Returns list of hits (empty = clean). Scans .py files only, skipping the
    holdout_bank package itself, its tests, and this docstring's own mention
    context is irrelevant (token scan is literal).
    """
    hits = []
    for d in source_dirs:
        root = d if os.path.isabs(d) else os.path.join(repo_root, d)
        if not os.path.isdir(root):
            continue
        for base, _dirs, files in os.walk(root):
            # The firewall package itself legitimately names the namespace.
            if "holdout_bank" in base.replace(os.sep, "/"):
                continue
            for fn in sorted(files):
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(base, fn)
                try:
                    with open(p, encoding="utf-8") as f:
                        text = f.read()
                except OSError:
                    continue
                for tok in FORBIDDEN_TOKENS:
                    if tok in text:
                        hits.append("%s: %s" % (os.path.relpath(p, repo_root), tok))
    return hits
