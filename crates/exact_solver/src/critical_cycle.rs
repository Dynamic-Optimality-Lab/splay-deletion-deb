//! Cyclic witnesses: reachable zero-slack directed cycles via SCCs of the
//! zero-reduced subgraph {e : L(e) - (P(t) - P(s)) == 0} for an exact
//! feasible potential P. Iterative Tarjan; an SCC with >1 vertex or a zero
//! self-loop contains a zero cycle. One canonical simple cycle per SCC.

use pair_graph::edge::Mode;

pub struct CycleWitness {
    /// Simple directed cycle as (source_index, mode, key) with explicit targets.
    pub edges: Vec<(usize, Mode, u32, usize)>,
    pub sum_a: u64,
    pub sum_y: u64,
}

/// Iterative Tarjan SCC over adjacency given as ordered neighbor lists.
pub fn strongly_connected(adj: &[Vec<(usize, Mode, u32)>]) -> Vec<Vec<usize>> {
    let n = adj.len();
    let mut index = vec![usize::MAX; n];
    let mut low = vec![0usize; n];
    let mut on_stack = vec![false; n];
    let mut stack: Vec<usize> = Vec::new();
    let mut sccs = Vec::new();
    let mut counter = 0usize;
    for root in 0..n {
        if index[root] != usize::MAX {
            continue;
        }
        let mut work: Vec<(usize, usize)> = vec![(root, 0)];
        while let Some((v, ci)) = work.pop() {
            if ci == 0 {
                index[v] = counter;
                low[v] = counter;
                counter += 1;
                stack.push(v);
                on_stack[v] = true;
            }
            if ci < adj[v].len() {
                let (w, _, _) = adj[v][ci];
                work.push((v, ci + 1));
                if index[w] == usize::MAX {
                    work.push((w, 0));
                } else if on_stack[w] {
                    low[v] = low[v].min(index[w]);
                }
            } else {
                if !work.is_empty() {
                    if let Some((parent, _)) = work.last() {
                        let p = *parent;
                        if on_stack[v] {
                            low[p] = low[p].min(low[v]);
                        }
                    }
                }
                if low[v] == index[v] {
                    let mut comp = Vec::new();
                    while let Some(w) = stack.pop() {
                        on_stack[w] = false;
                        comp.push(w);
                        if w == v {
                            break;
                        }
                    }
                    sccs.push(comp);
                }
            }
        }
    }
    sccs
}
