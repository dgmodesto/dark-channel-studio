$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose --env-file .env up -d --build
if ($LASTEXITCODE -ne 0) { throw "compose up failed" }
$port = ((Get-Content .env | Where-Object { $_ -match '^API_PORT=' }) -replace '^API_PORT=', '')
if (-not $port) { $port = 8000 }
for ($i = 0; $i -lt 60; $i++) {
  try {
    $r = Invoke-RestMethod "http://127.0.0.1:$port/health" -TimeoutSec 3
    if ($r.status -eq "healthy") { Write-Host "OK: platform healthy"; exit 0 }
  } catch { }
  Start-Sleep 2
}
docker compose --env-file .env ps
Write-Error "FAIL: platform did not become healthy"
exit 1
