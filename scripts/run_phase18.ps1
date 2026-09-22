# run_phase18.ps1 — SPEC 18 driver: seal (result + archive + manifest) + audits.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP6-PH18-01]: phase 18 start.
Write-Host "[WP6-PH18-01] SPEC 18 seal + audits start"
& python "$Repo\python\wp6\seal.py"
if ($LASTEXITCODE -ne 0) { throw "seal FAILED" }
& python "$Repo\python\wp6\audits.py"
if ($LASTEXITCODE -ne 0) { throw "phase 18 audits FAILED" }
# console.log equivalent [WP6-PH18-02]: phase 18 sealed.
Write-Host "[WP6-PH18-02] SPEC 18 seal + audits PASS"
