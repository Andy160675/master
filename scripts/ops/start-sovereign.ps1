[CmdletBinding()]
param(
  [switch]$Gate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Info([string]$m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Warn([string]$m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail([string]$m) {
  Write-Host "[FAIL] $m" -ForegroundColor Red
  if ($Gate) { exit 1 }
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
Push-Location $repoRoot

try {
  $docker = Get-Command docker -ErrorAction SilentlyContinue
  if (-not $docker) {
    Fail 'docker not found'
    exit 0
  }

  $composeOk = $false
  try { & docker compose version *> $null; if ($LASTEXITCODE -eq 0) { $composeOk = $true } } catch {}

  Info 'Bootstrapping sovereign services (docker compose up -d)'
  if ($composeOk) {
    & docker compose up -d
  } else {
    & docker-compose up -d
  }

  Info 'docker compose ps'
  if ($composeOk) { & docker compose ps } else { & docker-compose ps }

} catch {
  Fail "start-sovereign failed: $($_.Exception.Message)"
} finally {
  Pop-Location
}

exit 0
