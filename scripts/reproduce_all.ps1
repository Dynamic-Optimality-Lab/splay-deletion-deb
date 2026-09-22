# reproduce_all.ps1 — clean reproduction driver (S01).
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP6-RP-01]: reproduction start.
Write-Host "[WP6-RP-01] clean reproduction start"
& python "$Repo\python\wp6\reproduce.py"
if ($LASTEXITCODE -ne 0) { throw "reproduction FAILED" }
# console.log equivalent [WP6-RP-02]: reproduction sealed.
Write-Host "[WP6-RP-02] clean reproduction PASS"
