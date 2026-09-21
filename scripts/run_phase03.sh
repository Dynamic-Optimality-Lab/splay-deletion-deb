#!/bin/sh
# run_phase03.sh — POSIX counterpart of run_phase03.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP2-P03-01]: phase 03 start.
echo "[WP2-P03-01] SPEC 03 transition-table gate start"
python3 "$REPO/tests/test_wp2.py" --gate 03 --sizes "2 3 4 5 6"
# console.log equivalent [WP2-P03-02]: phase 03 sealed.
echo "[WP2-P03-02] SPEC 03 PASS"
