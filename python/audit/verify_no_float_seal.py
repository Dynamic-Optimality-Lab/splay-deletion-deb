"""No-float seal scanner: exact artifact fields must contain no floats.

Walks sealed JSON artifacts (certificates, witnesses, candidate exact
fields, summaries, potentials) and rejects any float instance at an exact
path. Labeled discovery-only display fields (discovery_float) are exempt by
name. Exit 0 iff the seal is float-free. Step-logged.
"""

import argparse
import json
import os
import sys

EXEMPT_KEYS = {"discovery_float"}


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def scan(obj, path, hits):
    """Collect paths holding float instances (outside exempt keys)."""
    if isinstance(obj, float):
        hits.append(path)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in EXEMPT_KEYS:
                continue
            scan(v, "%s.%s" % (path, k), hits)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            scan(v, "%s[%d]" % (path, i), hits)


def main(argv=None):
    """Scan sealed artifacts for floats."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    # console.log equivalent [WP2-AUD-F-01]: seal scan begin.
    console_log("WP2-AUD-F-01", "scanning %d dirs" % len(args.dirs))
    hits = []
    files = 0
    for d in args.dirs:
        for root, _, names in os.walk(d):
            for name in names:
                if not name.endswith(".json"):
                    continue
                files += 1
                with open(os.path.join(root, name), encoding="utf-8") as f:
                    scan(json.load(f), "%s/%s" % (root, name), hits)
    verdict = "PASS" if not hits else "FAIL"
    # console.log equivalent [WP2-AUD-F-02]: verdict.
    console_log("WP2-AUD-F-02", "seal scan %s files=%d hits=%d" % (verdict, files, len(hits)))
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "verify_no_float_seal.json"), "w", encoding="utf-8") as f:
        json.dump({"files": files, "hits": hits[:20], "verdict": verdict},
                  f, sort_keys=True, indent=2)
        f.write("\n")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
