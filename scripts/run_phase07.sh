#!/bin/sh
# run_phase07.sh — POSIX counterpart of run_phase07.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP3-P07-01]: phase 07 start.
echo "[WP3-P07-01] SPEC 07 canonical-potentials gate start"
python3 "$REPO/tests/test_wp3.py" --gate 07 --sizes "2 3 4 5 6 7"
# console.log equivalent [WP3-P07-02]: phase 07 sealed.
echo "[WP3-P07-02] SPEC 07 PASS"
