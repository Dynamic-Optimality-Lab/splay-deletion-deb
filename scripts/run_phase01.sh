#!/bin/sh
# run_phase01.sh — POSIX counterpart of run_phase01.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP1-P01-01]: phase 01 start.
echo "[WP1-P01-01] SPEC 01 Splay semantics gate start"
python3 "$REPO/tests/test_wp1.py" --gate 01
# console.log equivalent [WP1-P01-02]: phase 01 sealed.
echo "[WP1-P01-02] SPEC 01 PASS"
