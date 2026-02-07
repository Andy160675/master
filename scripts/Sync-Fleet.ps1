[CmdletBinding()]
param(
  [string]$Targets = "",
  [string]$NasRoot = "\\dxp4800plus-67ba\ops",
  [string]$QueueRoot = "",
  [string]$PackageRoot = "",
  [string]$Dest = "C:\ops\master_sync",
  [int]$WaitSeconds = 120,
  [switch]$PromptForCredential,
  [string]$NasDriveName = 'OPSN',
  [switch]$Confirm,
  [switch]$Gate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL] $m" -ForegroundColor Red }

function ConvertTo-TargetList([string]$s) {
  if (-not $s) { return @() }
  return @($s -split '[,;\s]+' | Where-Object { $_ -and $_.Trim().Length -gt 0 } | ForEach-Object { $_.Trim() })
}

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

function Get-NasAccess([string]$Path, [switch]$PromptForCredential, [string]$DriveName) {
  if (-not $Path.StartsWith('\\')) { return @{ effective = $Path; drive = $null } }
  if (-not $PromptForCredential) { return @{ effective = $Path; drive = $null } }

  $unc = Split-UncShareAndSubpath $Path
  $share = $unc.share
  $sub = $unc.subpath

  Info ("Mounting NAS share {0} as PSDrive '{1}'" -f $share, ($DriveName + ':'))
  $cred = Get-Credential -Message "Enter credentials to access $share"

  try {
    $existing = Get-PSDrive -Name $DriveName -ErrorAction SilentlyContinue
    if ($existing) { Remove-PSDrive -Name $DriveName -Force -ErrorAction SilentlyContinue }
  } catch {}

  New-PSDrive -Name $DriveName -PSProvider FileSystem -Root $share -Credential $cred -Scope Script | Out-Null
  $driveRoot = ($DriveName + ':')
  $effective = if ($sub) { Join-Path $driveRoot $sub } else { $driveRoot }
  return @{ effective = $effective; drive = $DriveName }
}

# Derive defaults from command-center config when Targets not specified
if (-not $Targets -or $Targets.Trim().Length -eq 0) {
  $ccCfg = "C:\PrecisePointway\config\command-center.json"
  if (Test-Path -LiteralPath $ccCfg) {
    try {
      $cfg = Get-Content -LiteralPath $ccCfg -Encoding UTF8 | ConvertFrom-Json
      if ($cfg.nas_root) { $NasRoot = [string]$cfg.nas_root }
      if ($cfg.fleet_pcs) { $Targets = (($cfg.fleet_pcs | ForEach-Object { "$_" }) -join ',') }
      Info "Loaded targets from command-center config: $ccCfg"
    } catch {
      Warn "Failed reading $ccCfg; continuing with defaults. $_"
    }
  }
}

$targetList = @(ConvertTo-TargetList $Targets)
if ($targetList.Count -eq 0) { throw "No targets specified (pass -Targets or ensure command-center config exists)." }

$queueRootResolved = if ($QueueRoot) { $QueueRoot } else { Join-Path $NasRoot 'Queue' }
$packageRootResolved = if ($PackageRoot) { $PackageRoot } else { Join-Path $NasRoot 'Packages' }

# If NAS paths require auth, mount once and rewrite roots to drive-based paths
$nas1 = Get-NasAccess -Path $queueRootResolved -PromptForCredential:$PromptForCredential -DriveName $NasDriveName
$queueRootEffective = $nas1.effective

$nas2 = Get-NasAccess -Path $packageRootResolved -PromptForCredential:$PromptForCredential -DriveName $NasDriveName
$packageRootEffective = $nas2.effective

# Workspace root is parent of scripts/
$workspaceRoot = Resolve-Path (Join-Path $PSScriptRoot '..')

$stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$pkgName = "master_sync_$stamp"
$pkgDir = Join-Path $packageRootEffective $pkgName

$validationDir = Join-Path $workspaceRoot 'validation\fleet_sync'
New-Item -ItemType Directory -Force -Path $validationDir | Out-Null
$planPath = Join-Path $validationDir "plan_${stamp}.json"

$allow = @(
  'scripts',
  'services\sovereign_dns',
  'docs\ops',
  'constitution',
  'secure_cloud',
  '.vscode\tasks.json',
  'CSS-ARCH-DOC-001.md',
  'CSS-GOV-DOC-002.md',
  'GOVERNANCE.md',
  'README.md',
  'SOVEREIGN_MODEL_POLICY.md',
  'SOVEREIGN_NODE_LAW.md'
)

$plan = [ordered]@{
  ts = (Get-Date).ToString('o')
  nasRoot = $NasRoot
  queueRoot = $queueRootResolved
  packageRoot = $packageRootResolved
  queueRootEffective = $queueRootEffective
  packageRootEffective = $packageRootEffective
  targets = $targetList
  dest = $Dest
  pkgName = $pkgName
  pkgDir = $pkgDir
  allowlist = $allow
  waitSeconds = $WaitSeconds
}

($plan | ConvertTo-Json -Depth 8) | Set-Content -Encoding UTF8 $planPath
Info "Wrote plan: $planPath"

if (-not $Confirm) {
  Warn "Viewer-only mode (no -Confirm). No deployment queued."
  Warn "Re-run with -Confirm to build package and queue deploy."
  exit 0
}

# Ensure roots exist
New-Item -ItemType Directory -Force -Path $queueRootEffective,$packageRootEffective | Out-Null
New-Item -ItemType Directory -Force -Path $pkgDir | Out-Null

Info "Building package at: $pkgDir"
foreach ($rel in $allow) {
  $src = Join-Path $workspaceRoot $rel
  $dst = Join-Path $pkgDir $rel

  if (Test-Path -LiteralPath $src) {
    if ((Get-Item -LiteralPath $src).PSIsContainer) {
      New-Item -ItemType Directory -Force -Path $dst | Out-Null
      $rc = Start-Process -FilePath robocopy -ArgumentList @(
        "$src",
        "$dst",
        '/E',
        '/R:2',
        '/W:2',
        '/NFL',
        '/NDL',
        '/NP'
      ) -PassThru -Wait -WindowStyle Hidden
      if ($rc.ExitCode -ge 8) { throw "robocopy failed for $rel (exit=$($rc.ExitCode))" }
    } else {
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
      Copy-Item -LiteralPath $src -Destination $dst -Force
    }
  } else {
    Warn "Missing allowlist path: $rel"
  }
}

# Queue deploy + a lightweight docker health probe on each node
$deployId = [guid]::NewGuid().ToString()
$probeId = [guid]::NewGuid().ToString()

function Write-QueueFile([string]$TargetName, [hashtable]$Cmd, [string]$Id) {
  $dir = Join-Path $queueRootEffective ($TargetName.ToLower())
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $file = Join-Path $dir ("command_" + $Id + ".json")
  ($Cmd | ConvertTo-Json -Depth 10) | Set-Content -Encoding UTF8 $file
  return $file
}

$deployCmd = [ordered]@{ id = $deployId; type = 'deploy'; package = $pkgDir; dest = $Dest }

# Probe writes to C:\ops\logs\docker_probe.jsonl
$probeCode = @'
$ErrorActionPreference = "Continue"
$logDir = "C:\ops\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logPath = Join-Path $logDir "docker_probe.jsonl"
function Emit($level,$msg,$data){
  $evt=[ordered]@{ ts=(Get-Date).ToString('o'); host=$env:COMPUTERNAME; level=$level; msg=$msg; data=$data }
  Add-Content -Path $logPath -Value (($evt|ConvertTo-Json -Depth 8 -Compress))
}
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker){ Emit 'Warn' 'docker cli missing' @{}; exit 0 }
$outV = ((& docker version 2>&1) | Out-String).Trim(); $ecV=$LASTEXITCODE
$outI = ((& docker info 2>&1) | Out-String).Trim(); $ecI=$LASTEXITCODE
Emit 'Info' 'docker version' @{ exit=$ecV; output=$outV }
Emit 'Info' 'docker info' @{ exit=$ecI; output=$outI }
'@

$probeCmd = [ordered]@{ id = $probeId; type = 'ps'; code = $probeCode }

$receipts = @()
foreach ($h in $targetList) {
  $p1 = Write-QueueFile -TargetName $h -Cmd $deployCmd -Id $deployId
  Info "Queued deploy for $h -> $p1"
  $p2 = Write-QueueFile -TargetName $h -Cmd $probeCmd -Id $probeId
  Info "Queued docker probe for $h -> $p2"
  $receipts += [ordered]@{ host=$h; deploy=$p1; probe=$p2 }
}

$receiptPath = Join-Path $validationDir "receipt_${stamp}.json"
([ordered]@{ plan=$planPath; deployId=$deployId; probeId=$probeId; queued=$receipts } | ConvertTo-Json -Depth 10) | Set-Content -Encoding UTF8 $receiptPath
Info "Wrote receipt: $receiptPath"

if ($WaitSeconds -le 0) { exit 0 }

Info "Waiting up to $WaitSeconds seconds for .done receipts (deploy + probe) ..."
$deadline = (Get-Date).AddSeconds($WaitSeconds)
$pending = [System.Collections.Generic.HashSet[string]]::new()
foreach ($h in $targetList) {
  $pending.Add("$h|$deployId") | Out-Null
  $pending.Add("$h|$probeId") | Out-Null
}

while ($pending.Count -gt 0 -and (Get-Date) -lt $deadline) {
  foreach ($key in @($pending)) {
    $parts = $key -split '\|'
    $h = $parts[0]
    $id = $parts[1]
    $done = Join-Path (Join-Path $queueRootEffective ($h.ToLower())) ("command_" + $id + ".done.json")
    if (Test-Path -LiteralPath $done) {
      $pending.Remove($key) | Out-Null
      Info "Done: $h id=$id -> $done"
    }
  }
  if ($pending.Count -gt 0) { Start-Sleep -Seconds 1 }
}

if ($pending.Count -gt 0) {
  $msg = "Timed out waiting for: $($pending | Sort-Object | ForEach-Object { $_ } -join ', ')"
  if ($Gate) { Fail $msg; exit 1 }
  Warn $msg
} else {
  Info "All receipts present. If Ship-Logs is enabled, review: \\dxp4800plus-67ba\ops\logs\<HOST>\docker_probe.jsonl"
}
