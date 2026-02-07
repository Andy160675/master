[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][ValidateRange(1, 2147483647)][int]$TotalAgents,
  [ValidateRange(0.1, 1000000)][double]$RatePerSecond = 15,
  [string]$CycleId = "",
  [string]$OutFile = "",
  [switch]$AuditOnly,
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

if (-not $CycleId) { $CycleId = [guid]::NewGuid().ToString() }

if (-not $OutFile) {
  $root = Join-Path $PSScriptRoot '..\..\validation\continuous_ops'
  New-Item -ItemType Directory -Force -Path $root | Out-Null
  $OutFile = Join-Path $root ("trinity_deploy_{0}_{1}.jsonl" -f (New-StampUtc), $CycleId)
}

$OutFile = (Resolve-Path -LiteralPath (Split-Path -Parent $OutFile) -ErrorAction SilentlyContinue).Path + "\\" + (Split-Path -Leaf $OutFile)
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutFile) | Out-Null

Info "High-capacity deploy (simulated)"
Info "CycleId: $CycleId"
Info "TotalAgents: $TotalAgents"
Info ("RatePerSecond: {0}" -f $RatePerSecond)
Info "OutFile: $OutFile"
if ($AuditOnly) { Info "Mode: AuditOnly (no actuation)" }

$sw = [System.Diagnostics.Stopwatch]::StartNew()

# StreamWriter for true JSONL streaming (low memory)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$writer = New-Object System.IO.StreamWriter($OutFile, $true, $utf8NoBom)

try {
  $writer.AutoFlush = $false
  $lastFlush = [DateTime]::UtcNow

  for ($i = 1; $i -le $TotalAgents; $i++) {
    $evt = [ordered]@{
      ts_utc = (Get-Date).ToUniversalTime().ToString('o')
      cycle_id = $CycleId
      agent_seq = $i
      status = 'queued'
      audit_only = [bool]$AuditOnly
    }

    $json = ($evt | ConvertTo-Json -Depth 6 -Compress)
    $writer.WriteLine($json)

    # Rate limiting by expected elapsed time
    if ($RatePerSecond -gt 0) {
      $expected = $i / $RatePerSecond
      $actual = $sw.Elapsed.TotalSeconds
      if ($actual -lt $expected) {
        $ms = [int][math]::Ceiling(($expected - $actual) * 1000)
        if ($ms -gt 0) { Start-Sleep -Milliseconds $ms }
      }
    }

    # Periodic flush (every ~1s)
    $now = [DateTime]::UtcNow
    if (($now - $lastFlush).TotalSeconds -ge 1) {
      $writer.Flush()
      $lastFlush = $now
    }
  }

  $writer.Flush()

  $summary = [ordered]@{
    ts_utc = (Get-Date).ToUniversalTime().ToString('o')
    cycle_id = $CycleId
    total_agents = $TotalAgents
    rate_per_second = $RatePerSecond
    elapsed_seconds = [math]::Round($sw.Elapsed.TotalSeconds, 3)
    out_file = $OutFile
  }

  Info ("Completed: {0} agents in {1}s" -f $TotalAgents, $summary.elapsed_seconds)
  ($summary | ConvertTo-Json -Depth 6) | Out-File -FilePath ($OutFile + '.summary.json') -Encoding utf8

} catch {
  Fail "Deploy failed: $($_.Exception.Message)"
} finally {
  try { $writer.Dispose() } catch {}
}

exit 0
