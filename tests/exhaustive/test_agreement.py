"""Exhaustive agreement tests (stdlib unittest, no third-party deps).

Triple agreement (reference vs independent vs functional) on all (T, x)
with n<=3, plus reference-vs-independent on n=4. The wider n<=5/n<=6
sweeps live in the gate runner (tests/test_wp1.py) and the stress script
(scripts/stress_wp1.py). Run: python tests/exhaustive/test_agreement.py
"""

import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

from python.audit import independent_splay, independent_tree
from python.reference import enumerate as enum
from python.reference import functional_splay as func
from python.reference import splay as ref_splay
from python.reference import tree as ref_tree


def keyed_shape(t):
    """Erase labels from a reference keyed tree."""
    if t == ():
        return "."
    return "(" + keyed_shape(t[0]) + keyed_shape(t[2]) + ")"


class TestAgreement(unittest.TestCase):
    """Cross-implementation agreement unit tests."""

    def test_triple_n3(self):
        """All three implementations agree on every (T, x), n<=3."""
        for n in (1, 2, 3):
            for shape in enum.canonical_shapes(n):
                t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shape))
                r = independent_tree.build_tree(independent_tree.parse_shape(shape))
                st = func.from_keyed_tree(t)
                for x in range(1, n + 1):
                    t2, cost, cases, _ = ref_splay.splay(t, x)
                    r2, icost, icases = independent_splay.splay(r, x)
                    _, fcost, fcases = func.splay(st, x, n)
                    self.assertEqual((keyed_shape(t2), cost, cases),
                                     (independent_tree.shape_of(r2), icost, icases))
                    self.assertEqual((cost, cases), (fcost, fcases))

    def test_pair_n4(self):
        """Reference and independent auditor agree on every (T, x), n=4."""
        for shape in enum.canonical_shapes(4):
            t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shape))
            r = independent_tree.build_tree(independent_tree.parse_shape(shape))
            for x in range(1, 5):
                t2, cost, cases, _ = ref_splay.splay(t, x)
                r2, icost, icases = independent_splay.splay(r, x)
                self.assertEqual((keyed_shape(t2), cost, cases),
                                 (independent_tree.shape_of(r2), icost, icases))


if __name__ == "__main__":
    unittest.main()
