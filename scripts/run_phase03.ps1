# run_phase03.ps1 — SPEC 03 driver: single-tree transition tables.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP2-P03-01]: phase 03 start.
Write-Host "[WP2-P03-01] SPEC 03 transition-table gate start"
& python "$Repo\tests\test_wp2.py" --gate 03 --sizes "2 3 4 5 6"
if ($LASTEXITCODE -ne 0) { throw "gate 03 FAILED" }
# console.log equivalent [WP2-P03-02]: phase 03 sealed.
Write-Host "[WP2-P03-02] SPEC 03 PASS"
