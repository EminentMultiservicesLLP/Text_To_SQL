# STEP 6 - run on the SERVER. Checks Ollama, the model, the engine, the database and one real question.
param([string]$Question = "billing last month")
$engine = Split-Path $PSScriptRoot -Parent
$envFile = Get-Content "$engine\.env" | Where-Object { $_ -match "^\s*[A-Z_]+=" }
$cfg = @{}; foreach ($l in $envFile) { $k, $v = $l -split "=", 2; $cfg[$k.Trim()] = $v.Trim() }
$ok = $true
function Step($name, [scriptblock]$body) {
    try { $r = & $body; Write-Host "[OK]   $name $r" -ForegroundColor Green }
    catch { Write-Host "[FAIL] $name - $($_.Exception.Message)" -ForegroundColor Red; $script:ok = $false }
}

Step "Ollama running" { (Invoke-RestMethod http://127.0.0.1:11434/api/version -TimeoutSec 10).version }
Step "Model $($cfg.DATACHAT_LLM_MODEL) installed" {
    $names = (Invoke-RestMethod http://127.0.0.1:11434/api/tags -TimeoutSec 10).models.name
    if ($names -notcontains $cfg.DATACHAT_LLM_MODEL) { throw "not found; run: ollama pull $($cfg.DATACHAT_LLM_MODEL)" }
}
Step "Engine running" {
    $h = Invoke-RestMethod http://127.0.0.1:8765/health -TimeoutSec 10
    if (-not $h.llm_enabled) { throw "engine is up but the LLM is disabled in .env" }
    "clients: $($h.clients -join ', ')"
}
Step "Question '$Question'" {
    $body = @{ client_id = "bis"; user_id = "deploy-check"; conversation_id = [guid]::NewGuid().ToString();
               message = $Question } | ConvertTo-Json
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $r = Invoke-RestMethod http://127.0.0.1:8765/v1/chat -Method Post -Body $body -ContentType "application/json" `
        -Headers @{ "X-Api-Key" = $cfg.DATACHAT_API_KEY } -TimeoutSec 300
    "($([math]::Round($sw.Elapsed.TotalSeconds))s): $($r.text)"
}
if ($ok) { Write-Host "All checks passed." -ForegroundColor Green }
else { Write-Host "See $engine\data\logs\engine.log and ollama.log" -ForegroundColor Yellow }
