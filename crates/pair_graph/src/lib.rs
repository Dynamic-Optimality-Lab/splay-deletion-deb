//! Diagonal-reachable paired state space R_n (frozen SPEC 04).
//! Consumes frozen single-tree transition tables; never alters Splay semantics.

pub mod csr;
pub mod edge;
pub mod reachability;
pub mod reverse;
pub mod state;

pub use edge::{EdgeKey, Mode};
pub use state::{PairId, Reachability};
