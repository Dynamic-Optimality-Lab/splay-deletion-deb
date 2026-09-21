//! Transient witnesses: nonempty diagonal-rooted zero-slack paths.
//! Decision rule: such a path exists iff some edge (t -> s) satisfies
//! U(t) + L(e) == 0 (then U(s) == 0 and the tight prefix plus e certifies).

use pair_graph::edge::Mode;

pub struct TransientWitness {
    /// Edge sequence as (source_index, mode, key) with explicit targets.
    pub edges: Vec<(usize, Mode, u32, usize)>,
    pub sum_a: u64,
    pub sum_y: u64,
}

/// Zero-slack diagonal path ending with the given tight edge, or None.
/// tight_parent[s] = argmin predecessor edge (t, mode, key) with
/// U(t) + L(e) == U(s); dist = U^Z table.
pub fn find_transient(
    dist: &[i128],
    tight_parent: &[Option<(usize, Mode, u32)>],
    is_diagonal: &[bool],
) -> Option<Vec<(usize, Mode, u32, usize)>> {
    let mut best: Option<(usize, Mode, u32, usize)> = None;
    for (s, parent) in tight_parent.iter().enumerate() {
        if let Some((t, mode, key)) = parent {
            if dist[*t] == 0 && dist[s] == 0 {
                // Candidate last edge of a zero path; verify prefix below.
                best = Some((*t, *mode, *key, s));
                break;
            }
        }
    }
    let (t, mode, key, s) = best?;
    let _ = is_diagonal;
    // Reconstruct tight prefix to t (dist decreases to a diagonal 0).
    let mut rev = vec![(t, mode, key, s)];
    let mut cur = t;
    let mut guard = dist.len() + 1;
    while dist[cur] != 0 || !is_diagonal[cur] {
        guard -= 1;
        if guard == 0 {
            return None;
        }
        let (pt, pm, pk) = tight_parent[cur]?;
        rev.push((pt, pm, pk, cur));
        cur = pt;
    }
    rev.reverse();
    Some(rev)
}
