# run_phase00.ps1 — SPEC 00 driver: foundation freeze verification.
# Each step emits identified console output (console.log equivalent:
# PowerShell has no console.log; Write-Host to the console is the faithful
# equivalent). Step IDs are recorded in Path.md with file:line references.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP1-P00-01]: phase 00 start.
Write-Host "[WP1-P00-01] SPEC 00 foundation gate start"
& python "$Repo\tests\test_wp1.py" --gate 00
if ($LASTEXITCODE -ne 0) { throw "gate 00 FAILED" }
# console.log equivalent [WP1-P00-02]: Rust type-check.
Write-Host "[WP1-P00-02] cargo check --tests"
$prevPref = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& cargo check --tests --manifest-path "$Repo\Cargo.toml" 2>&1 | ForEach-Object { "$_" }
$ErrorActionPreference = $prevPref
if ($LASTEXITCODE -ne 0) { throw "cargo check FAILED" }
# console.log equivalent [WP1-P00-03]: phase 00 sealed.
Write-Host "[WP1-P00-03] SPEC 00 PASS"
