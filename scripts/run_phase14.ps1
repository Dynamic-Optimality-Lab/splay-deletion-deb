# run_phase14.ps1 — SPEC 14 driver: adversarial falsification + UH-8 + holdout consumption.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP5-P14-01]: phase 14 start.
Write-Host "[WP5-P14-01] SPEC 14 adversarial + holdout gate start"
& python "$Repo\python\wp5\run_phase.py" --stage 14
if ($LASTEXITCODE -ne 0) { throw "phase 14 FAILED" }
# console.log equivalent [WP5-P14-02]: phase 14 sealed.
Write-Host "[WP5-P14-02] SPEC 14 PASS"
