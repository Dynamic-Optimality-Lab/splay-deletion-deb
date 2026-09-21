#!/bin/sh
# run_phase06.sh — POSIX counterpart of run_phase06.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP2-P06-01]: phase 06 start.
echo "[WP2-P06-01] SPEC 06 certification gate start"
python3 "$REPO/tests/test_wp2.py" --gate 06 --sizes "2 3 4 5 6"
# console.log equivalent [WP2-P06-02]: phase 06 sealed.
echo "[WP2-P06-02] SPEC 06 PASS"
