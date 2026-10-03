# Add one database table to a client pack in one step, then build the server package.
#   .\add-table.ps1 -Table public.smtbtsociety              (client bis, alias = table name)
#   .\add-table.ps1 -Table public.smtbtsociety -Alias soc -Client bis
# Shows one review and asks before changing anything. Afterwards copy DataChat-engine.zip to the server
# and run deploy\update.ps1 there.
param(
    [Parameter(Mandatory = $true)][string]$Table,
    [string]$Client = "bis",
    [string]$Alias = ""
)
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { Write-Host "No .venv here; run deploy\2-install-engine.ps1 first." -ForegroundColor Red; exit 1 }

$pyArgs = @("tools\add_table.py", "--client", $Client, "--table", $Table)
if ($Alias) { $pyArgs += @("--alias", $Alias) }
& $py @pyArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`nRunning the unit tests and the built-in-rules scenarios ..." -ForegroundColor Cyan
& $py -m pytest -q 2>&1 | Select-Object -Last 3 | ForEach-Object { "$_" }
& $py tools\scenario_test.py $Client --rules 2>&1 | Select-Object -Last 5 | ForEach-Object { "$_" }

Write-Host "`nBuilding the server package ..." -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "deploy\1-make-package.ps1")
Write-Host "`nNext, on the server: copy DataChat-engine.zip next to the engine folder and run" -ForegroundColor Green
Write-Host "  .\deploy\update.ps1 -Zip <path to DataChat-engine.zip>" -ForegroundColor Green
