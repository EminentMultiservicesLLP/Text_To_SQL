# STEP 5 - run on the SERVER as Administrator.
# Registers two startup tasks (run as SYSTEM, restart on failure): Ollama, then the DataChat engine.
param(
    [string]$ModelsDir = "D:\OllamaModels",
    [string]$OllamaExe = ""
)
$ErrorActionPreference = "Stop"
$engine = Split-Path $PSScriptRoot -Parent

if (-not $OllamaExe) {
    $OllamaExe = @("$env:ProgramFiles\Ollama\ollama.exe", "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe") |
        Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $OllamaExe) { $OllamaExe = (Get-Command ollama -ErrorAction SilentlyContinue).Source }
}
if (-not $OllamaExe -or -not (Test-Path $OllamaExe)) { throw "ollama.exe not found; pass -OllamaExe <path>" }

# the service runs as SYSTEM, so the model folder must be set machine-wide
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $ModelsDir, "Machine")
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "127.0.0.1:11434", "Machine")

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$atBoot = New-ScheduledTaskTrigger -AtStartup

# cmd.exe, not PowerShell: Windows PowerShell turns a program's stderr log lines into errors
$logs = "$engine\data\logs"
$ollama = New-ScheduledTaskAction -Execute "cmd.exe" -Argument ("/c `"set `"OLLAMA_MODELS=$ModelsDir`" && " +
    "set `"OLLAMA_HOST=127.0.0.1:11434`" && `"$OllamaExe`" serve >> `"$logs\ollama.log`" 2>&1`"")
Register-ScheduledTask -TaskName "DataChat-Ollama" -Action $ollama -Trigger $atBoot -Settings $settings `
    -Principal $principal -Force | Out-Null

$engineTrigger = New-ScheduledTaskTrigger -AtStartup
$engineTrigger.Delay = "PT1M"
$eng = New-ScheduledTaskAction -Execute "cmd.exe" -WorkingDirectory $engine -Argument ("/c `"`"$engine\.venv\Scripts\python.exe`" " +
    "-m uvicorn datachat.api:create_app --factory --host 127.0.0.1 --port 8765 --workers 1 >> `"$logs\engine.log`" 2>&1`"")
Register-ScheduledTask -TaskName "DataChat-Engine" -Action $eng -Trigger $engineTrigger -Settings $settings `
    -Principal $principal -Force | Out-Null

New-Item -ItemType Directory -Force "$engine\data\logs" | Out-Null
Get-Process ollama*, "ollama app" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-ScheduledTask -TaskName "DataChat-Ollama"
Start-Sleep 10
Start-ScheduledTask -TaskName "DataChat-Engine"
Write-Host "Registered and started DataChat-Ollama and DataChat-Engine. Logs: $engine\data\logs" -ForegroundColor Green
Write-Host "Run deploy\4-check.ps1 in about 2 minutes (the model loads from disk first)."
