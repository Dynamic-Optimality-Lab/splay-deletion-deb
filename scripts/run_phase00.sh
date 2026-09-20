#!/bin/sh
# run_phase00.sh — POSIX counterpart of run_phase00.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP1-P00-01]: phase 00 start.
echo "[WP1-P00-01] SPEC 00 foundation gate start"
python3 "$REPO/tests/test_wp1.py" --gate 00
# console.log equivalent [WP1-P00-02]: Rust type-check.
echo "[WP1-P00-02] cargo check --tests"
cargo check --tests --manifest-path "$REPO/Cargo.toml"
# console.log equivalent [WP1-P00-03]: phase 00 sealed.
echo "[WP1-P00-03] SPEC 00 PASS"
