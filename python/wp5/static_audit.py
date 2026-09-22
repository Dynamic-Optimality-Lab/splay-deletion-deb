"""Static synthesis-isolation audit (WP-5, SA-03/SA-04 normative).

Candidate SYNTHESIS files (generation + development falsification + adversary
code) must contain no reference to hidden-bank or pre-unlock holdout
namespaces. Post-unlock EVALUATION code (python/wp5/holdout.py) is outside
this scan by design: it runs only after unlock and imports bank packages
inside post-unlock functions (deferred imports, documented).

Scanned synthesis file list is explicit (fail-closed: unknown future files
are NOT silently covered; the WP-5 gate test asserts this exact list plus a
directory sweep for new .py files under python/wp5/ and python/adversary/).
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# console.log equivalent [WP5-AUD-01]: static audit helper loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


FORBIDDEN_TOKENS = (
    "holdout_bank",
    "h1_holdout",
    "bank.json",
    "bank_secret",
    "HOLDOUT-H1",
    "HOLDOUT_H1",
    "bank_manifest",
    "n8_holdout",
    "n8_candidate_set",
    "n8_firewall",
)

_QUARANTINED_DATA_MARKERS = (
    "bank.json",
    "bank_secret",
    "forward.bin",
    "inverse.bin",
    "reachable.json",
    "feature_table",
    "edge_deltas",
)

# Strict synthesis files: no holdout/n8-detail tokens, no holdout/n8 imports.
# Orchestration files (run_phase/run_verify/run_adversarial/holdout) are NOT
# in this list: they run gates and post-unlock evaluation (documented), never
# synthesize. This audit module itself is excluded: it only DEFINES the token
# list and performs no reads (structurally enforced below).
SYNTHESIS_FILES = (
    "python/wp5/__init__.py",
    "python/wp5/structural.py",
    "python/wp5/candidates.py",
    "python/wp5/falsify.py",
    "python/wp5/mutation.py",
    "python/adversary/__init__.py",
    "python/adversary/motif_generator.py",
    "python/adversary/residual_search.py",
    "python/adversary/hill_climb.py",
    "python/adversary/genetic_search.py",
    "python/adversary/witness_generalizer.py",
    "python/wp5_independent/__init__.py",
    "python/wp5_independent/independent.py",
)

# Orchestration modules: allowed control-plane references (gate checks and
# post-unlock evaluation only); audited by documented exclusion here.
ORCHESTRATION_FILES = (
    "python/wp5/run_phase.py",
    "python/wp5/run_verify.py",
    "python/wp5/run_adversarial.py",
    "python/wp5/holdout.py",
    "python/wp5/static_audit.py",
)


def audit_files(rel_paths, repo_root=REPO):
    """Literal token scan over explicit synthesis files. Returns hit list."""
    hits = []
    for rel in rel_paths:
        path = rel if os.path.isabs(rel) else os.path.join(repo_root, rel)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        for token in FORBIDDEN_TOKENS:
            if token in text:
                hits.append("%s: %s" % (rel, token))
    return hits


def audit_self(repo_root=REPO):
    """Structural self-check at AST level: this module DEFINES the token list
    (data) but never imports holdout packages nor names quarantined data
    files outside that definition."""
    import ast
    with open(os.path.join(repo_root, "python", "wp5", "static_audit.py"),
              encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""])
            for name in names:
                if "holdout_bank" in name or "n8_holdout" in name:
                    hits.append("python/wp5/static_audit.py: bank import %s" % name)
    # String literals outside the two marker-definition sites themselves.
    def_lines = set()
    for target_id in ("FORBIDDEN_TOKENS", "_QUARANTINED_DATA_MARKERS"):
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                    getattr(t, "id", "") == target_id for t in node.targets):
                for other in ast.walk(node):
                    lineno = getattr(other, "lineno", None)
                    if lineno is not None:
                        def_lines.add(lineno)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if getattr(node, "lineno", None) in def_lines:
                continue
            for marker in _QUARANTINED_DATA_MARKERS:
                if marker in node.value:
                    hits.append("python/wp5/static_audit.py: data literal %s" % marker)
    return hits


def audit_synthesis_tree(repo_root=REPO):
    """Scan synthesis files + fail if unknown .py files appeared unscanned."""
    import glob
    hits = audit_files(SYNTHESIS_FILES, repo_root)
    hits.extend(audit_self(repo_root))
    for directory in ("python/wp5", "python/adversary", "python/wp5_independent"):
        root = os.path.join(repo_root, directory)
        if not os.path.isdir(root):
            continue
        for path in sorted(glob.glob(os.path.join(root, "*.py"))):
            rel = os.path.relpath(path, repo_root).replace(os.sep, "/")
            if rel in ORCHESTRATION_FILES:
                continue  # documented orchestration exclusion (see above)
            if rel not in SYNTHESIS_FILES:
                hits.append("%s: UNSCANNED-NEW-FILE" % rel)
    return hits
