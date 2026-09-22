#!/bin/sh
# run_uh4_repair.sh — POSIX counterpart of run_uh4_repair.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP5-UH4R-01]: repair pipeline start.
echo "[WP5-UH4R-01] UH-4 compliance-repair pipeline start"
python3 "$REPO/python/wp5/uh4_geometry.py" --sizes "2 3 4 5 6 7"
python3 "$REPO/python/wp5/uh4_sandwich.py"
python3 "$REPO/tests/test_wp5_uh4.py"
python3 "$REPO/scripts/stress_uh4.py"
# console.log equivalent [WP5-UH4R-02]: repair pipeline sealed.
echo "[WP5-UH4R-02] UH-4 compliance-repair pipeline PASS"
