# run_phase07.ps1 — SPEC 07 driver: canonical potentials gate.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP3-P07-01]: phase 07 start.
Write-Host "[WP3-P07-01] SPEC 07 canonical-potentials gate start"
& python "$Repo\tests\test_wp3.py" --gate 07 --sizes "2 3 4 5 6 7"
if ($LASTEXITCODE -ne 0) { throw "gate 07 FAILED" }
# console.log equivalent [WP3-P07-02]: phase 07 sealed.
Write-Host "[WP3-P07-02] SPEC 07 PASS"
