#!/bin/sh
# run_phase04.sh — POSIX counterpart of run_phase04.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP2-P04-01]: phase 04 start.
echo "[WP2-P04-01] SPEC 04 reachability gate start"
python3 "$REPO/tests/test_wp2.py" --gate 04 --sizes "2 3 4 5 6"
# console.log equivalent [WP2-P04-02]: phase 04 sealed.
echo "[WP2-P04-02] SPEC 04 PASS"
