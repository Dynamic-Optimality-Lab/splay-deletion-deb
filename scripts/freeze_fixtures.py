"""Freeze the full oracle fixture file from hand entries + triple agreement.

Reads python/reference/fixtures_hand.json, then extends it with every n=3
(T, x) case not already covered, but ONLY after the three independent
implementations agree exactly on it. Output: python/reference/fixtures.json.
Deterministic: entries sorted by (n, before, key). Step-logged.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from python.audit import independent_splay, independent_tree  # noqa: E402
from python.reference import enumerate as enum  # noqa: E402
from python.reference import functional_splay as func  # noqa: E402
from python.reference import splay as ref_splay  # noqa: E402
from python.reference import tree as ref_tree  # noqa: E402


def console_log(step_id, msg):
    """console.log equivalent: identified console output for every step.

    Python has no console.log primitive; print() to stdout is the faithful
    equivalent. Each emission carries a step ID for Path.md traceability.
    """
    print("[%s] %s" % (step_id, msg), flush=True)


def _shape_of_keyed(t):
    if t == ():
        return "."
    return "(" + _shape_of_keyed(t[0]) + _shape_of_keyed(t[2]) + ")"


def main():
    refdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python", "reference")
    with open(os.path.join(refdir, "fixtures_hand.json"), encoding="utf-8") as f:
        hand = json.load(f)
    entries = list(hand["entries"])
    covered = set((e["n"], e["before"], e["key"]) for e in entries)
    # console.log equivalent [WP1-FIX-01]: hand fixtures loaded.
    console_log("WP1-FIX-01", "hand entries=%d" % len(entries))
    nxt = 11
    for shape in enum.canonical_shapes(3):
        t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shape))
        iroot = independent_tree.build_tree(independent_tree.parse_shape(shape))
        fstate = func.from_keyed_tree(t)
        for x in (1, 2, 3):
            if (3, shape, x) in covered:
                continue
            t2, cost, cases, path0 = ref_splay.splay(t, x)
            i2, icost, icases = independent_splay.splay(iroot, x)
            f2, fcost, fcases = func.splay(fstate, x, 3)
            after = _shape_of_keyed(t2)
            if not (cost == icost == fcost and cases == icases == fcases
                    and independent_tree.shape_of(i2) == after):
                raise AssertionError("triple disagreement on %r x=%d" % (shape, x))
            entries.append({"after": after, "before": shape, "cases": cases,
                            "cost": cost, "depth": len(path0) - 1,
                            "id": "F-%03d" % nxt, "key": x, "n": 3,
                            "provenance": "triple-agreement-v0.1.0"})
            nxt += 1
    entries.sort(key=lambda e: (e["n"], e["before"], e["key"]))
    out = {"entries": entries, "version": "fixtures-v0.1"}
    with open(os.path.join(refdir, "fixtures.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, sort_keys=True, indent=2)
        f.write("\n")
    # console.log equivalent [WP1-FIX-02]: fixture file frozen.
    console_log("WP1-FIX-02", "frozen entries=%d" % len(entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
