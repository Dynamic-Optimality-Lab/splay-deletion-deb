#!/bin/sh
# run_phase17.sh — SPEC 17 driver: P17 negative-branch activation analysis.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP6-PH17-01]: phase 17 start.
echo "[WP6-PH17-01] SPEC 17 P17 activation analysis start"
python3 "$REPO/python/wp6/p17_analysis.py"
# console.log equivalent [WP6-PH17-02]: phase 17 sealed.
echo "[WP6-PH17-02] SPEC 17 activation record sealed"
