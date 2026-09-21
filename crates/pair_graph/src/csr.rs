//! Compact CSR adjacency over reachable_index (Tier B/C materialization).

/// CSR edge list: offsets[i]..offsets[i+1] address targets/keys/modes of
/// reachable state i. Targets stored as reachable_index (dense).
#[derive(Clone, Debug)]
pub struct Csr {
    pub offsets: Vec<usize>,
    pub targets: Vec<usize>,
    pub modes: Vec<u8>,
    pub keys: Vec<u32>,
}

impl Csr {
    pub fn out_degree(&self, idx: usize) -> usize {
        self.offsets[idx + 1] - self.offsets[idx]
    }
}
