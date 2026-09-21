//! Directed edges: (source_state_id, mode, key), KEEP (0) before DELETE (1),
//! keys ascending. Target and costs are deterministic functions of the key.

use crate::state::PairId;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Mode {
    Keep = 0,
    Delete = 1,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct EdgeKey {
    pub source: PairId,
    pub mode: Mode,
    pub key: u32,
}

impl EdgeKey {
    /// Frozen deterministic order: (mode, key) with KEEP first.
    pub fn order_rank(&self) -> (u8, u32) {
        (self.mode as u8, self.key)
    }
}

/// One transition step. a = full-sequence cost, y = subsequence cost
/// (0 on DELETE). target computed from single-tree tables by the caller.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Edge {
    pub key: EdgeKey,
    pub target: PairId,
    pub a: u32,
    pub y: u32,
}

impl Edge {
    /// Integer-scaled slack L_{p,q}(e) = p*a - q*y with overflow detection.
    pub fn scaled_slack(&self, p: i128, q: i128) -> Option<i128> {
        p.checked_mul(self.a as i128)?.checked_sub(q.checked_mul(self.y as i128)?)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn keep_orders_before_delete() {
        let k = EdgeKey { source: PairId(0), mode: Mode::Keep, key: 2 };
        let d = EdgeKey { source: PairId(0), mode: Mode::Delete, key: 1 };
        assert!(k.order_rank() < d.order_rank());
    }
}
