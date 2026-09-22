#!/bin/sh
# run_phase16.sh — SPEC 16 driver: P01 telescoping unit + P02 bridge audit.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP6-PH16-01]: phase 16 start.
echo "[WP6-PH16-01] SPEC 16 telescoping unit + bridge audit start"
python3 "$REPO/python/wp6/telescope.py"
# console.log equivalent [WP6-PH16-02]: phase 16 sealed.
echo "[WP6-PH16-02] SPEC 16 records sealed"
