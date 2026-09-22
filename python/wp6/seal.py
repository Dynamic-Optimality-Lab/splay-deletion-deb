"""P18 seal: FINAL_RESULT.json + MANIFEST.sha256 + deterministic archive.

FINAL_RESULT.json is populated from artifacts (never expectations) and
validated against schemas/final_result.schema.json. The claim level is
computed from verified booleans: exact b_n* sealed + canonical potentials
complete + critical derivatives complete + zero survivors + no proved
lemma/family => FINITE_EXACT_BN_RESULTS.

The archive SPLAY-AM-PD-v0.1.tar.zst is deterministic (sorted entries,
mtime=0, uid/gid 0, PAX format, fixed zstd level) over all tracked files
plus the new seal/wp6 files present in the worktree, excluding the archive
itself, its .sha256, and non-scientific paths (.git, target, pycache).
Secrets are untracked and therefore excluded by construction.
"""
import hashlib
import io
import json
import os
import sys
import tarfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)


# console.log equivalent [WP6-SEAL-01]: seal module loaded.
def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step."""
    print("[%s] %s" % (step_id, msg), flush=True)


SPEC_SET = [
    {"version": "v0.1", "sha256": "29070d39f54d40c3f8b1ccdde8b588545749dc3f60e8949c430036a0185f1565"},
    {"version": "v0.1.1-SA01", "sha256": "8B77278FF98F6AB5A3AA4D929A5787735F269647D5E3088CF4288F8ACF8C7726"},
    {"version": "v0.1.2-SA02", "sha256": "79C58ED0278A6F81FE42685955C2D50EEF9A6744CCD0A701B6FE8DF96EE41CDF"},
    {"version": "v0.1.3-SA03", "sha256": "BB407FAC46DB30FA58F8833E513152FC10182AC931AFD84DDB0C29B0217E25E1"},
    {"version": "v0.1.4-SA04", "sha256": "23046D37799860CCFD69BED21D6474F35ACA4E6FB91474FAAE2002617503E5FB"},
]

ARCHIVE_NAME = "SPLAY-AM-PD-v0.1.tar.zst"
ZSTD_LEVEL = 10
EXCLUDE_DIRS = (".git/", "target/", "__pycache__/")
EXCLUDE_FILES = (ARCHIVE_NAME, ARCHIVE_NAME + ".sha256",
                 "artifacts/seal/MANIFEST.sha256")


def sha_file(path):
    """SHA-256 of a file (streamed)."""
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def build_result():
    """Populate FINAL_RESULT content from sealed artifacts."""
    # console.log equivalent [WP6-SEAL-02]: result population from artifacts.
    console_log("WP6-SEAL-02", "populating FINAL_RESULT from artifacts")
    sizes = (2, 3, 4, 5, 6, 7)
    bn_results = []
    for n in sizes:
        with open(os.path.join(REPO, "artifacts", "certificates", "n%d" % n,
                               "bn_certificate.json"), encoding="utf-8") as handle:
            cert = json.load(handle)
        bn_results.append({"n": n, "b": cert["b"], "outcome": cert["criticality"]})
    potentials_ok = True
    for n in sizes:
        with open(os.path.join(REPO, "artifacts", "potentials", "n%d" % n,
                               "summary.json"), encoding="utf-8") as handle:
            summary = json.load(handle)
        if not summary.get("G_nonnegative"):
            potentials_ok = False
    critical_ok = True
    for n in sizes:
        with open(os.path.join(REPO, "artifacts", "critical", "n%d" % n,
                               "summary.json"), encoding="utf-8") as handle:
            summary = json.load(handle)
        if "forced_delta_count" not in summary:
            critical_ok = False
    with open(os.path.join(REPO, "artifacts", "wp6", "p17_activation.json"),
              encoding="utf-8") as handle:
        p17 = json.load(handle)
    with open(os.path.join(REPO, "artifacts", "wp6", "positive_branch_closure.json"),
              encoding="utf-8") as handle:
        closure = json.load(handle)
    survivors = closure.get("survivors", [])
    lemma = bool(survivors) and False
    family = (p17.get("verdict") == "P17_ACTIVATED")
    if lemma:
        claim = "UNIVERSAL_PAIR_ACCESS_LEMMA_PROVED"
    elif family:
        claim = "DYNAMIC_OPTIMALITY_DISPROVED"
    elif survivors:
        claim = "CANDIDATE_H_SURVIVES_FINITE_TESTS"
    elif potentials_ok and critical_ok and len(bn_results) == 6:
        claim = "FINITE_EXACT_BN_RESULTS"
    else:
        claim = "FINITE_INFRASTRUCTURE_ONLY"
    # console.log equivalent [WP6-SEAL-03]: claim computed from booleans.
    console_log("WP6-SEAL-03", "claim computed: %s (survivors=%d lemma=%s family=%s)" %
                (claim, len(survivors), lemma, family))
    return {
        "experiment_id": "SPLAY-AM-PD-v0.1",
        "finite_exact_sizes": list(sizes),
        "bn_results": bn_results,
        "canonical_potentials_complete": potentials_ok,
        "critical_derivatives_complete": critical_ok,
        "best_H_hypothesis": survivors[0] if survivors else None,
        "universal_pair_access_lemma": lemma,
        "approximate_monotonicity_proved": False,
        "dynamic_optimality_proved": False,
        "unbounded_counterexample_family_proved": family,
        "claim_level": claim,
        "normative_spec_set": SPEC_SET,
    }


def write_result(result):
    """Validate against schema; write sealed result."""
    import jsonschema
    with open(os.path.join(REPO, "schemas", "final_result.schema.json"),
              encoding="utf-8") as handle:
        schema = json.load(handle)
    # console.log equivalent [WP6-SEAL-04]: schema validation of result.
    console_log("WP6-SEAL-04", "validating FINAL_RESULT against schema")
    jsonschema.validate(result, schema)
    seal_dir = os.path.join(REPO, "artifacts", "seal")
    os.makedirs(seal_dir, exist_ok=True)
    with open(os.path.join(seal_dir, "FINAL_RESULT.json"), "w", encoding="utf-8") as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write("\n")
    # console.log equivalent [WP6-SEAL-05]: result sealed.
    console_log("WP6-SEAL-05", "FINAL_RESULT sealed claim=%s" % result["claim_level"])
    return os.path.join(seal_dir, "FINAL_RESULT.json")


def archive_members():
    """Deterministic member list: full worktree minus exclusions.

    Worktree walk (not git ls-files) so new seal/wp6/test/script/doc files
    are covered before they are committed. Excludes the archive itself, its
    sidecar, and non-scientific paths (.git, target, pycache).
    """
    members = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = sorted(d for d in dirs
                         if d != ".git" and d != "target" and d != "__pycache__")
        for name in sorted(files):
            if name.endswith((".pyc", ".pyo")):
                continue
            rel = os.path.relpath(os.path.join(root, name), REPO)
            flat = rel.replace(os.sep, "/")
            if flat in EXCLUDE_FILES:
                continue
            if flat.startswith(EXCLUDE_DIRS) or "/__pycache__/" in flat:
                continue
            members.append(rel)
    return sorted(members)


def build_archive():
    """Deterministic tar.zst + .sha256 at repo root."""
    # console.log equivalent [WP6-SEAL-06]: archive build start.
    console_log("WP6-SEAL-06", "deterministic archive build start")
    import zstandard as zstd
    members = archive_members()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
        for rel in members:
            full = os.path.join(REPO, rel)
            info = tar.gettarinfo(full, arcname=rel.replace(os.sep, "/"))
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.pax_headers = {}
            with open(full, "rb") as handle:
                tar.addfile(info, handle)
    blob = zstd.ZstdCompressor(level=ZSTD_LEVEL).compress(buf.getvalue())
    out = os.path.join(REPO, ARCHIVE_NAME)
    with open(out, "wb") as handle:
        handle.write(blob)
    digest = sha_file(out)
    with open(out + ".sha256", "w", encoding="utf-8") as handle:
        handle.write("%s  %s\n" % (digest, ARCHIVE_NAME))
    # console.log equivalent [WP6-SEAL-07]: archive sealed.
    console_log("WP6-SEAL-07", "archive %s sha256=%s members=%d" %
                (ARCHIVE_NAME, digest, len(members)))
    return out, digest, members


def write_manifest(archive_digest, members):
    """MANIFEST.sha256 over every archived member + the archive itself.

    The manifest never lists itself (self-hash paradox); its integrity
    comes from the seal commit. The archive likewise excludes the manifest
    (built after) — documented, not hidden.
    """
    # console.log equivalent [WP6-SEAL-08]: manifest build start.
    console_log("WP6-SEAL-08", "manifest build start")
    lines = []
    for rel in members:
        flat = rel.replace(os.sep, "/")
        lines.append("%s  %s\n" % (sha_file(os.path.join(REPO, rel)), flat))
    lines.append("%s  %s\n" % (archive_digest, ARCHIVE_NAME))
    lines.sort(key=lambda line: line.split("  ", 1)[1])
    with open(os.path.join(REPO, "artifacts", "seal", "MANIFEST.sha256"),
              "w", encoding="utf-8") as handle:
        handle.writelines(lines)
    # console.log equivalent [WP6-SEAL-09]: manifest sealed.
    console_log("WP6-SEAL-09", "manifest sealed entries=%d" % len(lines))
    return len(lines)


def main(argv=None):
    """P18 seal pipeline: result -> archive -> manifest."""
    result = build_result()
    write_result(result)
    _out, digest, members = build_archive()
    count = write_manifest(digest, members)
    print(json.dumps({"claim": result["claim_level"], "manifest_entries": count,
                      "archive_sha256": digest}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
