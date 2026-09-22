#!/bin/sh
# run_phase12.sh — POSIX counterpart of run_phase12.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP5-P12-01]: phase 12 start.
echo "[WP5-P12-01] SPEC 12 candidate-freeze + development-gate start"
python3 "$REPO/python/wp5/run_phase.py" --stage 12
# console.log equivalent [WP5-P12-02]: phase 12 sealed.
echo "[WP5-P12-02] SPEC 12 PASS"
