#requires -Version 5.1
<#
Local development launcher. Infra (Postgres, Redis) runs in Docker; API, worker and web run
on the host with hot reload. Used by the VS Code tasks in .vscode/tasks.json.

  .\deploy\scripts\dev.ps1 infra    # docker compose up postgres redis (waits until healthy)
  .\deploy\scripts\dev.ps1 api      # migrations + uvicorn --reload
  .\deploy\scripts\dev.ps1 worker   # arq worker
  .\deploy\scripts\dev.ps1 web      # next dev
  .\deploy\scripts\dev.ps1 stop     # stop infra containers
#>
param([Parameter(Mandatory)][ValidateSet("infra", "api", "worker", "web", "stop")][string]$Service)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$envFile = Join-Path $root "deploy\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root "deploy\.env.example") $envFile
    Write-Host "Created deploy/.env from the example (edit it to change the password)."
}

$cfg = @{}
Get-Content $envFile | Where-Object { $_ -match '^\s*[A-Za-z_]+=' } | ForEach-Object {
    $k, $v = $_ -split '=', 2
    $cfg[$k.Trim()] = $v.Trim()
}
function Get-Cfg($name, $default) { if ($cfg[$name]) { $cfg[$name] } else { $default } }

$pgPort = Get-Cfg "POSTGRES_PORT" "5432"
$redisPort = Get-Cfg "REDIS_PORT" "6379"
$apiPort = Get-Cfg "API_PORT" "8000"
$webPort = Get-Cfg "WEB_PORT" "3000"

# Provider settings (ROLES, API keys, budget) are forwarded to the host processes.
foreach ($name in "ROLES", "OPENAI_API_KEY", "ELEVENLABS_API_KEY", "RUN_BUDGET_USD", "LOG_LEVEL") {
    if ($cfg[$name]) { Set-Item "env:$name" $cfg[$name] }
}
$env:DATABASE_URL = "postgresql+asyncpg://$($cfg.POSTGRES_USER):$($cfg.POSTGRES_PASSWORD)@127.0.0.1:$pgPort/$($cfg.POSTGRES_DB)"
$env:REDIS_URL = "redis://127.0.0.1:$redisPort/0"
$env:API_BASE_URL = "http://127.0.0.1:$apiPort"
$env:VOICE_STORAGE_DIR = Join-Path $root "storage\audio"

# Native stderr (e.g. Docker warnings) must not abort the script under $ErrorActionPreference=Stop.
function Test-Docker {
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try { docker info 2>&1 | Out-Null; return ($LASTEXITCODE -eq 0) } finally { $ErrorActionPreference = $prev }
}

function Wait-Port($port, $label) {
    for ($i = 0; $i -lt 60; $i++) {
        if (Test-NetConnection 127.0.0.1 -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue) { return }
        Start-Sleep -Seconds 2
    }
    throw "$label did not become reachable on port $port"
}

Set-Location $root
switch ($Service) {
    "infra" {
        docker info *> $null
        if ($LASTEXITCODE -ne 0) {
            $desktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
            if (-not (Test-Path $desktop)) { throw "Docker is not installed or not on PATH. Install Docker Desktop." }
            Write-Host "Docker engine is not running; starting Docker Desktop..."
            Start-Process $desktop
            $ready = $false
            for ($i = 0; $i -lt 90 -and -not $ready; $i++) {
                Start-Sleep -Seconds 2
                docker info *> $null
                $ready = ($LASTEXITCODE -eq 0)
            }
            if (-not $ready) { throw "Docker engine did not start within 3 minutes. Start Docker Desktop manually and retry." }
        }
        docker compose -f deploy/compose.yaml --env-file deploy/.env up -d --wait postgres redis
        if ($LASTEXITCODE -ne 0) { throw "docker compose failed" }
        Write-Host "Postgres on :$pgPort and Redis on :$redisPort are ready."
    }
    "api" {
        Wait-Port $pgPort "Postgres"
        uv sync --all-packages
        Set-Location (Join-Path $root "apps\api")
        uv run alembic upgrade head
        uv run uvicorn dcs_api.main:app_factory --factory --reload --host 127.0.0.1 --port $apiPort
    }
    "worker" {
        Wait-Port $redisPort "Redis"
        uv sync --all-packages
        uv run arq dcs_worker.settings.WorkerSettings --watch (Join-Path $root "apps\worker\src")
    }
    "web" {
        Set-Location (Join-Path $root "apps\web")
        if (-not (Test-Path node_modules)) { npm ci }
        npx next dev -p $webPort
    }
    "stop" {
        docker compose -f deploy/compose.yaml --env-file deploy/.env stop postgres redis
    }
}
