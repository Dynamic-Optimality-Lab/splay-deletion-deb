#!/bin/sh
# run_phase13.sh — POSIX counterpart of run_phase13.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP5-P13-01]: phase 13 start.
echo "[WP5-P13-01] SPEC 13 independent-falsifier gate start"
python3 "$REPO/python/wp5/run_phase.py" --stage 13
# console.log equivalent [WP5-P13-02]: phase 13 sealed.
echo "[WP5-P13-02] SPEC 13 PASS"
