# run_phase08.ps1 — SPEC 08 driver: critical geometry + B06 diagnostic gate.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP3-P08-01]: phase 08 start.
Write-Host "[WP3-P08-01] SPEC 08 critical-geometry gate start"
& python "$Repo\tests\test_wp3.py" --gate 08 --sizes "2 3 4 5 6 7"
if ($LASTEXITCODE -ne 0) { throw "gate 08 FAILED" }
# console.log equivalent [WP3-P08-02]: phase 08 sealed.
Write-Host "[WP3-P08-02] SPEC 08 PASS"
