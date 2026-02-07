[CmdletBinding()]
param(
  [ValidateRange(1, 2147483647)][int]$CycleAgents = 1100000,
  [ValidateRange(0.1, 1000000)][double]$RatePerSecond = 15,
  [ValidateRange(0, 500)][double]$IncreaseRunTimePercent = 0,
  [switch]$SimulationMode,
  [string]$NasRoot = "\\dxp4800plus-67ba\ops",
  [string]$NasLogsSubdir = "04_LOGS\continuous_ops",
  [switch]$PromptNasCredential,
  [ValidatePattern('^[A-Z]$')][string]$NasDriveLetter = 'O',
  [ValidateRange(0, 1000000)][int]$KeepCycles = 30,
  [ValidateRange(0, 86400)][int]$CyclePauseSeconds = 0,
  [ValidateRange(0, 1000000)][int]$MaxCycles = 0,
  [switch]$NoVerifyArtifacts,
  [switch]$ConfirmInfra,
  [switch]$Confirm,
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

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$validationRoot = Join-Path $repoRoot 'validation\continuous_ops'
New-Item -ItemType Directory -Force -Path $validationRoot | Out-Null

$deployScript = Join-Path $PSScriptRoot 'Deploy-TrinityFleet-HighCapacity.ps1'
$validateScript = Join-Path $PSScriptRoot 'validate_sovereignty.ps1'
$verifyScript = Join-Path $PSScriptRoot 'Verify-CycleArtifacts.ps1'

if (-not (Test-Path -LiteralPath $deployScript)) { throw "Missing deploy script: $deployScript" }
if (-not (Test-Path -LiteralPath $validateScript)) { throw "Missing validate script: $validateScript" }

function Get-NasLogsRoot {
  param([string]$NasRoot, [string]$Subdir, [switch]$PromptCred, [string]$DriveLetter)

  if (-not $NasRoot.StartsWith('\\')) {
    return @{ path = (Join-Path $NasRoot $Subdir); drive = $null }
  }

  if (-not $PromptCred) {
    return @{ path = (Join-Path $NasRoot $Subdir); drive = $null }
  }

  $mount = Join-Path $PSScriptRoot 'Mount-EvidenceShare.ps1'
  if (-not (Test-Path -LiteralPath $mount)) {
    throw "PromptNasCredential requested but helper missing: $mount"
  }

  & $mount -UncPath $NasRoot -DriveLetter $DriveLetter -PromptCredential -Gate:$Gate | Out-Null
  $driveRoot = ($DriveLetter + ':')
  return @{ path = (Join-Path $driveRoot $Subdir); drive = $driveRoot }
}

function Invoke-DockerBootstrap {
  param([switch]$DoIt)

  $docker = Get-Command docker -ErrorAction SilentlyContinue
  if (-not $docker) {
    Warn 'docker not found; skipping docker compose bootstrap'
    return
  }

  $startSovereign = Join-Path $PSScriptRoot 'start-sovereign.ps1'
  if ($DoIt -and (Test-Path -LiteralPath $startSovereign)) {
    Info 'Infra bootstrap: start-sovereign.ps1'
    & $startSovereign -Gate:$Gate
    return
  }

  Push-Location $repoRoot
  try {
    # Prefer docker compose, fallback to docker-compose
    $composeOk = $false
    try { & docker compose version *> $null; if ($LASTEXITCODE -eq 0) { $composeOk = $true } } catch {}

    if (-not $DoIt) {
      Info 'Infra check (viewer): docker compose ps'
      if ($composeOk) { & docker compose ps } else { & docker-compose ps }
      return
    }

    Info 'Infra bootstrap: docker compose up -d'
    if ($composeOk) { & docker compose up -d } else { & docker-compose up -d }

  } finally {
    Pop-Location
  }
}

function Copy-DirBestEffort([string]$Src, [string]$Dst) {
  New-Item -ItemType Directory -Force -Path $Dst | Out-Null
  $rc = Start-Process -FilePath robocopy -ArgumentList @(
    $Src,
    $Dst,
    '/E',
    '/R:2',
    '/W:2',
    '/NFL',
    '/NDL',
    '/NP'
  ) -PassThru -Wait -WindowStyle Hidden
  if ($rc.ExitCode -ge 8) { throw "robocopy failed (exit=$($rc.ExitCode))" }
}

function Remove-OldCycleDirs([string]$Root, [int]$Keep) {
  if ($Keep -le 0) { return }
  if (-not (Test-Path -LiteralPath $Root)) { return }

  $dirs = Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending
  if (-not $dirs) { return }

  $toDelete = $dirs | Select-Object -Skip $Keep
  foreach ($d in $toDelete) {
    try { Remove-Item -LiteralPath $d.FullName -Recurse -Force -ErrorAction SilentlyContinue } catch {}
  }
}

# Start background monitors (lightweight, best-effort)
$monitorJobs = @()
function Start-MonitorJobs([string]$cycleRoot) {
  $monitorJobs = @()

  $pentadScript = Join-Path $PSScriptRoot 'Monitor-PentadBalance.ps1'
  if (Test-Path -LiteralPath $pentadScript) {
    $pentadOut = Join-Path $cycleRoot 'pentad_balance.jsonl'
    $monitorJobs += Start-Job -Name 'pentad_balance' -ScriptBlock {
      param($scriptPath, $outFile)
      & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath -OutFile $outFile -IntervalSeconds 30
    } -ArgumentList $pentadScript, $pentadOut
  }

  $metricsScript = Join-Path $repoRoot 'scripts\Manage-Metrics.ps1'
  if (Test-Path -LiteralPath $metricsScript) {
    $metricsLog = Join-Path $cycleRoot 'monitor_metrics.log'
    $monitorJobs += Start-Job -Name 'metrics_monitor' -ScriptBlock {
      param($scriptPath, $logPath)
      while ($true) {
        try {
          & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath *>&1 | Out-File -FilePath $logPath -Append -Encoding utf8
        } catch {
          "[ERROR] $($_.Exception.Message)" | Out-File -FilePath $logPath -Append -Encoding utf8
        }
        Start-Sleep -Seconds 30
      }
    } -ArgumentList $metricsScript, $metricsLog
  }

  $docker = Get-Command docker -ErrorAction SilentlyContinue
  if ($docker) {
    $dockerLog = Join-Path $cycleRoot 'monitor_docker.jsonl'
    $monitorJobs += Start-Job -Name 'docker_monitor' -ScriptBlock {
      param($logPath)
      while ($true) {
        $evt = [ordered]@{ ts_utc = (Get-Date).ToUniversalTime().ToString('o'); kind='docker_ps'; ok=$true; output='' }
        try {
          $evt.output = ((& docker ps 2>&1) | Out-String).Trim()
        } catch {
          $evt.ok = $false
          $evt.output = $_.Exception.Message
        }
        Add-Content -Path $logPath -Value (($evt | ConvertTo-Json -Depth 6 -Compress))
        Start-Sleep -Seconds 30
      }
    } -ArgumentList $dockerLog
  }

  return ,$monitorJobs
}

function Stop-MonitorJobs($jobs) {
  foreach ($j in @($jobs)) {
    try { Stop-Job -Job $j -Force -ErrorAction SilentlyContinue } catch {}
    try { Remove-Job -Job $j -Force -ErrorAction SilentlyContinue } catch {}
  }
}

 # Compatibility / convenience:
 # -SimulationMode forces simulated execution (deploy JSONL + sovereignty validate) without requiring -Confirm,
 # and avoids infra bootstrapping.
 if ($SimulationMode) {
   $Confirm = $true
   $ConfirmInfra = $false
 }

Info 'Sovereign Continuous Controller (safe by default)'
Info "RepoRoot: $repoRoot"
Info "CycleAgents: $CycleAgents  RatePerSecond: $RatePerSecond  IncreaseRunTimePercent: $IncreaseRunTimePercent"
Info "MaxCycles: $MaxCycles (0 = infinite)"
Info "ConfirmInfra: $([bool]$ConfirmInfra)  Confirm: $([bool]$Confirm)  SimulationMode: $([bool]$SimulationMode)  Gate: $([bool]$Gate)"
Info "VerifyArtifacts: $([bool](-not $NoVerifyArtifacts))"

$effectiveRate = $RatePerSecond
if ($IncreaseRunTimePercent -gt 0) {
  $effectiveRate = $RatePerSecond / (1 + ($IncreaseRunTimePercent / 100.0))
}
Info ("EffectiveRatePerSecond: {0}" -f ([math]::Round($effectiveRate, 6)))

# Resolve NAS target for archiving
$nas = Get-NasLogsRoot -NasRoot $NasRoot -Subdir $NasLogsSubdir -PromptCred:$PromptNasCredential -DriveLetter $NasDriveLetter
$nasLogsRoot = $nas.path
Info "NAS logs root (best-effort): $nasLogsRoot"

$cycleNumber = 0

try {
  # Infra bootstrap once per controller start
  Invoke-DockerBootstrap -DoIt:$ConfirmInfra

  while ($true) {
    $cycleNumber++
    $cycleStamp = New-StampUtc
    $cycleId = [guid]::NewGuid().ToString()
    $cycleDirName = ("{0}_cycle_{1:0000}_{2}" -f $cycleStamp, $cycleNumber, $cycleId)
    $cycleRoot = Join-Path $validationRoot $cycleDirName
    New-Item -ItemType Directory -Force -Path $cycleRoot | Out-Null

    Info "=== Cycle $cycleNumber start: $cycleDirName ==="

    $monitorJobs = Start-MonitorJobs -cycleRoot $cycleRoot

    try {
      $outJsonl = Join-Path $cycleRoot 'deploy.jsonl'

      if (-not $Confirm) {
        Warn 'Viewer-only mode (no -Confirm): skipping deploy + validate'
      } else {
        & $deployScript -TotalAgents $CycleAgents -RatePerSecond $effectiveRate -CycleId $cycleId -OutFile $outJsonl -AuditOnly:$true -Gate:$Gate
        & $validateScript -OutDir (Join-Path $cycleRoot 'sovereignty') -Gate:$Gate
      }

      # Artifact verification (best-effort unless -Gate)
      if ((-not $NoVerifyArtifacts) -and $Confirm -and (Test-Path -LiteralPath $verifyScript)) {
        try {
          $verifyArgs = @(
            '-NoProfile',
            '-ExecutionPolicy',
            'Bypass',
            '-File',
            $verifyScript,
            '-CycleRoot',
            $cycleRoot
          )
          if ($Gate) { $verifyArgs += '-Gate' }
          & powershell @verifyArgs | Out-Host
          if ($LASTEXITCODE -ne 0) {
            throw "artifact verification failed (exit=$LASTEXITCODE)"
          }
        } catch {
          Warn "Artifact verification error: $($_.Exception.Message)"
          if ($Gate) { throw }
        }
      }

      # Archive to NAS (best-effort)
      try {
        New-Item -ItemType Directory -Force -Path $nasLogsRoot | Out-Null
        $dst = Join-Path $nasLogsRoot $cycleDirName
        Copy-DirBestEffort -Src $cycleRoot -Dst $dst
        Remove-OldCycleDirs -Root $nasLogsRoot -Keep $KeepCycles
        Info "Archived cycle -> $dst"
      } catch {
        Warn "NAS archive failed (best-effort): $($_.Exception.Message)"
      }

      Remove-OldCycleDirs -Root $validationRoot -Keep $KeepCycles

    } finally {
      Stop-MonitorJobs -jobs $monitorJobs
    }

    Info "=== Cycle $cycleNumber end ==="

    if ($MaxCycles -gt 0 -and $cycleNumber -ge $MaxCycles) {
      Info "MaxCycles reached ($MaxCycles). Exiting."
      break
    }

    if ($CyclePauseSeconds -gt 0) {
      Info "Sleeping $CyclePauseSeconds seconds"
      Start-Sleep -Seconds $CyclePauseSeconds
    }
  }

} catch {
  Fail "Controller stopped due to error: $($_.Exception.Message)"
} finally {
  # best-effort cleanup
  try { Stop-MonitorJobs -jobs $monitorJobs } catch {}
}

exit 0
