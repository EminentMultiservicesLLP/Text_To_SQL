# STEP 3 - run on the SERVER, inside the unzipped engine folder (after Python 3.12 is installed).
# Creates a separate Python environment (.venv) for DataChat only and installs its packages into it.
$ErrorActionPreference = "Stop"
$engine = Split-Path $PSScriptRoot -Parent
Set-Location $engine

$python = $null
foreach ($cand in @(@("py", "-3.12"), @("py", "-3"), @("python"))) {
    try {
        $v = & $cand[0] $cand[1..9] -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -eq 0 -and [version]$v -ge [version]"3.11") { $python = $cand; break }
    } catch { }
}
if (-not $python) { throw "Python 3.11+ not found. Install Python 3.12 from python.org first (step 2)." }
Write-Host "Using Python $v ($($python -join ' '))"

if (-not (Test-Path .venv\Scripts\python.exe)) {
    & $python[0] $python[1..9] -m venv .venv
}
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

New-Item -ItemType Directory -Force data, data\logs | Out-Null
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example - EDIT IT NOW (BIS_DSN, DATACHAT_API_KEY, DATACHAT_LLM_NUM_THREAD)." -ForegroundColor Yellow
}

.\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed - do not continue, send the output." }
Write-Host "Engine installed in $engine\.venv" -ForegroundColor Green
