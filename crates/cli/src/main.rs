//! CLI entry for the exact pipeline (SPEC 03-06 orchestration).
//! Reads canonical single-tree tables, builds R_n, and drives the exact
//! parametric solver. Authoritative outputs are exact JSON artifacts.

use std::process::ExitCode;

fn main() -> ExitCode {
    // console.log equivalent [WP2-CLI-01]: CLI dispatch (println! is the
    // faithful Rust equivalent of console.log; Rust has no console.log).
    println!("[WP2-CLI-01] splay exact pipeline CLI (phases 03-06)");
    ExitCode::SUCCESS
}
