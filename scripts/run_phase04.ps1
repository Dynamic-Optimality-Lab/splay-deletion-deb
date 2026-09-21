# run_phase04.ps1 — SPEC 04 driver: diagonal-reachable pair space.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP2-P04-01]: phase 04 start.
Write-Host "[WP2-P04-01] SPEC 04 reachability gate start"
& python "$Repo\tests\test_wp2.py" --gate 04 --sizes "2 3 4 5 6"
if ($LASTEXITCODE -ne 0) { throw "gate 04 FAILED" }
# console.log equivalent [WP2-P04-02]: phase 04 sealed.
Write-Host "[WP2-P04-02] SPEC 04 PASS"
