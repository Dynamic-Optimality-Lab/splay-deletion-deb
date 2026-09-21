//! Exact b_n* solver: integer-scaled parametric search, canonical potentials,
//! critical witnesses, and two-sided certificates. No floating point anywhere
//! in this crate (threat T6).

pub mod candidate;
pub mod canonical_potentials;
pub mod certificates;
pub mod critical_cycle;
pub mod critical_path;
pub mod difference_constraints;
pub mod rational;
pub mod shortest_path;
