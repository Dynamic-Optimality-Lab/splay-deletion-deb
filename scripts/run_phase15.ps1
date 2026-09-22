# run_phase15.ps1 — SPEC 15 driver: positive-branch closure (no survivors).
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP6-PH15-01]: phase 15 start.
Write-Host "[WP6-PH15-01] SPEC 15 positive-branch closure start"
& python "$Repo\python\wp6\branches.py"
if ($LASTEXITCODE -ne 0) { throw "phase 15 FAILED" }
# console.log equivalent [WP6-PH15-02]: phase 15 sealed.
Write-Host "[WP6-PH15-02] SPEC 15 closure recorded"
