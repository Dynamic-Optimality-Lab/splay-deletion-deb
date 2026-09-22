# run_phase16.ps1 — SPEC 16 driver: P01 telescoping unit + P02 bridge audit.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP6-PH16-01]: phase 16 start.
Write-Host "[WP6-PH16-01] SPEC 16 telescoping unit + bridge audit start"
& python "$Repo\python\wp6\telescope.py"
if ($LASTEXITCODE -ne 0) { throw "phase 16 FAILED" }
# console.log equivalent [WP6-PH16-02]: phase 16 sealed.
Write-Host "[WP6-PH16-02] SPEC 16 records sealed"
