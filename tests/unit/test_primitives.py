"""Unit tests for WP-1 primitives (stdlib unittest, no third-party deps).

Covers error paths and conventions the exhaustive gates assume:
malformed shapes, absent keys, childless rotations, cost bounds, and
post-splay root/validity on small trees. Run: python tests/unit/test_primitives.py
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


class TestShapes(unittest.TestCase):
    """Canonical shape grammar unit tests."""

    def test_rejects_malformed(self):
        """Malformed shape strings raise ValueError."""
        for bad in ("(()", "(..)..", "", "(.)", "((..))"):
            with self.assertRaises(ValueError):
                ref_tree.parse_shape(bad)

    def test_round_trip_spot(self):
        """Parse/serialize round-trips on representative codes."""
        for code in ("(..)", "((..).)", "(.(..))", "((..)(..))"):
            self.assertEqual(ref_tree.serialize_shape(ref_tree.parse_shape(code)), code)

    def test_independent_rejects_malformed(self):
        """Independent parser rejects malformed input independently."""
        with self.assertRaises(ValueError):
            independent_tree.parse_shape("(()")


class TestCosts(unittest.TestCase):
    """Depth/cost convention unit tests (M01/M02 at unit level)."""

    def test_root_depth_zero_cost_one(self):
        """Root depth is 0 and root access costs 1."""
        t = ref_tree.assign_inorder_keys(ref_tree.parse_shape("((..)(..))"))
        self.assertEqual(ref_tree.compute_depth(t, 2), 0)
        self.assertEqual(ref_tree.access_cost(t, 2), 1)

    def test_cost_bounds_small(self):
        """1 <= cost <= n for every (T, x) with n<=4."""
        for n in range(1, 5):
            for shape in enum.canonical_shapes(n):
                t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shape))
                for x in range(1, n + 1):
                    c = ref_tree.access_cost(t, x)
                    self.assertGreaterEqual(c, 1)
                    self.assertLessEqual(c, n)

    def test_absent_key_raises(self):
        """Absent keys raise KeyError in both implementations."""
        t = ref_tree.assign_inorder_keys(ref_tree.parse_shape("(..)"))
        with self.assertRaises(KeyError):
            ref_tree.find_path(t, 9)
        r = independent_tree.build_tree(independent_tree.parse_shape("(..)"))
        with self.assertRaises(KeyError):
            independent_tree.locate(r, 9)


class TestRotations(unittest.TestCase):
    """Rotation error-path and post-condition unit tests."""

    def test_childless_rotation_raises(self):
        """Rotations without the required child raise ValueError."""
        t = ref_tree.assign_inorder_keys(ref_tree.parse_shape("(..)"))
        with self.assertRaises(ValueError):
            ref_splay.rotate_right(t, 1)
        with self.assertRaises(ValueError):
            ref_splay.rotate_left(t, 1)

    def test_splay_postconditions_small(self):
        """After splay: x is root and the BST is valid (n<=3, all cases)."""
        for shape in enum.canonical_shapes(3):
            n = 3
            t = ref_tree.assign_inorder_keys(ref_tree.parse_shape(shape))
            for x in (1, 2, 3):
                t2, _, _, _ = ref_splay.splay(t, x)
                self.assertEqual(ref_tree.find_path(t2, x), [x])
                self.assertTrue(ref_tree.validate_bst(t2, n))
                r = independent_tree.build_tree(independent_tree.parse_shape(shape))
                r2, _, _ = independent_splay.splay(r, x)
                self.assertTrue(independent_tree.validate_bst(r2, n))
                st = func.from_keyed_tree(t)
                st2, _, _ = func.splay(st, x, n)
                self.assertEqual(st2[3], x)


if __name__ == "__main__":
    unittest.main()
