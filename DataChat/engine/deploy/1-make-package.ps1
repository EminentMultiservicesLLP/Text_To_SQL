# STEP 1 - run on the DEVELOPER machine.
# Builds DataChat-engine.zip (code + packs only; no .venv, no .env secrets, no local data).
$ErrorActionPreference = "Stop"
$engine = Split-Path $PSScriptRoot -Parent
$stage = Join-Path $env:TEMP "datachat-engine-stage"
$zip = Join-Path (Split-Path $engine -Parent) "DataChat-engine.zip"

if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
robocopy $engine $stage /E /NFL /NDL /NJH /NJS /NP `
    /XD .venv data .pytest_cache __pycache__ reports draft `
    /XF .env *.pyc *.log | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy failed ($LASTEXITCODE)" }

if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zip
Remove-Item $stage -Recurse -Force
Write-Host "Package ready: $zip  ($([math]::Round((Get-Item $zip).Length / 1KB)) KB)"
Write-Host "Copy it to the server and unzip to e.g. D:\DataChat\engine"
