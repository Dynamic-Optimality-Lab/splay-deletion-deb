//! Canonical U^Z / V^Z / G^Z tables (WP-3 computes full tables; WP-2 needs U^Z
//! for the upper certificate and zero-slack structure). Forced ⟺ G == 0
//! by exact integer equality, never tolerance.

#[derive(Clone, Debug)]
pub struct CanonicalRow {
    pub u_scaled: i128,
    pub v_scaled: i128,
}

impl CanonicalRow {
    pub fn gap(&self) -> Option<i128> {
        self.u_scaled.checked_sub(self.v_scaled)
    }

    pub fn forced(&self) -> Option<bool> {
        Some(self.gap()? == 0)
    }
}
