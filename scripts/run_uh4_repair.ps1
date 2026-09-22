# run_uh4_repair.ps1 — WP-5 UH-4 compliance-repair driver: b=2 geometry + independent verify + sandwich + gates + stress.
$ErrorActionPreference = "Stop"
$Repo = Split-Path -Parent $PSScriptRoot
# console.log equivalent [WP5-UH4R-01]: repair pipeline start.
Write-Host "[WP5-UH4R-01] UH-4 compliance-repair pipeline start"
& python "$Repo\python\wp5\uh4_geometry.py" --sizes "2 3 4 5 6 7"
if ($LASTEXITCODE -ne 0) { throw "b=2 geometry FAILED" }
& python "$Repo\python\wp5\uh4_sandwich.py"
if ($LASTEXITCODE -ne 0) { throw "UH-4 sandwich FAILED" }
& python "$Repo\tests\test_wp5_uh4.py"
if ($LASTEXITCODE -ne 0) { throw "UH-4 gates FAILED" }
& python "$Repo\scripts\stress_uh4.py"
if ($LASTEXITCODE -ne 0) { throw "UH-4 stress FAILED" }
# console.log equivalent [WP5-UH4R-02]: repair pipeline sealed.
Write-Host "[WP5-UH4R-02] UH-4 compliance-repair pipeline PASS"
