//! Two-sided seal checks: reduced p/q, sanity bracket by cross
//! multiplication, full-edge upper inequalities, and at least one valid
//! lower witness (nonempty transient path or nonempty reachable cycle).

use crate::rational::Reduced;

#[derive(Debug, PartialEq, Eq)]
pub enum SealError {
    NotReduced,
    Bracket,
    UpperViolation { edge: usize },
    NoLowerWitness,
}

pub fn check_reduced(p: i128, q: i128) -> Result<Reduced, SealError> {
    Reduced::new(p, q).ok_or(SealError::NotReduced)
}

pub fn check_bracket(b: Reduced, n: i128) -> Result<(), SealError> {
    if b.in_bracket(n).unwrap_or(false) {
        Ok(())
    } else {
        Err(SealError::Bracket)
    }
}
