#!/bin/sh
# run_phase14.sh — POSIX counterpart of run_phase14.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP5-P14-01]: phase 14 start.
echo "[WP5-P14-01] SPEC 14 adversarial + holdout gate start"
python3 "$REPO/python/wp5/run_phase.py" --stage 14
# console.log equivalent [WP5-P14-02]: phase 14 sealed.
echo "[WP5-P14-02] SPEC 14 PASS"
