# run_phase05.ps1 — SPEC 05 driver: rational candidate discovery.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP2-P05-01]: phase 05 start.
Write-Host "[WP2-P05-01] SPEC 05 discovery gate start"
& python "$Repo\tests\test_wp2.py" --gate 05 --sizes "2 3 4 5 6"
if ($LASTEXITCODE -ne 0) { throw "gate 05 FAILED" }
# console.log equivalent [WP2-P05-02]: phase 05 sealed.
Write-Host "[WP2-P05-02] SPEC 05 PASS"
