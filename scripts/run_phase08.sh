#!/bin/sh
# run_phase08.sh — POSIX counterpart of run_phase08.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP3-P08-01]: phase 08 start.
echo "[WP3-P08-01] SPEC 08 critical-geometry gate start"
python3 "$REPO/tests/test_wp3.py" --gate 08 --sizes "2 3 4 5 6 7"
# console.log equivalent [WP3-P08-02]: phase 08 sealed.
echo "[WP3-P08-02] SPEC 08 PASS"
