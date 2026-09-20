//! Exact BST-shape enumeration with Catalan verification.
//! Generation order is NOT canonical; callers must sort codes for tree_id.

use crate::encode::{serialize_shape, Shape};

/// Exact Catalan number by multiplicative integer arithmetic (u128).
pub fn catalan(n: u32) -> u128 {
    let mut result: u128 = 1;
    for k in 1..=n as u128 {
        result = result * (n as u128 + k) / k;
    }
    result / (n as u128 + 1)
}

pub fn gen_skeletons(n: u32) -> Vec<Shape> {
    if n == 0 {
        return vec![Shape::Empty];
    }
    let mut out = Vec::new();
    for l in 0..n {
        let r = n - 1 - l;
        for left in gen_skeletons(l) {
            for right in gen_skeletons(r) {
                out.push(Shape::Node(Box::new(left.clone()), Box::new(right.clone())));
            }
        }
    }
    out
}

/// Canonical shape codes sorted lexicographically; index is tree_id.
pub fn canonical_shapes(n: u32) -> Vec<String> {
    let mut codes: Vec<String> = gen_skeletons(n).iter().map(serialize_shape).collect();
    codes.sort();
    codes
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn catalan_values() {
        for (n, c) in [(1, 1), (2, 2), (3, 5), (4, 14), (5, 42), (6, 132), (7, 429), (8, 1430)] {
            assert_eq!(catalan(n), c, "C_{n}");
            assert_eq!(canonical_shapes(n).len() as u128, c, "emitted {n}");
        }
    }

    #[test]
    fn canonical_ids_stable() {
        let shapes = canonical_shapes(3);
        assert_eq!(shapes[0], "(((..).).)");
        assert!(shapes.windows(2).all(|w| w[0] < w[1]));
    }
}
