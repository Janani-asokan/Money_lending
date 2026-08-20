$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$environmentFile = Join-Path $projectRoot '.env.production'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker Desktop is required. Install and start Docker Desktop, then run this script again.'
}

if (-not (Test-Path -LiteralPath $environmentFile)) {
    throw 'Create .env.production from .env.production.example and replace every CHANGE_ME value.'
}

$unsafeValues = Select-String -LiteralPath $environmentFile -Pattern 'CHANGE_ME'
if ($unsafeValues) {
    throw '.env.production still contains CHANGE_ME placeholders.'
}

docker compose --env-file $environmentFile -f (Join-Path $projectRoot 'compose.production.yml') up -d
if ($LASTEXITCODE -ne 0) { throw 'MongoDB containers failed to start.' }

docker compose --env-file $environmentFile -f (Join-Path $projectRoot 'compose.production.yml') ps
Write-Host 'MongoDB persistent replica is running on 127.0.0.1:27017.' -ForegroundColor Green
