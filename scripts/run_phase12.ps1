# run_phase12.ps1 — SPEC 12 driver: candidate freeze + development gates (UH-0..UH-3, UH-5, OG, mutation).
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP5-P12-01]: phase 12 start.
Write-Host "[WP5-P12-01] SPEC 12 candidate-freeze + development-gate start"
& python "$Repo\python\wp5\run_phase.py" --stage 12
if ($LASTEXITCODE -ne 0) { throw "phase 12 FAILED" }
# console.log equivalent [WP5-P12-02]: phase 12 sealed.
Write-Host "[WP5-P12-02] SPEC 12 PASS"
