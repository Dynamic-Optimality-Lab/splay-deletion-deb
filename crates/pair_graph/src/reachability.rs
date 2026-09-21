//! Multi-source BFS reachability from all diagonal states.
//! Successors are two single-tree table lookups per (pair, mode, key).
//! Discovery order is discarded for the external dense index: final
//! reachable_index follows ascending pair_id sort.

use crate::edge::Mode;
use crate::state::{PairId, Reachability};
use std::collections::{HashMap, VecDeque};

/// Single-tree transition tables for one n.
/// after[t][x] and cost[t][x] use tree_id rows and 1-based key columns
/// (column 0 unused).
pub struct SingleTables {
    pub n: u32,
    pub after: Vec<Vec<u64>>,
    pub cost: Vec<Vec<u32>>,
}

impl SingleTables {
    pub fn successor(&self, pair: PairId, tree_count: u64, mode: Mode, key: u32) -> (PairId, u32, u32) {
        let (a, b) = pair.split(tree_count);
        let a2 = self.after[a as usize][key as usize];
        let a_cost = self.cost[a as usize][key as usize];
        let (b2, y) = match mode {
            Mode::Keep => (self.after[b as usize][key as usize], self.cost[b as usize][key as usize]),
            Mode::Delete => (b, 0),
        };
        (PairId::new(a2, b2, tree_count), a_cost, y)
    }
}

/// BFS parent witness for every non-diagonal reachable state.
#[derive(Clone, Debug)]
pub struct ParentWitness {
    pub parent: PairId,
    pub mode: Mode,
    pub key: u32,
}

pub struct ReachabilityBuild {
    pub reach: Reachability,
    pub parents: HashMap<PairId, ParentWitness>,
}

/// Build R_n: seed all diagonals ascending, expand in frozen edge order.
pub fn build_reachable(n: u32, tree_count: u64, tables: &SingleTables) -> ReachabilityBuild {
    let mut seen: Vec<PairId> = Vec::new();
    let mut in_set = std::collections::HashSet::new();
    let mut parents = HashMap::new();
    let mut queue = VecDeque::new();
    for t in 0..tree_count {
        let d = PairId::new(t, t, tree_count);
        in_set.insert(d);
        seen.push(d);
        queue.push_back(d);
    }
    while let Some(pair) = queue.pop_front() {
        for mode in [Mode::Keep, Mode::Delete] {
            for key in 1..=n {
                let (target, _, _) = tables.successor(pair, tree_count, mode, key);
                if in_set.insert(target) {
                    seen.push(target);
                    queue.push_back(target);
                    parents.insert(target, ParentWitness { parent: pair, mode, key });
                }
            }
        }
    }
    seen.sort();
    let reach = Reachability { n, tree_count, pairs: seen };
    ReachabilityBuild { reach, parents }
}

/// Verify full forward closure: every one of the 2n outgoing edges of every
/// reachable state must land inside the reachable set.
pub fn verify_closure(build: &ReachabilityBuild, tables: &SingleTables) -> bool {
    for pair in &build.reach.pairs {
        for mode in [Mode::Keep, Mode::Delete] {
            for key in 1..=build.reach.n {
                let (target, _, _) = tables.successor(*pair, build.reach.tree_count, mode, key);
                if !build.reach.contains(target) {
                    return false;
                }
            }
        }
    }
    true
}
