//! Candidate trail: every probed rational with its exact-certification status.
//! Discovery entries are never sealed; only the two-sided certificate seals.

use crate::rational::Reduced;

#[derive(Clone, Debug)]
pub struct CandidateProbe {
    pub b: Reduced,
    pub backend: &'static str,
    pub valid: Option<bool>,
}

#[derive(Clone, Debug)]
pub struct CandidateSet {
    pub n: u32,
    pub probes: Vec<CandidateProbe>,
    pub sealed: Option<Reduced>,
}
