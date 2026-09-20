# run_phase02.ps1 — SPEC 02 driver: enumeration gate + tree artifacts n=1..8.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP1-P02-01]: phase 02 start.
Write-Host "[WP1-P02-01] SPEC 02 enumeration gate start"
& python "$Repo\tests\test_wp1.py" --gate 02
if ($LASTEXITCODE -ne 0) { throw "gate 02 FAILED" }
foreach ($n in 1..8) {
    # console.log equivalent [WP1-P02-02]: per-n artifact build.
    Write-Host "[WP1-P02-02] building artifacts/trees/n$n"
    & python "$Repo\python\reference\enumerate.py" --n $n --out "$Repo\artifacts\trees\n$n"
    if ($LASTEXITCODE -ne 0) { throw "tree build n=$n FAILED" }
}
# console.log equivalent [WP1-P02-03]: phase 02 sealed.
Write-Host "[WP1-P02-03] SPEC 02 PASS"
