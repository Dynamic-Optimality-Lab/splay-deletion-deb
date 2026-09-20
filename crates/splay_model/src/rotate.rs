//! Single rotations with immediate consistency assertions.
//! No recursion in the rotation core: explicit parent/grandparent temporaries.

use crate::tree::{Tree, TreeError};

fn attach(t: &mut Tree, parent: Option<usize>, side_left: bool, child: Option<usize>) {
    if let Some(p) = parent {
        if side_left {
            t.nodes[p].left = child;
        } else {
            t.nodes[p].right = child;
        }
    } else {
        t.root = child;
    }
    if let Some(c) = child {
        t.nodes[c].parent = parent;
    }
}

fn is_left(t: &Tree, idx: usize) -> Result<bool, TreeError> {
    match t.nodes[idx].parent {
        None => Err(TreeError::Invariant("root has no side".to_string())),
        Some(p) => {
            if t.nodes[p].left == Some(idx) {
                Ok(true)
            } else if t.nodes[p].right == Some(idx) {
                Ok(false)
            } else {
                Err(TreeError::Invariant("parent/child mismatch".to_string()))
            }
        }
    }
}

/// Right rotation at node p. Requires a left child.
pub fn rotate_right(t: &mut Tree, p: usize) -> Result<(), TreeError> {
    let q = t.nodes[p].left.ok_or_else(|| TreeError::Invariant("no left child".to_string()))?;
    let beta = t.nodes[q].right;
    let gp = t.nodes[p].parent;
    let gp_side_left = gp.map(|g| t.nodes[g].left == Some(p)).unwrap_or(true);
    t.nodes[q].right = Some(p);
    t.nodes[p].parent = Some(q);
    t.nodes[p].left = beta;
    if let Some(b) = beta {
        t.nodes[b].parent = Some(p);
    }
    attach(t, gp, gp_side_left, Some(q));
    debug_assert!(t.check().is_ok());
    Ok(())
}

/// Left rotation at node p. Requires a right child.
pub fn rotate_left(t: &mut Tree, p: usize) -> Result<(), TreeError> {
    let q = t.nodes[p].right.ok_or_else(|| TreeError::Invariant("no right child".to_string()))?;
    let beta = t.nodes[q].left;
    let gp = t.nodes[p].parent;
    let gp_side_left = gp.map(|g| t.nodes[g].left == Some(p)).unwrap_or(true);
    t.nodes[q].left = Some(p);
    t.nodes[p].parent = Some(q);
    t.nodes[p].right = beta;
    if let Some(b) = beta {
        t.nodes[b].parent = Some(p);
    }
    attach(t, gp, gp_side_left, Some(q));
    debug_assert!(t.check().is_ok());
    Ok(())
}

pub fn child_side(t: &Tree, idx: usize) -> Result<Option<bool>, TreeError> {
    match t.nodes[idx].parent {
        None => Ok(None),
        Some(_) => Ok(Some(is_left(t, idx)?)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::encode::parse_shape;

    #[test]
    fn zig_changes_root() {
        let mut t = Tree::from_shape(&parse_shape("((..).)").unwrap());
        let p = t.root.unwrap();
        rotate_right(&mut t, p).unwrap();
        assert_eq!(t.nodes[t.root.unwrap()].key, 1);
        t.check().unwrap();
    }
}
