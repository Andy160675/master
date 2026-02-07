[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Targets,
  [string]$QueueRoot = "\\dxp4800plus-67ba\ops\Queue",
  [int]$WaitSeconds = 0,
  [switch]$PromptForCredential,
  [string]$QueueDriveName = 'OPSQ',
  [switch]$Gate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err($m) { Write-Host "[FAIL] $m" -ForegroundColor Red }

function ConvertTo-Targets([string]$s) {
  $out = @()
  ($s -split '[,;\s]+' | Where-Object { $_ -and $_.Trim().Length -gt 0 }) | ForEach-Object { $out += $_.Trim() }
  return $out
}

$hosts = @(ConvertTo-Targets $Targets)
if ($hosts.Count -eq 0) { throw "No targets parsed from: $Targets" }

function Split-UncShareAndSubpath([string]$UncPath) {
  # Returns @{ share='\\server\share'; subpath='optional\path' }
  if (-not $UncPath.StartsWith('\\')) { throw "Not a UNC path: $UncPath" }
  $parts = $UncPath.TrimEnd('\') -split '\\' | Where-Object { $_ -ne '' }
  if ($parts.Count -lt 2) { throw "Invalid UNC path: $UncPath" }
  $share = "\\$($parts[0])\$($parts[1])"
  $sub = ''
  if ($parts.Count -gt 2) { $sub = ($parts[2..($parts.Count-1)] -join '\') }
  return @{ share = $share; subpath = $sub }
}

$queueRootEffective = $QueueRoot
if ($PromptForCredential -and $QueueRoot.StartsWith('\\')) {
  $unc = Split-UncShareAndSubpath $QueueRoot
  $share = $unc.share
  $sub = $unc.subpath

  Write-Info "QueueRoot is UNC and PromptForCredential set. Mounting $share as PSDrive '$QueueDriveName:'"
  $cred = Get-Credential -Message "Enter credentials to access $share"

  # Replace any existing drive with the same name
  try {
    $existing = Get-PSDrive -Name $QueueDriveName -ErrorAction SilentlyContinue
    if ($existing) { Remove-PSDrive -Name $QueueDriveName -Force -ErrorAction SilentlyContinue }
  } catch {}

  New-PSDrive -Name $QueueDriveName -PSProvider FileSystem -Root $share -Credential $cred -Scope Script | Out-Null
  $queueRootEffective = if ($sub) { Join-Path ("$QueueDriveName`:") $sub } else { "$QueueDriveName`:" }
  Write-Info "Using QueueRoot via PSDrive: $queueRootEffective"
}

$workspaceRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$outDir = Join-Path $workspaceRoot 'validation\docker_fix'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$cmdId = [guid]::NewGuid().ToString()

# Inline code executed on each Windows node by FleetPullAgent (runs hidden).
# Writes JSONL events to C:\ops\logs\docker_fix.jsonl (shipped nightly if Ship-Logs is installed).
$code = @'
$ErrorActionPreference = "Continue"

$logDir = "C:\ops\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logPath = Join-Path $logDir "docker_fix.jsonl"

function Emit([string]$Level, [string]$Message, $Data) {
  try {
    $evt = [ordered]@{
      ts    = (Get-Date).ToString('o')
      host  = $env:COMPUTERNAME
      level = $Level
      msg   = $Message
      data  = $Data
    }
    Add-Content -Path $logPath -Value (($evt | ConvertTo-Json -Depth 8 -Compress))
  } catch {
    # last-ditch: ignore logging failures
  }
}

function Get-ServiceInfo([string]$Name) {
  try {
    $svc = Get-Service -Name $Name -ErrorAction Stop
    $startMode = $null
    try {
      $wmi = Get-CimInstance Win32_Service -Filter "Name='$Name'" -ErrorAction Stop
      $startMode = $wmi.StartMode
    } catch {}

    return [ordered]@{ name = $Name; status = $svc.Status.ToString(); startMode = $startMode }
  } catch {
    return $null
  }
}

function Try-Run([string]$Label, [scriptblock]$Action) {
  try {
    & $Action
    Emit "Info" "action-ok: $Label" @{ }
    return $true
  } catch {
    Emit "Warn" "action-failed: $Label" @{ error = "$_" }
    return $false
  }
}

Emit "Info" "DockerFix start" @{ pid = $PID; user = $env:USERNAME }

$before = [ordered]@{
  dockerCli = $false
  dockerVersion = $null
  dockerInfo = $null
  composeVersion = $null
  services = @()
}

foreach ($n in @('com.docker.service', 'docker')) {
  $si = Get-ServiceInfo $n
  if ($si) { $before.services += $si }
}

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
  $before.dockerCli = $true
  $before.dockerVersion = ((& docker version 2>&1) | Out-String).Trim()
  $before.composeVersion = ((& docker compose version 2>&1) | Out-String).Trim()
  $before.dockerInfo = ((& docker info 2>&1) | Out-String).Trim()
}

Emit "Info" "DockerFix before" $before

# Preferred: Docker Desktop
$didDesktop = $false
try {
  $svc = Get-Service -Name 'com.docker.service' -ErrorAction Stop
  $didDesktop = $true
  Try-Run "restart com.docker.service" { Restart-Service -Name 'com.docker.service' -Force -ErrorAction Stop } | Out-Null
} catch {}

# Fallback: Docker Engine service
try {
  $svc = Get-Service -Name 'docker' -ErrorAction Stop
  Try-Run "restart docker" { Restart-Service -Name 'docker' -Force -ErrorAction Stop } | Out-Null
} catch {}

# WSL reset often clears hung Docker Desktop backends
try {
  $wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
  if ($wsl) {
    Try-Run "wsl --shutdown" { & wsl.exe --shutdown 2>&1 | Out-Null } | Out-Null
  }
} catch {}

Start-Sleep -Seconds 4

$after = [ordered]@{
  dockerCli = $false
  dockerVersion = $null
  dockerInfo = $null
  composeVersion = $null
  services = @()
}

foreach ($n in @('com.docker.service', 'docker')) {
  $si = Get-ServiceInfo $n
  if ($si) { $after.services += $si }
}

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if ($dockerCmd) {
  $after.dockerCli = $true
  $after.dockerVersion = ((& docker version 2>&1) | Out-String).Trim()
  $after.composeVersion = ((& docker compose version 2>&1) | Out-String).Trim()
  $after.dockerInfo = ((& docker info 2>&1) | Out-String).Trim()
}

Emit "Info" "DockerFix after" $after

if (-not $after.dockerCli) {
  Emit "Error" "DockerFix failed: docker CLI not found" @{ }
  exit 2
}

# Determine success: docker info returns 0 and includes 'Server:'
try {
  $ok = (& docker info 2>&1 | Out-String)
  if ($LASTEXITCODE -eq 0 -and $ok -match 'Server:') {
    Emit "Success" "DockerFix ok" @{ }
    exit 0
  }

  Emit "Error" "DockerFix failed: docker info nonzero" @{ exit = $LASTEXITCODE; output = $ok }
  exit 1
} catch {
  Emit "Error" "DockerFix exception" @{ error = "$_" }
  exit 1
}
'@

$cmd = [ordered]@{
  id = $cmdId
  type = 'ps'
  code = $code
}

foreach ($h in $hosts) {
  $dir = Join-Path $queueRootEffective ($h.ToLower())
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $file = Join-Path $dir ("command_" + $cmdId + ".json")
  try {
    ($cmd | ConvertTo-Json -Depth 8) | Set-Content -Encoding UTF8 $file
  } catch {
    $hint = if ($QueueRoot.StartsWith('\\') -and -not $PromptForCredential) {
      "QueueRoot is a UNC path; try re-running with -PromptForCredential or authenticate first (e.g., 'net use')."
    } else {
      ""
    }
    throw "Failed writing command for $h to $file :: $($_.Exception.Message) $hint"
  }
  Write-Info "Queued docker fix for $h (id=$cmdId) -> $file"
}

$meta = [ordered]@{
  ts = (Get-Date).ToString('o')
  id = $cmdId
  queueRoot = $QueueRoot
  targets = $hosts
  waitSeconds = $WaitSeconds
}

$metaPath = Join-Path $outDir "fleet_docker_fix_${stamp}.json"
($meta | ConvertTo-Json -Depth 6) | Set-Content -Encoding UTF8 $metaPath
Write-Info "Wrote meta: $metaPath"

if ($WaitSeconds -gt 0) {
  Write-Info "Waiting up to $WaitSeconds seconds for .done receipts..."
  $deadline = (Get-Date).AddSeconds($WaitSeconds)

  $pending = [System.Collections.Generic.HashSet[string]]::new([string[]]$hosts)

  while ($pending.Count -gt 0 -and (Get-Date) -lt $deadline) {
    foreach ($h in @($pending)) {
      $done = Join-Path (Join-Path $queueRootEffective ($h.ToLower())) ("command_" + $cmdId + ".done.json")
      if (Test-Path -LiteralPath $done) {
        $pending.Remove($h) | Out-Null
        Write-Info "Done: $h -> $done"
      }
    }
    if ($pending.Count -gt 0) { Start-Sleep -Seconds 1 }
  }

  if ($pending.Count -gt 0) {
    $msg = "Timed out waiting for: $($pending | Sort-Object | ForEach-Object { $_ } -join ', ')"
    if ($Gate) { Write-Err $msg; exit 1 }
    Write-Warn $msg
  } else {
    Write-Info "All targets reported done. Review per-node logs at: \\dxp4800plus-67ba\ops\logs\<HOST>\docker_fix.jsonl (if Ship-Logs is installed)."
  }
}
