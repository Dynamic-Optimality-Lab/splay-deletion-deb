#!/bin/sh
# run_phase18.sh — SPEC 18 driver: seal (result + archive + manifest) + audits.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP6-PH18-01]: phase 18 start.
echo "[WP6-PH18-01] SPEC 18 seal + audits start"
python3 "$REPO/python/wp6/seal.py"
python3 "$REPO/python/wp6/audits.py"
# console.log equivalent [WP6-PH18-02]: phase 18 sealed.
echo "[WP6-PH18-02] SPEC 18 seal + audits PASS"
