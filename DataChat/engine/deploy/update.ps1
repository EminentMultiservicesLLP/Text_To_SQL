# UPDATE - run on the SERVER as Administrator after copying a new DataChat-engine.zip.
#   .\deploy\update.ps1 -Zip D:\DataChat\DataChat-engine.zip [-Group Society]
# Stops the engine, unpacks the new code over this folder (.env, .venv and data are kept), installs any new
# Python packages, checks database access, starts the engine and tests it.
param(
    [Parameter(Mandatory = $true)][string]$Zip,
    [string]$Group = ""
)
$ErrorActionPreference = "Stop"
$engine = Split-Path $PSScriptRoot -Parent
$py = "$engine\.venv\Scripts\python.exe"
if (-not (Test-Path $Zip)) { throw "Zip not found: $Zip" }
if (-not (Test-Path $py)) { throw "No .venv in $engine; run deploy\2-install-engine.ps1 first" }

Write-Host "1/5 Stopping the engine ..." -ForegroundColor Cyan
Stop-ScheduledTask -TaskName "DataChat-Engine" -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -like "*uvicorn*datachat*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep 2

Write-Host "2/5 Unpacking $Zip ..." -ForegroundColor Cyan
$backup = "$engine\data\backup-packs-$(Get-Date -Format yyyyMMdd-HHmmss)"
Copy-Item "$engine\packs" $backup -Recurse
Expand-Archive -Path $Zip -DestinationPath $engine -Force
Write-Host "    previous packs saved in $backup"

$ErrorActionPreference = "Continue"
Write-Host "3/5 Installing Python packages ..." -ForegroundColor Cyan
& $py -m pip install -q -r "$engine\requirements.txt" 2>&1 | ForEach-Object { "$_" }

Write-Host "4/5 Checking database access ..." -ForegroundColor Cyan
& $py "$engine\tools\check_access.py" 2>&1 | ForEach-Object { "$_" }
$accessOk = $LASTEXITCODE -eq 0

Write-Host "5/5 Starting the engine ..." -ForegroundColor Cyan
Start-ScheduledTask -TaskName "DataChat-Engine"
$up = $false
foreach ($i in 1..60) {
    Start-Sleep 5
    try { Invoke-RestMethod http://127.0.0.1:8765/health -TimeoutSec 5 | Out-Null; $up = $true; break } catch { }
}
if (-not $up) {
    Write-Host "Engine did not start in 5 minutes. See $engine\data\logs\engine.log" -ForegroundColor Red
    Write-Host "To go back: copy $backup over $engine\packs and run Start-ScheduledTask DataChat-Engine"
    exit 1
}
Write-Host "Engine is running." -ForegroundColor Green

Push-Location $engine
if ($Group) {
    Write-Host "`nTesting the '$Group' questions with the model ..." -ForegroundColor Cyan
    & $py tools\scenario_test.py bis --group $Group 2>&1 | ForEach-Object { "$_" }
} else {
    & "$engine\deploy\4-check.ps1"
}
Pop-Location
if (-not $accessOk) {
    Write-Host "`nSome tables can't be read yet: run the GRANT lines above, then questions on them will work." -ForegroundColor Yellow
}
