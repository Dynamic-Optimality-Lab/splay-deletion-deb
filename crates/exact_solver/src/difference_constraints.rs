//! Queue-based Bellman-Ford (SPFA) over integer-scaled slacks with exact
//! negative-object extraction. Checked i128 only under a proved run bound;
//! otherwise returns CapacityFail (never wraps silently).

use pair_graph::edge::Mode;
use pair_graph::reachability::SingleTables;
use pair_graph::state::Reachability;

#[derive(Debug)]
pub enum SolveError {
    CapacityFail,
}

/// Edge weight closure: L(e) = p*a - q*y as i128 (caller bounds p, q, a, y).
pub type WeightFn = dyn Fn(u32, u32) -> Option<i128>;

pub struct Validity {
    /// Shortest diagonal-rooted slack per reachable_index (None = unreachable,
    /// impossible here since all states are diagonal-reachable by construction).
    pub dist: Vec<Option<i128>>,
    /// Tight-parent edge per index for witness reconstruction.
    pub parent: Vec<Option<(usize, Mode, u32)>>,
}

fn successors(
    tables: &SingleTables,
    reach: &Reachability,
    idx: usize,
    weight: &WeightFn,
) -> Vec<(usize, Mode, u32, i128)> {
    let pair = reach.pairs[idx];
    let mut out = Vec::new();
    for mode in [Mode::Keep, Mode::Delete] {
        for key in 1..=reach.n {
            let (target, a, y) = tables.successor(pair, reach.tree_count, mode, key);
            let j = reach.index_of(target).expect("forward closure");
            if let Some(w) = weight(a, y) {
                out.push((j, mode, key, w));
            }
        }
    }
    out
}

/// SPFA from all diagonals (dist 0). Returns shortest slacks plus, on
/// invalidity, classification data for witness extraction.
pub fn shortest_slacks(
    tables: &SingleTables,
    reach: &Reachability,
    weight: &WeightFn,
) -> Result<Validity, SolveError> {
    let n = reach.count();
    let mut dist: Vec<Option<i128>> = vec![None; n];
    let mut parent: Vec<Option<(usize, Mode, u32)>> = vec![None; n];
    let mut in_queue = vec![false; n];
    let mut relax_count = vec![0u64; n];
    let mut queue = std::collections::VecDeque::new();
    for (i, pair) in reach.pairs.iter().enumerate() {
        let (a, b) = pair.split(reach.tree_count);
        if a == b {
            dist[i] = Some(0);
            queue.push_back(i);
            in_queue[i] = true;
        }
    }
    while let Some(u) = queue.pop_front() {
        in_queue[u] = false;
        let du = dist[u].expect("queued vertex has finite dist");
        for (v, mode, key, w) in successors(tables, reach, u, weight) {
            let nd = du.checked_add(w).ok_or(SolveError::CapacityFail)?;
            let better = dist[v].map(|dv| nd < dv).unwrap_or(true);
            if better {
                dist[v] = Some(nd);
                parent[v] = Some((u, mode, key));
                relax_count[v] += 1;
                if relax_count[v] > n as u64 {
                    return Err(SolveError::CapacityFail);
                }
                if !in_queue[v] {
                    queue.push_back(v);
                    in_queue[v] = true;
                }
            }
        }
    }
    Ok(Validity { dist, parent })
}
