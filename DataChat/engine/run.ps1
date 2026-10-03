# Starts the DataChat engine on this machine only (127.0.0.1). The Blazor app calls it over localhost.
# Logs go to stderr; with "Stop" Windows PowerShell would treat the first log line as an error and quit.
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m uvicorn datachat.api:create_app --factory --host 127.0.0.1 --port 8765 --workers 1 2>&1 |
    ForEach-Object { "$_" }
