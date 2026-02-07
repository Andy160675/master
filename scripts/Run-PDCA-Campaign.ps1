param(
  [int]$Batches = 15,
  [int]$IterationsPerBatch = 10,
  [string]$OutRoot = "",
  [switch]$Offline,
  [switch]$Gated,
  [switch]$EmitAlerts,
  [int]$MaxRetries = 0,
  [int]$IntervalSeconds = 0,
  [string]$Policy = "sovereign_recursion/policy.default.json",
  [string]$Ledger = "validation/sovereign_recursion/ledger.jsonl",
  [string]$NasHost = "",
  [int]$Rating,
  [switch]$ContinueOnFail
)

$ErrorActionPreference = 'Stop'

function Resolve-RepoRoot {
  $here = (Get-Location).Path
  if (Test-Path (Join-Path $here 'sovereign_recursion')) { return $here }
  $scriptDir = Split-Path -Parent $PSCommandPath
  $root = Split-Path -Parent $scriptDir
  return $root
}

$repoRoot = Resolve-RepoRoot
Set-Location $repoRoot

$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
  throw "Expected python at $python (create .venv or update script)."
}

$resolvedOutRoot = $OutRoot
if ([string]::IsNullOrWhiteSpace($resolvedOutRoot)) {
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
  $resolvedOutRoot = Join-Path $repoRoot ("sovereign_recursion\artifacts\pdca_campaigns\campaign_${stamp}")
}
New-Item -ItemType Directory -Force -Path $resolvedOutRoot | Out-Null

$policyPath = Join-Path $repoRoot $Policy
$ledgerPath = Join-Path $repoRoot $Ledger

Write-Host "[PDCA] repoRoot=$repoRoot" -ForegroundColor Cyan
Write-Host "[PDCA] batches=$Batches iterationsPerBatch=$IterationsPerBatch" -ForegroundColor Cyan
Write-Host "[PDCA] outRoot=$resolvedOutRoot" -ForegroundColor Cyan

$offlineEnabled = $true
if ($PSBoundParameters.ContainsKey('Offline')) { $offlineEnabled = [bool]$Offline }

$gatedEnabled = $true
if ($PSBoundParameters.ContainsKey('Gated')) { $gatedEnabled = [bool]$Gated }

$emitAlertsEnabled = $true
if ($PSBoundParameters.ContainsKey('EmitAlerts')) { $emitAlertsEnabled = [bool]$EmitAlerts }

$continueOnFailEnabled = $true
if ($PSBoundParameters.ContainsKey('ContinueOnFail')) { $continueOnFailEnabled = [bool]$ContinueOnFail }

$summaryCsv = Join-Path $resolvedOutRoot 'campaign_summary.csv'

function Get-BatchDir([int]$b) {
  return (Join-Path $resolvedOutRoot ("batch_{0:D2}" -f $b))
}

function Get-BatchLoopSummaryPath([int]$b) {
  return (Join-Path (Get-BatchDir -b $b) 'loop_summary.jsonl')
}

function Test-BatchComplete([int]$b, [int]$expectedIterations) {
  $p = Get-BatchLoopSummaryPath -b $b
  if (-not (Test-Path $p)) { return $false }
  try {
    $count = (Get-Content $p | Measure-Object).Count
    return ($count -eq $expectedIterations)
  } catch {
    return $false
  }
}

function Get-BatchRc([int]$b) {
  $p = Get-BatchLoopSummaryPath -b $b
  if (-not (Test-Path $p)) { return 1 }
  try {
    $rows = Get-Content $p | ConvertFrom-Json
    $bad = ($rows | Where-Object { $_.rc -ne 0 }).Count
    if ($bad -gt 0) { return 1 }
    return 0
  } catch {
    return 1
  }
}

function Ensure-EmptyDir([string]$p) {
  if (Test-Path $p) {
    Remove-Item -Recurse -Force -Path $p
  }
  New-Item -ItemType Directory -Force -Path $p | Out-Null
}

$failed = 0
$results = @()

for ($b = 1; $b -le $Batches; $b++) {
  $batchDir = Get-BatchDir -b $b
  $complete = Test-BatchComplete -b $b -expectedIterations $IterationsPerBatch

  if ($complete) {
    $rc = Get-BatchRc -b $b
    $results += [pscustomobject]@{ batch=$b; rc=$rc; out_dir=$batchDir }
    if ($rc -ne 0) { $failed++ }
    continue
  }

  # If directory exists but incomplete, re-run it cleanly
  Ensure-EmptyDir -p $batchDir

  $pyArgs = @(
    '-m','sovereign_recursion.loop_runner',
    '--iterations',"$IterationsPerBatch",
    '--max-retries',"$MaxRetries",
    '--interval-seconds',"$IntervalSeconds",
    '--policy', $policyPath,
    '--ledger', $ledgerPath,
    '--out-root', $batchDir
  )

  if ($PSBoundParameters.ContainsKey('Rating')) { $pyArgs += @('--rating',"$Rating") }
  if (-not [string]::IsNullOrWhiteSpace($NasHost)) { $pyArgs += @('--nas-host',$NasHost) }
  if ($offlineEnabled) { $pyArgs += '--offline' }
  if ($gatedEnabled) { $pyArgs += '--gated' }
  if ($emitAlertsEnabled) { $pyArgs += '--emit-alerts' }

  Write-Host ("[PDCA] Batch {0:D2}/{1:D2} ..." -f $b, $Batches) -ForegroundColor Yellow
  & $python @pyArgs
  $rc = $LASTEXITCODE

  $results += [pscustomobject]@{ batch=$b; rc=$rc; out_dir=$batchDir }

  if ($rc -ne 0) {
    $failed++
    Write-Host ("[PDCA] Batch {0:D2} FAILED (rc={1})." -f $b, $rc) -ForegroundColor Red
    if (-not $continueOnFailEnabled) { break }
  } else {
    Write-Host ("[PDCA] Batch {0:D2} PASS." -f $b) -ForegroundColor Green
  }
}

# Regenerate summary CSV deterministically
"batch,rc,out_dir" | Set-Content -Encoding ASCII -Path $summaryCsv
foreach ($r in ($results | Sort-Object batch)) {
  "{0},{1},{2}" -f $r.batch, $r.rc, $r.out_dir | Add-Content -Encoding ASCII -Path $summaryCsv
}

Write-Host "[PDCA] Verifying ledger integrity..." -ForegroundColor Cyan
& $python -m sovereign_recursion.ledger --ledger $ledgerPath verify
$ledgerRc = $LASTEXITCODE

$final = @{
  ts_local = (Get-Date).ToString('o')
  repo_root = $repoRoot
  batches = $Batches
  iterations_per_batch = $IterationsPerBatch
  failed_batches = $failed
  out_root = $resolvedOutRoot
  ledger_path = $ledgerPath
  ledger_verify_rc = $ledgerRc
  offline = [bool]$offlineEnabled
  gated = [bool]$gatedEnabled
  emit_alerts = [bool]$emitAlertsEnabled
  continue_on_fail = [bool]$continueOnFailEnabled
}
$finalPath = Join-Path $resolvedOutRoot 'campaign_final.json'
$final | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $finalPath

Write-Host "[PDCA] Final -> $finalPath" -ForegroundColor Cyan
if ($failed -gt 0 -or $ledgerRc -ne 0) { exit 1 }
exit 0
