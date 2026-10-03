# Copies one Ollama model (manifest + its blobs) from this machine's model folder into -Destination,
# in the same folder layout, for servers that can't download models themselves.
# On the server, copy the contents of -Destination into its OLLAMA_MODELS folder.
param(
    [Parameter(Mandatory)] [string]$Destination,
    [string]$Source = "E:\BIS\OllamaModels",
    [string]$Model = "qwen3:8b"
)
$ErrorActionPreference = "Stop"
$name, $tag = $Model -split ":", 2
if (-not $tag) { $tag = "latest" }
$manifestRel = "manifests\registry.ollama.ai\library\$name\$tag"
$manifest = Join-Path $Source $manifestRel
if (-not (Test-Path $manifest)) { throw "Model $Model not found under $Source" }

$j = Get-Content $manifest -Raw | ConvertFrom-Json
$digests = @($j.config.digest) + @($j.layers.digest)
New-Item -ItemType Directory -Force (Join-Path $Destination (Split-Path $manifestRel)), (Join-Path $Destination "blobs") | Out-Null
Copy-Item $manifest (Join-Path $Destination $manifestRel) -Force
foreach ($d in $digests) {
    $blob = "blobs\" + ($d -replace ":", "-")
    Write-Host "Copying $blob"
    Copy-Item (Join-Path $Source $blob) (Join-Path $Destination $blob) -Force
}
Write-Host "Done: $Model exported to $Destination" -ForegroundColor Green
