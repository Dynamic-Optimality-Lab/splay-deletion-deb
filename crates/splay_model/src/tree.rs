//! Pointer-index BST with inorder-rank labels 1..=n.

use crate::encode::Shape;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Node {
    pub key: u32,
    pub parent: Option<usize>,
    pub left: Option<usize>,
    pub right: Option<usize>,
}

#[derive(Clone, Debug)]
pub struct Tree {
    pub nodes: Vec<Node>,
    pub root: Option<usize>,
}

#[derive(Debug, PartialEq, Eq)]
pub enum TreeError {
    KeyAbsent(u32),
    Invariant(String),
}

impl Tree {
    /// Build a labeled tree from a skeleton, assigning inorder rank 1..=n.
    pub fn from_shape(skel: &Shape) -> Tree {
        let mut tree = Tree { nodes: Vec::new(), root: None };
        let mut next_key = 1u32;
        tree.root = build_into(&mut tree.nodes, skel, None, &mut next_key);
        tree
    }

    pub fn size(&self) -> usize {
        self.nodes.len()
    }

    pub fn n_keys(&self) -> u32 {
        self.nodes.len() as u32
    }

    pub fn index_of(&self, key: u32) -> Option<usize> {
        self.nodes.iter().position(|nd| nd.key == key)
    }

    /// Root-to-key index path. None if absent.
    pub fn find_path(&self, key: u32) -> Option<Vec<usize>> {
        let mut path = Vec::new();
        let mut cur = self.root?;
        loop {
            path.push(cur);
            let k = self.nodes[cur].key;
            if key == k {
                return Some(path);
            }
            cur = if key < k { self.nodes[cur].left? } else { self.nodes[cur].right? };
        }
    }

    /// Depth in edges (root depth 0). Frozen cost is depth + 1.
    pub fn depth(&self, key: u32) -> Result<usize, TreeError> {
        self.find_path(key)
            .map(|p| p.len() - 1)
            .ok_or(TreeError::KeyAbsent(key))
    }

    pub fn cost(&self, key: u32) -> Result<usize, TreeError> {
        Ok(self.depth(key)? + 1)
    }

    pub fn inorder_keys(&self) -> Vec<u32> {
        let mut out = Vec::new();
        fn go(t: &Tree, idx: Option<usize>, out: &mut Vec<u32>) {
            if let Some(i) = idx {
                go(t, t.nodes[i].left, out);
                out.push(t.nodes[i].key);
                go(t, t.nodes[i].right, out);
            }
        }
        go(self, self.root, &mut out);
        out
    }

    /// Full invariant check: mutual links, acyclicity, count, inorder 1..=n.
    pub fn check(&self) -> Result<(), TreeError> {
        let n = self.nodes.len();
        let mut seen = vec![false; n];
        let mut order = Vec::new();
        fn go(t: &Tree, idx: Option<usize>, seen: &mut [bool], order: &mut Vec<u32>) -> Result<(), TreeError> {
            if let Some(i) = idx {
                if seen[i] {
                    return Err(TreeError::Invariant("cycle".to_string()));
                }
                seen[i] = true;
                let nd = &t.nodes[i];
                if let Some(l) = nd.left {
                    if t.nodes[l].parent != Some(i) {
                        return Err(TreeError::Invariant("left link".to_string()));
                    }
                }
                if let Some(r) = nd.right {
                    if t.nodes[r].parent != Some(i) {
                        return Err(TreeError::Invariant("right link".to_string()));
                    }
                }
                go(t, nd.left, seen, order)?;
                order.push(nd.key);
                go(t, nd.right, seen, order)?;
            }
            Ok(())
        }
        go(self, self.root, &mut seen, &mut order)?;
        if seen.iter().any(|s| !s) {
            return Err(TreeError::Invariant("unreachable node".to_string()));
        }
        let expect: Vec<u32> = (1..=n as u32).collect();
        if order != expect {
            return Err(TreeError::Invariant("inorder".to_string()));
        }
        Ok(())
    }
}

fn build_into(nodes: &mut Vec<Node>, skel: &Shape, parent: Option<usize>, next_key: &mut u32) -> Option<usize> {
    match skel {
        Shape::Empty => None,
        Shape::Node(l, r) => {
            let left = build_into(nodes, l, None, next_key);
            let idx = nodes.len();
            nodes.push(Node { key: 0, parent, left: None, right: None });
            let key = *next_key;
            *next_key += 1;
            nodes[idx].key = key;
            let right = build_into(nodes, r, None, next_key);
            nodes[idx].left = left;
            nodes[idx].right = right;
            if let Some(l) = left {
                nodes[l].parent = Some(idx);
            }
            if let Some(r) = right {
                nodes[r].parent = Some(idx);
            }
            Some(idx)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::encode::parse_shape;

    #[test]
    fn labels_and_inorder() {
        let t = Tree::from_shape(&parse_shape("((..)(..))").unwrap());
        assert_eq!(t.inorder_keys(), vec![1, 2, 3]);
        t.check().unwrap();
    }

    #[test]
    fn depth_cost_convention() {
        let t = Tree::from_shape(&parse_shape("(((..).).)").unwrap());
        assert_eq!(t.depth(1).unwrap(), 2);
        assert_eq!(t.cost(1).unwrap(), 3);
        assert_eq!(t.cost(3).unwrap(), 1);
    }
}
