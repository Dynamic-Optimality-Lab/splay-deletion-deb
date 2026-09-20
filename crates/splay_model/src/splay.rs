//! Bottom-up Splay: exactly ZIG / LL / RR / LR / RL (frozen spec Sec. 4).

use crate::rotate::{child_side, rotate_left, rotate_right};
use crate::tree::{Tree, TreeError};

#[derive(Clone, PartialEq, Eq, Debug)]
pub struct SplayOutcome {
    pub cost: usize,
    pub cases: Vec<&'static str>,
    pub access_path: Vec<u32>,
}

/// Splay key x to the root. Returns pre-splay cost, rotation cases, and the
/// pre-splay access path. Post-conditions: x is root, tree checks clean.
pub fn splay(t: &mut Tree, x: u32) -> Result<SplayOutcome, TreeError> {
    let target = t.index_of(x).ok_or(TreeError::KeyAbsent(x))?;
    let _ = target;
    let path: Vec<u32> = {
        let mut v = t.index_of(x).unwrap();
        let mut rev = vec![t.nodes[v].key];
        while let Some(p) = t.nodes[v].parent {
            v = p;
            rev.push(t.nodes[v].key);
        }
        rev.reverse();
        rev
    };
    let cost = path.len();
    let mut cases = Vec::new();
    loop {
        let vi = t.index_of(x).unwrap();
        let pi = match t.nodes[vi].parent {
            None => break,
            Some(p) => p,
        };
        let v_left = child_side(t, vi)?.unwrap_or(true);
        match t.nodes[pi].parent {
            None => {
                if v_left {
                    rotate_right(t, pi)?;
                } else {
                    rotate_left(t, pi)?;
                }
                cases.push("ZIG");
            }
            Some(gi) => {
                let p_left = child_side(t, pi)?.unwrap_or(true);
                match (v_left, p_left) {
                    (true, true) => {
                        rotate_right(t, gi)?;
                        rotate_right(t, pi)?;
                        cases.push("LL");
                    }
                    (false, false) => {
                        rotate_left(t, gi)?;
                        rotate_left(t, pi)?;
                        cases.push("RR");
                    }
                    (false, true) => {
                        rotate_left(t, pi)?;
                        rotate_right(t, gi)?;
                        cases.push("LR");
                    }
                    (true, false) => {
                        rotate_right(t, pi)?;
                        rotate_left(t, gi)?;
                        cases.push("RL");
                    }
                }
            }
        }
    }
    t.check()?;
    let root_key = t.nodes[t.root.unwrap()].key;
    if root_key != x {
        return Err(TreeError::Invariant("x not root after splay".to_string()));
    }
    Ok(SplayOutcome { cost, cases, access_path: path })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::encode::parse_shape;
    use crate::tree::Tree;

    fn shape_of(t: &Tree) -> String {
        fn go(t: &Tree, idx: Option<usize>) -> String {
            match idx {
                None => ".".to_string(),
                Some(i) => format!("({}{})", go(t, t.nodes[i].left), go(t, t.nodes[i].right)),
            }
        }
        go(t, t.root)
    }

    #[test]
    fn zigzig_left_chain_matches_fixture() {
        let mut t = Tree::from_shape(&parse_shape("(((..).).)").unwrap());
        let out = splay(&mut t, 1).unwrap();
        assert_eq!(out.cost, 3);
        assert_eq!(out.cases, vec!["LL", "ZIG"]);
        assert_eq!(shape_of(&t), "(.(.(..)))");
    }

    #[test]
    fn zigzag_left_right_matches_fixture() {
        let mut t = Tree::from_shape(&parse_shape("((.(..)).)").unwrap());
        let out = splay(&mut t, 2).unwrap();
        assert_eq!(out.cost, 3);
        assert_eq!(out.cases, vec!["LR"]);
        assert_eq!(shape_of(&t), "((..)(..))");
    }

    #[test]
    fn root_access_is_identity() {
        let mut t = Tree::from_shape(&parse_shape("((..)(..))").unwrap());
        let out = splay(&mut t, 2).unwrap();
        assert_eq!(out.cost, 1);
        assert!(out.cases.is_empty());
        assert_eq!(shape_of(&t), "((..)(..))");
    }
}
