#!/bin/sh
# run_phase05.sh — POSIX counterpart of run_phase05.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP2-P05-01]: phase 05 start.
echo "[WP2-P05-01] SPEC 05 discovery gate start"
python3 "$REPO/tests/test_wp2.py" --gate 05 --sizes "2 3 4 5 6"
# console.log equivalent [WP2-P05-02]: phase 05 sealed.
echo "[WP2-P05-02] SPEC 05 PASS"
