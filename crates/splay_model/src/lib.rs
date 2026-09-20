//! Exact BST / bottom-up Splay model with frozen v0.1 semantics.
//!
//! Cost convention: c(T,x) = depth + 1. Pair-graph and solver crates build on
//! the transition operation frozen here; they may not alter it.

pub mod encode;
pub mod enumerate;
pub mod rotate;
pub mod splay;
pub mod tree;

pub use encode::Shape;
pub use tree::Tree;
