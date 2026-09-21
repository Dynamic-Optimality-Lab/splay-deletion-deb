//! Canonical U^Z / V^Z / G^Z tables (WP-3 computes full tables; WP-2 needs U^Z
//! for the upper certificate and zero-slack structure). Forced ⟺ G == 0
//! by exact integer equality, never tolerance.
//!
//! Frozen FGAP decision rule for edge e:s→t (exact, threat T12):
//! FGAP(e) ⟺ G(s)==0 AND G(t)==0 AND U(t)−U(s)==L(e). Endpoints-U=V alone
//! never suffices; the difference check is mandatory.

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

/// Frozen FGAP rule. Returns the exact forced derivative on success.
pub fn fgap_derivative(
    g_source: i128,
    g_target: i128,
    u_source: i128,
    u_target: i128,
    edge_slack: i128,
) -> Option<i128> {
    if g_source == 0 && g_target == 0 && u_target.checked_sub(u_source)? == edge_slack {
        Some(edge_slack)
    } else {
        None
    }
}

/// Bellman inequality check for one edge: V(t)−V(s) ≤ L(e) (same for U).
pub fn bellman_holds(v_source: i128, v_target: i128, edge_slack: i128) -> Option<bool> {
    Some(v_target.checked_sub(v_source)? <= edge_slack)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fgap_requires_difference_check() {
        // Both endpoints forced but wrong difference: not FGAP.
        assert_eq!(fgap_derivative(0, 0, 5, 9, 3), None);
        // Exact match: FGAP with derivative 3.
        assert_eq!(fgap_derivative(0, 0, 5, 8, 3), Some(3));
        // Unforced endpoint: not FGAP even with matching difference.
        assert_eq!(fgap_derivative(1, 0, 5, 8, 3), None);
    }
}
