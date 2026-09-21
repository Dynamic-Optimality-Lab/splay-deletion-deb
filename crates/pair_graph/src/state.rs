//! Pair identifiers and the reachable set R_n.
//! pair_id = A_id * C_n + B_id (stable, incl. unreachable pairs).
//! reachable_index = position in ascending sort of reachable pair_ids.

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Debug)]
pub struct PairId(pub u64);

impl PairId {
    pub fn new(a_id: u64, b_id: u64, tree_count: u64) -> PairId {
        PairId(a_id * tree_count + b_id)
    }

    pub fn split(self, tree_count: u64) -> (u64, u64) {
        (self.0 / tree_count, self.0 % tree_count)
    }
}

#[derive(Clone, Debug)]
pub struct Reachability {
    pub n: u32,
    pub tree_count: u64,
    /// Ascending sorted reachable pair ids; position is reachable_index.
    pub pairs: Vec<PairId>,
}

impl Reachability {
    pub fn contains(&self, id: PairId) -> bool {
        self.pairs.binary_search(&id).is_ok()
    }

    pub fn index_of(&self, id: PairId) -> Option<usize> {
        self.pairs.binary_search(&id).ok()
    }

    pub fn count(&self) -> usize {
        self.pairs.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pair_id_round_trip() {
        let id = PairId::new(3, 7, 42);
        assert_eq!(id.split(42), (3, 7));
    }
}
