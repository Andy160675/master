[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$CycleRoot,
  [ValidateRange(0, 86400)][int]$MaxWindowSeconds = 7200,
  [switch]$EmitJson,
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

function Read-Json([string]$path) {
  return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function ConvertTo-UtcDateTime([string]$s) {
  if ([string]::IsNullOrWhiteSpace($s)) { return $null }
  try { return [DateTime]::Parse($s).ToUniversalTime() } catch { return $null }
}

function Get-Sha256([string]$path) {
  try { return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant() } catch { return $null }
}

$cycleRootPath = (Resolve-Path -LiteralPath $CycleRoot).Path

$deployJsonl = Join-Path $cycleRootPath 'deploy.jsonl'
$deploySummary = $deployJsonl + '.summary.json'
$pentad = Join-Path $cycleRootPath 'pentad_balance.jsonl'
$sovereigntyDir = Join-Path $cycleRootPath 'sovereignty'

$sovereigntyJson = $null
if (Test-Path -LiteralPath $sovereigntyDir) {
  $c = @(
    Get-ChildItem -LiteralPath $sovereigntyDir -Filter 'sovereignty_validate_*.json' -File -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTimeUtc -Descending
  )
  if ($c.Count -gt 0) { $sovereigntyJson = $c[0].FullName }
}

# Identity sources
$folderName = Split-Path -Leaf $cycleRootPath
$folderGuid = $null
if ($folderName -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})$') {
  $folderGuid = $Matches[1]
}

$deployCycleId = $null
$deployTotalAgents = $null
if (Test-Path -LiteralPath $deploySummary) {
  try {
    $s = Read-Json $deploySummary
    if ($s.cycle_id) { $deployCycleId = [string]$s.cycle_id }
    if ($null -ne $s.total_agents) { $deployTotalAgents = [int]$s.total_agents }
  } catch {}
}

# Read first+last line of deploy.jsonl for cycle_id and monotonic ts (no full scan; supports 1M+ lines)
$deployFirstTs = $null
$deployLastTs = $null
$deployFirstCycle = $null
$deployLastCycle = $null
$deployLineCount = $deployTotalAgents

if (Test-Path -LiteralPath $deployJsonl) {
  try {
    $o = Get-Content -LiteralPath $deployJsonl -Encoding UTF8 -TotalCount 1 -ErrorAction Stop | Select-Object -First 1 | ConvertFrom-Json
    $deployFirstTs = ConvertTo-UtcDateTime ([string]$o.ts_utc)
    $deployFirstCycle = if ($o.cycle_id) { [string]$o.cycle_id } else { $null }
  } catch {}

  try {
    $o = Get-Content -LiteralPath $deployJsonl -Encoding UTF8 -Tail 1 -ErrorAction Stop | Select-Object -First 1 | ConvertFrom-Json
    $deployLastTs = ConvertTo-UtcDateTime ([string]$o.ts_utc)
    $deployLastCycle = if ($o.cycle_id) { [string]$o.cycle_id } else { $null }
  } catch {}
}

$sovereigntyOk = $null
$sovereigntyTs = $null
if ($null -ne $sovereigntyJson) {
  try {
    $sv = Read-Json $sovereigntyJson
    if ($null -ne $sv.ok) { $sovereigntyOk = [bool]$sv.ok }
    $sovereigntyTs = ConvertTo-UtcDateTime ([string]$sv.ts_utc)
  } catch {}
}

# Temporal window checks
$times = @()
foreach ($t in @($deployFirstTs, $deployLastTs, $sovereigntyTs)) { if ($t) { $times += $t } }
$windowSeconds = $null
if ($times.Count -ge 2) {
  $min = ($times | Sort-Object)[0]
  $max = ($times | Sort-Object)[-1]
  $windowSeconds = [int]([TimeSpan]($max - $min)).TotalSeconds
}

$identitySet = @(
  @($folderGuid, $deployCycleId, $deployFirstCycle, $deployLastCycle) |
    Where-Object { $_ } |
    Select-Object -Unique
)
$identityAgreement = (@($identitySet).Count -le 1)

$temporalAgreement = $true
$temporalReasons = @()
if ($deployFirstTs -and $deployLastTs -and $deployLastTs -lt $deployFirstTs) {
  $temporalAgreement = $false
  $temporalReasons += 'deploy timestamps not monotonic'
}
if ($null -ne $windowSeconds -and $windowSeconds -gt $MaxWindowSeconds) {
  $temporalAgreement = $false
  $temporalReasons += ("execution window too large: {0}s" -f $windowSeconds)
}

# Evidence checks: existence + hashes
$evidence = @()
function Add-Evidence([string]$name, [string]$path) {
  $exists = Test-Path -LiteralPath $path
  $script:evidence += [ordered]@{ name = $name; path = $path; exists = [bool]$exists; sha256 = if ($exists) { Get-Sha256 $path } else { $null } }
}

Add-Evidence -name 'deploy.jsonl' -path $deployJsonl
Add-Evidence -name 'deploy.summary.json' -path $deploySummary
if (Test-Path -LiteralPath $pentad) { Add-Evidence -name 'pentad_balance.jsonl' -path $pentad }
if ($null -ne $sovereigntyJson) { Add-Evidence -name 'sovereignty_validate.json' -path $sovereigntyJson }

$missingEvidence = @($evidence | Where-Object { -not $_.exists })
$evidenceAgreement = ($missingEvidence.Count -eq 0)

# Constitutional agreement
$constitutionalAgreement = $true
$constitutionalReasons = @()
if ($null -eq $sovereigntyOk) {
  $constitutionalAgreement = $false
  $constitutionalReasons += 'sovereignty ok flag missing'
} elseif (-not $sovereigntyOk) {
  $constitutionalAgreement = $false
  $constitutionalReasons += 'sovereignty validation failed'
}

$report = [ordered]@{
  generated_utc = (Get-Date).ToUniversalTime().ToString('o')
  cycle_root = $cycleRootPath
  identity = [ordered]@{
    folder_cycle_id = $folderGuid
    deploy_summary_cycle_id = $deployCycleId
    deploy_first_cycle_id = $deployFirstCycle
    deploy_last_cycle_id = $deployLastCycle
    unique_ids = $identitySet
    agreement = $identityAgreement
  }
  temporal = [ordered]@{
    deploy_first_ts_utc = if ($deployFirstTs) { $deployFirstTs.ToString('o') } else { $null }
    deploy_last_ts_utc = if ($deployLastTs) { $deployLastTs.ToString('o') } else { $null }
    sovereignty_ts_utc = if ($sovereigntyTs) { $sovereigntyTs.ToString('o') } else { $null }
    window_seconds = $windowSeconds
    max_window_seconds = $MaxWindowSeconds
    agreement = $temporalAgreement
    reasons = $temporalReasons
  }
  evidence = [ordered]@{
    agreement = $evidenceAgreement
    artifacts = $evidence
  }
  constitutional = [ordered]@{
    sovereignty_ok = $sovereigntyOk
    agreement = $constitutionalAgreement
    reasons = $constitutionalReasons
  }
  summary = [ordered]@{
    deploy_lines = $deployLineCount
    ok = ($identityAgreement -and $temporalAgreement -and $evidenceAgreement -and $constitutionalAgreement)
  }
}

$outDir = Join-Path $cycleRootPath 'verify'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outPath = Join-Path $outDir ("cycle_verify_{0}.json" -f (New-StampUtc))
$report | ConvertTo-Json -Depth 8 | Out-File -FilePath $outPath -Encoding utf8

$receipt = Join-Path $PSScriptRoot 'Write-Sha256-Receipt.ps1'
if (Test-Path -LiteralPath $receipt) {
  & $receipt -InputFile $outPath -OutputFile ($outPath + '.sha256') -DisplayPath (Split-Path -Leaf $outPath) | Out-Null
}

if ($EmitJson) {
  $report | ConvertTo-Json -Depth 8
} else {
  Write-Host "Verify report -> $outPath" -ForegroundColor Green
  if ($report.summary.ok) {
    Write-Host 'OK: artifacts agree' -ForegroundColor Green
  } else {
    Write-Host 'FAIL: disagreement detected' -ForegroundColor Yellow
    if (-not $identityAgreement) { Write-Host ("Identity mismatch: {0}" -f ($identitySet -join ', ')) -ForegroundColor Yellow }
    if (-not $temporalAgreement) { Write-Host ("Temporal: {0}" -f ($temporalReasons -join '; ')) -ForegroundColor Yellow }
    if (-not $evidenceAgreement) { Write-Host 'Missing evidence artifact(s)' -ForegroundColor Yellow }
    if (-not $constitutionalAgreement) { Write-Host ("Constitutional: {0}" -f ($constitutionalReasons -join '; ')) -ForegroundColor Yellow }
  }
}

if ($Gate -and (-not $report.summary.ok)) { exit 1 }
exit 0
