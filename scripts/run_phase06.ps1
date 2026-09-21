# run_phase06.ps1 — SPEC 06 driver: exact b_n* certification seal.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP2-P06-01]: phase 06 start.
Write-Host "[WP2-P06-01] SPEC 06 certification gate start"
& python "$Repo\tests\test_wp2.py" --gate 06 --sizes "2 3 4 5 6"
if ($LASTEXITCODE -ne 0) { throw "gate 06 FAILED" }
# console.log equivalent [WP2-P06-02]: phase 06 sealed.
Write-Host "[WP2-P06-02] SPEC 06 PASS"
