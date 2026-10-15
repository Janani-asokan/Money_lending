$ErrorActionPreference = "Stop"
$composeArgs = @("compose", "--env-file", ".env.production", "-f", "compose.production.yml")

docker @composeArgs ps

$httpPort = if ($env:APP_HTTP_PORT) { $env:APP_HTTP_PORT } else { "8080" }
$health = Invoke-RestMethod -Uri "http://127.0.0.1:$httpPort/api/health" -TimeoutSec 15
if (-not $health.ok -or -not $health.ready -or $health.database -ne "mongodb") {
    throw "Application health verification failed"
}

$unhealthy = docker @composeArgs ps --format json | ConvertFrom-Json | Where-Object { $_.Health -and $_.Health -ne "healthy" }
if ($unhealthy) {
    throw "One or more production services are unhealthy: $($unhealthy.Service -join ', ')"
}

Write-Host "Production stack verified: gateway, frontend, API and MongoDB are available."
