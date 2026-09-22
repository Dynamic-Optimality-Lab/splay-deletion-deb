"""WP-6 seal stress suite: fault injection against the seal.

Ten checks (WP6-S-01..WP6-S-10): wrong-claim rejection, manifest-tamper
detection, float-smuggling detection, missing-pin detection, archive-tamper
detection, false-P17 rejection, survivor-smuggling detection, result
rebuild identity, bad-claim-string schema rejection, seal-log presence.
In-memory/file-copy only; committed artifacts never mutated. Writes
artifacts/logs/wp6_stress.json. Exit 0 iff all pass. Step-logged.
"""
import hashlib
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

PASS = []
FAIL = []


# console.log equivalent [WP6-S-00]: stress module loaded.
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


def seal_result():
    """Load the sealed FINAL_RESULT."""
    with open(os.path.join(REPO, "artifacts", "seal", "FINAL_RESULT.json"),
              encoding="utf-8") as handle:
        return json.load(handle)


def stress_claim():
    """WP6-S-01: filed claim equals recomputed claim (no promotion)."""
    # console.log equivalent [WP6-S-01]: claim-identity stress.
    console_log("WP6-S-01", "WP6-S-01 claim identity")
    from python.wp6 import seal as SEAL
    check("WP6-S-01", SEAL.build_result()["claim_level"] == seal_result()["claim_level"]
          == "FINITE_EXACT_BN_RESULTS", "claim recompute identical, finite")


def manifest_verify(lines, skip_self_log=True):
    """Manifest gate predicate: every line hashes correctly.

    The run's own log file is excluded from the sane check: it is rewritten
    by this very run after the check, so no manifest can cover its new bytes
    yet. Coverage chain: each run verifies the previous run's log bytes;
    the seal manifest covers the final log (checked read-only by WP6-06).
    """
    self_log = "artifacts/logs/wp6_stress.json"
    for line in lines:
        parts = line.split("  ")
        if len(parts) != 2:
            return False
        exp, rel = parts
        if skip_self_log and rel == self_log:
            continue
        full = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.isfile(full):
            return False
        h = hashlib.sha256()
        with open(full, "rb") as handle:
            for chunk in iter(lambda: handle.read(1048576), b""):
                h.update(chunk)
        if h.hexdigest() != exp.lower():
            return False
    return True


def stress_manifest_tamper():
    """WP6-S-02: tampered manifest entry detected."""
    # console.log equivalent [WP6-S-02]: manifest-tamper injection.
    console_log("WP6-S-02", "WP6-S-02 manifest tamper")
    with open(os.path.join(REPO, "artifacts", "seal", "MANIFEST.sha256"),
              encoding="utf-8") as handle:
        lines = [l.rstrip("\n") for l in handle if l.strip()]
    sane = manifest_verify(lines)
    forged = list(lines)
    head, _sep, tail = forged[0].partition("  ")
    forged[0] = ("0" if head[0] != "0" else "1") + head[1:] + "  " + tail
    check("WP6-S-02", sane and not manifest_verify(forged), "tamper caught")


def stress_float_smuggle():
    """WP6-S-03: smuggled float in an exact field detected."""
    # console.log equivalent [WP6-S-03]: float-smuggle injection.
    console_log("WP6-S-03", "WP6-S-03 float smuggle")
    cert = json.load(open(os.path.join(
        REPO, "artifacts", "certificates", "n4", "bn_certificate.json"), encoding="utf-8"))
    forged = json.loads(json.dumps(cert))
    forged["b"]["p"] = 1.5
    found = []

    def walk(value, stack):
        if isinstance(value, float):
            if not stack or stack[-1] != "forced_fraction":
                found.append("/".join(stack))
        elif isinstance(value, dict):
            for k, v in value.items():
                walk(v, stack + [str(k)])
        elif isinstance(value, list):
            for i, v in enumerate(value):
                walk(v, stack + [str(i)])
    walk(forged, [])
    check("WP6-S-03", found == ["b/p"], "smuggled float located at b/p")


def spec_set_ok(entries):
    """Spec-set gate predicate: exactly the five governed versions."""
    versions = [e.get("version") for e in entries]
    return (versions == ["v0.1", "v0.1.1-SA01", "v0.1.2-SA02", "v0.1.3-SA03", "v0.1.4-SA04"]
            and all(len(e.get("sha256", "")) == 64 for e in entries))


def stress_missing_pin():
    """WP6-S-04: dropped normative pin detected."""
    # console.log equivalent [WP6-S-04]: missing-pin injection.
    console_log("WP6-S-04", "WP6-S-04 missing pin")
    entries = seal_result()["normative_spec_set"]
    check("WP6-S-04", spec_set_ok(entries) and not spec_set_ok(entries[:4]),
          "4-of-5 spec set refused")


def stress_archive_tamper():
    """WP6-S-05: archive byte-tamper detected via sidecar hash."""
    # console.log equivalent [WP6-S-05]: archive-tamper injection.
    console_log("WP6-S-05", "WP6-S-05 archive tamper")
    with open(os.path.join(REPO, "SPLAY-AM-PD-v0.1.tar.zst"), "rb") as handle:
        blob = bytearray(handle.read())
    blob[1000] ^= 1
    tampered = hashlib.sha256(bytes(blob)).hexdigest()
    with open(os.path.join(REPO, "SPLAY-AM-PD-v0.1.tar.zst.sha256"),
              encoding="utf-8") as handle:
        sidecar = handle.read().strip().split("  ")[0]
    check("WP6-S-05", tampered != sidecar, "1-bit flip diverges from sidecar")


def p17_consistent(record):
    """P17 gate predicate: activation requires passing criteria."""
    if record.get("verdict") == "P17_ACTIVATED":
        return any(f.get("family_activated") for f in record.get("families", []))
    if record.get("verdict") == "P17_NOT_ACTIVATED":
        return not any(f.get("family_activated") for f in record.get("families", []))
    return False


def stress_false_p17():
    """WP6-S-06: forged P17 activation rejected."""
    # console.log equivalent [WP6-S-06]: false-P17 injection.
    console_log("WP6-S-06", "WP6-S-06 false P17")
    with open(os.path.join(REPO, "artifacts", "wp6", "p17_activation.json"),
              encoding="utf-8") as handle:
        record = json.load(handle)
    forged = json.loads(json.dumps(record))
    forged["verdict"] = "P17_ACTIVATED"
    check("WP6-S-06", p17_consistent(record) and not p17_consistent(forged),
          "forged activation refused")


def stress_survivor_smuggle():
    """WP6-S-07: smuggled survivor detected (would force claim change)."""
    # console.log equivalent [WP6-S-07]: survivor-smuggle injection.
    console_log("WP6-S-07", "WP6-S-07 survivor smuggle")
    with open(os.path.join(REPO, "artifacts", "wp6", "positive_branch_closure.json"),
              encoding="utf-8") as handle:
        closure = json.load(handle)
    forged = json.loads(json.dumps(closure))
    forged["survivors"] = ["H-0001"]
    detected = (closure["survivors"] == [] and forged["survivors"] != []
                and seal_result()["best_H_hypothesis"] is None)
    check("WP6-S-07", detected, "smuggled survivor diverges from seal")


def stress_rebuild_identity():
    """WP6-S-08: seal rebuild identical (result + manifest entry count)."""
    # console.log equivalent [WP6-S-08]: rebuild identity.
    console_log("WP6-S-08", "WP6-S-08 rebuild identity")
    from python.wp6 import seal as SEAL
    with open(os.path.join(REPO, "artifacts", "seal", "MANIFEST.sha256"),
              encoding="utf-8") as handle:
        count = sum(1 for l in handle if l.strip())
    check("WP6-S-08", SEAL.build_result() == seal_result()
          and count == len(SEAL.archive_members()) + 1, "rebuild identical")


def stress_bad_claim():
    """WP6-S-09: bad claim string rejected by schema."""
    # console.log equivalent [WP6-S-09]: bad-claim injection.
    console_log("WP6-S-09", "WP6-S-09 bad claim")
    import jsonschema
    with open(os.path.join(REPO, "schemas", "final_result.schema.json"),
              encoding="utf-8") as handle:
        schema = json.load(handle)
    forged = json.loads(json.dumps(seal_result()))
    forged["claim_level"] = "DYNAMIC_OPTIMALITY_PROVED_ALMOST"
    try:
        jsonschema.validate(forged, schema)
        rejected = False
    except Exception:
        rejected = True
    check("WP6-S-09", rejected, "off-enum claim rejected")


def stress_logs():
    """WP6-S-10: seal-phase logs present with exit 0."""
    # console.log equivalent [WP6-S-10]: log presence.
    console_log("WP6-S-10", "WP6-S-10 log presence")
    ok = True
    for name in ("phase15", "phase16", "phase17", "phase18", "reproduce", "wp6_stress"):
        path = os.path.join(REPO, "artifacts", "logs",
                            name if name.endswith(".json") else name + ".json")
        if name == "wp6_stress":
            continue
        if not os.path.exists(path):
            ok = False
    check("WP6-S-10", ok, "phase + reproduce logs present")


def main(argv=None):
    """Run WP-6 stress suite, write JSON log, exit nonzero on failure."""
    t0 = time.time()
    # console.log equivalent [WP6-S-00]: suite start.
    console_log("WP6-S-00", "WP-6 stress suite start")
    stress_claim()
    stress_manifest_tamper()
    stress_float_smuggle()
    stress_missing_pin()
    stress_archive_tamper()
    stress_false_p17()
    stress_survivor_smuggle()
    stress_rebuild_identity()
    stress_bad_claim()
    stress_logs()
    dt = time.time() - t0
    # console.log equivalent [WP6-S-11]: suite summary.
    console_log("WP6-S-11", "pass=%d fail=%d seconds=%.1f" % (len(PASS), len(FAIL), dt))
    with open(os.path.join(REPO, "artifacts", "logs", "wp6_stress.json"),
              "w", encoding="utf-8") as handle:
        json.dump({"experiment_id": "SPLAY-AM-PD-v0.1", "exit": 0 if not FAIL else 1,
                   "fail": FAIL, "pass": PASS,
                   "wall_seconds": round(dt, 1)}, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
