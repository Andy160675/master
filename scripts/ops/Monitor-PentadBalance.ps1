[CmdletBinding()]
param(
  [string]$OutFile = "",
  [ValidateRange(1, 3600)][int]$IntervalSeconds = 30,
  [switch]$Once,
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

if (-not $OutFile) {
  $root = Join-Path $PSScriptRoot '..\..\validation\continuous_ops'
  New-Item -ItemType Directory -Force -Path $root | Out-Null
  $OutFile = Join-Path $root ("pentad_balance_{0}.jsonl" -f (New-StampUtc))
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutFile) | Out-Null

function Get-CpuPercent {
  try {
    $v = (Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction Stop).CounterSamples[0].CookedValue
    return [math]::Round([double]$v, 2)
  } catch { return $null }
}

function Get-MemoryInfo {
  try {
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
    $totalKb = [double]$os.TotalVisibleMemorySize
    $freeKb = [double]$os.FreePhysicalMemory
    $usedKb = $totalKb - $freeKb
    return [ordered]@{
      total_mb = [math]::Round($totalKb / 1024, 1)
      free_mb  = [math]::Round($freeKb / 1024, 1)
      used_mb  = [math]::Round($usedKb / 1024, 1)
      used_pct = if ($totalKb -gt 0) { [math]::Round(($usedKb / $totalKb) * 100, 2) } else { $null }
    }
  } catch { return $null }
}

function Get-DiskInfo {
  $drives = @()
  try {
    $drives = Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue | Where-Object { $_.Free -is [long] -and $_.Used -is [long] }
  } catch {}

  $out = @()
  foreach ($d in $drives) {
    $total = $d.Used + $d.Free
    $out += [ordered]@{
      name = $d.Name
      free_gb = [math]::Round($d.Free / 1GB, 2)
      total_gb = [math]::Round($total / 1GB, 2)
      free_pct = if ($total -gt 0) { [math]::Round(($d.Free / $total) * 100, 2) } else { $null }
      root = $d.Root
    }
  }
  return $out
}

function Get-DockerSummary {
  $docker = Get-Command docker -ErrorAction SilentlyContinue
  if (-not $docker) { return [ordered]@{ ok = $false; detail = 'docker not found' } }

  try {
    $ps = ((& docker ps --format "{{.ID}} {{.Image}} {{.Status}}" 2>&1) | Out-String).Trim()
    return [ordered]@{ ok = $true; ps = $ps }
  } catch {
    return [ordered]@{ ok = $false; detail = $_.Exception.Message }
  }
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$writer = New-Object System.IO.StreamWriter($OutFile, $true, $utf8NoBom)

try {
  Info "Monitor-PentadBalance -> $OutFile"

  while ($true) {
    $evt = [ordered]@{
      ts_utc = (Get-Date).ToUniversalTime().ToString('o')
      host = $env:COMPUTERNAME
      cpu_pct = (Get-CpuPercent)
      memory = (Get-MemoryInfo)
      disks = (Get-DiskInfo)
      docker = (Get-DockerSummary)
    }

    $writer.WriteLine(($evt | ConvertTo-Json -Depth 8 -Compress))
    $writer.Flush()

    if ($Once) { break }
    Start-Sleep -Seconds $IntervalSeconds
  }

} catch {
  Fail "Monitor error: $($_.Exception.Message)"
} finally {
  try { $writer.Dispose() } catch {}
}

exit 0
