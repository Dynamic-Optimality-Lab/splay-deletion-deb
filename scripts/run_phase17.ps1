# run_phase17.ps1 — SPEC 17 driver: P17 negative-branch activation analysis.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP6-PH17-01]: phase 17 start.
Write-Host "[WP6-PH17-01] SPEC 17 P17 activation analysis start"
& python "$Repo\python\wp6\p17_analysis.py"
if ($LASTEXITCODE -ne 0) { throw "phase 17 FAILED" }
# console.log equivalent [WP6-PH17-02]: phase 17 sealed.
Write-Host "[WP6-PH17-02] SPEC 17 activation record sealed"
