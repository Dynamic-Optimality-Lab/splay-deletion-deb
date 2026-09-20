#!/bin/sh
# run_phase02.sh — POSIX counterpart of run_phase02.ps1.
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP1-P02-01]: phase 02 start.
echo "[WP1-P02-01] SPEC 02 enumeration gate start"
python3 "$REPO/tests/test_wp1.py" --gate 02
n=1
while [ $n -le 8 ]; do
    # console.log equivalent [WP1-P02-02]: per-n artifact build.
    echo "[WP1-P02-02] building artifacts/trees/n$n"
    python3 "$REPO/python/reference/enumerate.py" --n "$n" --out "$REPO/artifacts/trees/n$n"
    n=$((n + 1))
done
# console.log equivalent [WP1-P02-03]: phase 02 sealed.
echo "[WP1-P02-03] SPEC 02 PASS"
