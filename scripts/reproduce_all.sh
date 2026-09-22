#!/bin/sh
# reproduce_all.sh — clean reproduction driver (S01).
set -e
REPO="$(dirname "$0")/.."
# console.log equivalent [WP6-RP-01]: reproduction start.
echo "[WP6-RP-01] clean reproduction start"
python3 "$REPO/python/wp6/reproduce.py"
# console.log equivalent [WP6-RP-02]: reproduction sealed.
echo "[WP6-RP-02] clean reproduction PASS"
