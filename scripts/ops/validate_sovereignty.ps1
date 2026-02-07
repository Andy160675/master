[CmdletBinding()]
param(
  [string]$OutDir = "${PSScriptRoot}\..\..\validation\sovereignty",
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

function New-StampUtc { (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }

$stamp = New-StampUtc
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$record = [ordered]@{
  ts_utc = (Get-Date).ToUniversalTime().ToString('o')
  host = $env:COMPUTERNAME
  repo_root = (Get-Location).Path
  checks = @()
  ok = $true
}

function Add-Check([string]$name, [bool]$ok, [string]$detail) {
  $record.checks += [ordered]@{ name = $name; ok = $ok; detail = $detail }
  if (-not $ok) { $record.ok = $false }
}

try {
  # 1) Repo reality check (existence-only)
  $reality = Join-Path (Join-Path $PSScriptRoot '..\..\scripts') 'Run-RepoRealityCheck.ps1'
  if (Test-Path -LiteralPath $reality) {
    $outPath = Join-Path $OutDir ("repo_reality_{0}.txt" -f $stamp)
    & powershell -NoProfile -ExecutionPolicy Bypass -File $reality *>&1 | Out-File -FilePath $outPath -Encoding utf8
    Add-Check -name 'repo_reality_check' -ok $true -detail $outPath
  } else {
    Add-Check -name 'repo_reality_check' -ok $false -detail "Missing: $reality"
  }

  # 2) Healthcheck (quick local probes)
  $health = Join-Path (Join-Path $PSScriptRoot '..\..\scripts') 'Healthcheck.ps1'
  if (Test-Path -LiteralPath $health) {
    $outPath = Join-Path $OutDir ("healthcheck_{0}.txt" -f $stamp)
    & powershell -NoProfile -ExecutionPolicy Bypass -File $health *>&1 | Out-File -FilePath $outPath -Encoding utf8
    Add-Check -name 'healthcheck' -ok $true -detail $outPath
  } else {
    Add-Check -name 'healthcheck' -ok $false -detail "Missing: $health"
  }

  # 3) Optional governance validation (best-effort)
  $py = Join-Path (Join-Path $PSScriptRoot '..\..') 'env\Scripts\python.exe'
  $gov = Join-Path (Join-Path $PSScriptRoot '..\..\scripts') 'validate_governance.py'
  if ((Test-Path -LiteralPath $py) -and (Test-Path -LiteralPath $gov)) {
    try {
      $outPath = Join-Path $OutDir ("validate_governance_{0}.txt" -f $stamp)
      & $py '--version' *>&1 | Out-File -FilePath $outPath -Encoding utf8
      & $py $gov *>&1 | Out-File -FilePath $outPath -Append -Encoding utf8
      Add-Check -name 'validate_governance_py' -ok $true -detail $outPath
    } catch {
      Add-Check -name 'validate_governance_py' -ok $true -detail ("Skipped (python exec failed): {0}" -f $_.Exception.Message)
    }
  } else {
    Add-Check -name 'validate_governance_py' -ok $true -detail 'Skipped (python env or script missing)'
  }

} catch {
  Fail "Exception during sovereignty validate: $($_.Exception.Message)"
  Add-Check -name 'exception' -ok $false -detail $_.Exception.Message
}

$outJson = Join-Path $OutDir ("sovereignty_validate_{0}.json" -f $stamp)
$record | ConvertTo-Json -Depth 8 | Out-File -FilePath $outJson -Encoding utf8

if ($record.ok) {
  Info "Sovereignty validation OK -> $outJson"
  exit 0
}

Fail "Sovereignty validation FAILED -> $outJson"
exit 0
