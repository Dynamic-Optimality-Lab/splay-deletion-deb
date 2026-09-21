//! Exact U^Z: shortest scaled slack from the diagonal super-source.
//! At a valid b no diagonal-reachable negative cycle exists, so distances
//! are finite and satisfy every local inequality with equality witnesses.

use crate::difference_constraints::{shortest_slacks, SolveError, WeightFn};
use pair_graph::reachability::SingleTables;
use pair_graph::state::Reachability;

pub struct UpperPotential {
    /// Integer-scaled potential per reachable_index (= U^Z here).
    pub values: Vec<i128>,
}

pub fn compute_upper(
    tables: &SingleTables,
    reach: &Reachability,
    weight: &WeightFn,
) -> Result<UpperPotential, SolveError> {
    let v = shortest_slacks(tables, reach, weight)?;
    let values = v
        .dist
        .into_iter()
        .map(|d| d.expect("all reachable states have finite dist at valid b"))
        .collect();
    Ok(UpperPotential { values })
}
