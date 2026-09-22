# run_phase13.ps1 — SPEC 13 driver: UH-4 sandwich tables + independent H05 verification.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP5-P13-01]: phase 13 start.
Write-Host "[WP5-P13-01] SPEC 13 independent-falsifier gate start"
& python "$Repo\python\wp5\run_phase.py" --stage 13
if ($LASTEXITCODE -ne 0) { throw "phase 13 FAILED" }
# console.log equivalent [WP5-P13-02]: phase 13 sealed.
Write-Host "[WP5-P13-02] SPEC 13 PASS"
