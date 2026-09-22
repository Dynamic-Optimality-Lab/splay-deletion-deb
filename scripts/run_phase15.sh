#!/bin/sh
# run_phase15.sh — SPEC 15 driver: positive-branch closure (no survivors).
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP6-PH15-01]: phase 15 start.
echo "[WP6-PH15-01] SPEC 15 positive-branch closure start"
python3 "$REPO/python/wp6/branches.py"
# console.log equivalent [WP6-PH15-02]: phase 15 sealed.
echo "[WP6-PH15-02] SPEC 15 closure recorded"
