# run_phase01.ps1 — SPEC 01 driver: reference Splay semantics gate.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP1-P01-01]: phase 01 start.
Write-Host "[WP1-P01-01] SPEC 01 Splay semantics gate start"
& python "$Repo\tests\test_wp1.py" --gate 01
if ($LASTEXITCODE -ne 0) { throw "gate 01 FAILED" }
# console.log equivalent [WP1-P01-02]: phase 01 sealed.
Write-Host "[WP1-P01-02] SPEC 01 PASS"
