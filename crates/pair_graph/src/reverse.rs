//! Reverse-edge generation from inverse single-tree tables (for V).
//! DELETE predecessor of (A2,B) under x: {(A,B) : A in pred[x][A2]}.
//! KEEP predecessor of (A2,B2): cross product of both pred lists.
//! Every generated predecessor is filtered by R_n membership by the caller.

/// pred[x][after] = sorted before-tree ids (column/key x 1-based).
pub struct InverseTables {
    pub n: u32,
    pub pred: Vec<Vec<Vec<u64>>>,
}

impl InverseTables {
    /// Conservation check: sum over after of len(pred[x][after]) == C_n.
    pub fn conservation_holds(&self, tree_count: u64) -> bool {
        (1..=self.n as usize).all(|x| {
            self.pred[x].iter().map(|v| v.len() as u64).sum::<u64>() == tree_count
        })
    }
}
