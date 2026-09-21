//! Reduced exact rationals p/q with cross-multiplication comparisons.
//! Serialized as base-10 integer strings; no decimal approximations.

fn gcd(mut a: i128, mut m: i128) -> i128 {
    while m != 0 {
        let t = m;
        m = a % m;
        a = t;
    }
    a.abs()
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Reduced {
    pub p: i128,
    pub q: i128,
}

impl Reduced {
    /// Reduced form; requires p, q > 0.
    pub fn new(p: i128, q: i128) -> Option<Reduced> {
        if p <= 0 || q <= 0 {
            return None;
        }
        let g = gcd(p, q);
        Some(Reduced { p: p / g, q: q / g })
    }

    /// Exact comparison self >= other by cross multiplication (may overflow
    /// on absurd inputs; callers prove run-specific bounds first).
    pub fn ge(self, other: Reduced) -> Option<bool> {
        Some(self.p.checked_mul(other.q)? >= other.p.checked_mul(self.q)?)
    }

    /// Exact sanity bracket 1 <= p/q <= n by cross multiplication.
    pub fn in_bracket(self, n: i128) -> Option<bool> {
        Some(self.q <= self.p && self.p <= n.checked_mul(self.q)?)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reduces_and_compares() {
        let b = Reduced::new(6, 4).unwrap();
        assert_eq!((b.p, b.q), (3, 2));
        assert!(b.ge(Reduced::new(4, 3).unwrap()).unwrap());
        assert!(b.in_bracket(5).unwrap());
        assert!(!b.in_bracket(1).unwrap());
    }
}
