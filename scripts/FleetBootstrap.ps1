param(
  [string[]]$Targets = @('pc-1','pc-2','pc-3','pc-4'),
  [string]$NasRoot = "\\dxp4800plus-67ba\ops",
  [switch]$SkipNasCheck,
  [switch]$RunNow,
  [int]$SelfHealIntervalSec = 300
)

function Assert-NasAvailable {
  param(
    [Parameter(Mandatory=$true)][string]$NasRoot,
    [switch]$SkipNasCheck
  )

  if ($SkipNasCheck) {
    Write-Warning "[NAS] SkipNasCheck enabled; continuing without NAS preflight."
    return
  }

  if (-not $NasRoot.StartsWith('\\')) {
    throw "NasRoot must be a UNC path (\\\\server\\share). Got: $NasRoot"
  }

  $nasHost = ($NasRoot -split '\\')[2]
  if (-not $nasHost) {
    throw "Cannot parse NAS host from NasRoot: $NasRoot"
  }

  $pingOk = Test-Connection -ComputerName $nasHost -Count 1 -Quiet -ErrorAction SilentlyContinue
  if (-not $pingOk) {
    throw "Cannot reach NAS host '$nasHost' (ping failed). NasRoot=$NasRoot"
  }

  if (-not (Test-Path -LiteralPath $NasRoot)) {
    throw "Cannot access NAS share path. NasRoot=$NasRoot"
  }
}

Assert-NasAvailable -NasRoot $NasRoot -SkipNasCheck:$SkipNasCheck

$QueueRoot = Join-Path $NasRoot 'Queue'
$PkgRoot   = Join-Path $NasRoot 'Packages'
$CfgRoot   = Join-Path $NasRoot 'Config'

# Ensure NAS structure
New-Item -ItemType Directory -Force -Path $QueueRoot,$PkgRoot,$CfgRoot | Out-Null

# Package current scripts into a versioned folder (timestamp)
$stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$pkgName = "selfheal_$stamp"
$pkgDir = Join-Path $PkgRoot $pkgName
New-Item -ItemType Directory -Force -Path $pkgDir | Out-Null

$ws = Split-Path -Parent $PSScriptRoot
Copy-Item -Path (Join-Path $ws 'scripts\SelfHealAutomation.ps1') -Destination $pkgDir -Force
Copy-Item -Path (Join-Path $ws 'scripts\FleetPullAgent.ps1')   -Destination $pkgDir -Force
Copy-Item -Path (Join-Path $ws 'scripts\Register-SelfHeal.ps1')-Destination $pkgDir -Force
Copy-Item -Path (Join-Path $ws 'scripts\Ship-Logs.ps1')        -Destination $pkgDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $ws 'scripts\Notify-Module.psm1')   -Destination $pkgDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $ws 'scripts\Start-Collab.ps1')     -Destination $pkgDir -Force -ErrorAction SilentlyContinue
Copy-Item -Path (Join-Path $ws 'scripts\End-Collab.ps1')       -Destination $pkgDir -Force -ErrorAction SilentlyContinue

# Optional central config
$thCfg = Join-Path $CfgRoot 'ThresholdConfig.json'
if (-not (Test-Path $thCfg)) {
  '{"DiskSpaceThresholdGB":10,"CriticalServices":["Spooler","wuauserv"]}' | Set-Content -Encoding UTF8 $thCfg
}

# Queue deploy + registration + log shipper + optional one-time run
foreach ($h in $Targets) {
  $host = $h.ToLower()
  # 1) Deploy package to C:\ops
  & "$ws\scripts\Queue-Command.ps1" -Hosts $host -Type deploy -Package $pkgDir -Dest 'C:\ops'
  # 2) Sync central config
  & "$ws\scripts\Queue-Command.ps1" -Hosts $host -Type sync -Package $CfgRoot -Dest 'C:\ops\Config'
  # 3) Register tasks via inline PS
  $code = @"
  schtasks /Create /TN "SelfHeal Automation" /SC ONSTART /RU SYSTEM /RL HIGHEST /TR "powershell -NoProfile -ExecutionPolicy Bypass -File C:\ops\SelfHealAutomation.ps1 -IntervalSec $SelfHealIntervalSec" /F
  schtasks /Create /TN "Fleet Pull Agent" /SC ONSTART /RU SYSTEM /RL HIGHEST /TR "powershell -NoProfile -ExecutionPolicy Bypass -File C:\ops\FleetPullAgent.ps1" /F
  schtasks /Create /TN "Ship Logs Nightly" /SC DAILY /ST 02:10 /RU SYSTEM /RL HIGHEST /TR "powershell -NoProfile -ExecutionPolicy Bypass -File C:\ops\Ship-Logs.ps1" /F
"@
  & "$ws\scripts\Queue-Command.ps1" -Hosts $host -Code $code | Out-Null
  # 4) First run (optional)
  if ($RunNow) {
    & "$ws\scripts\Queue-Command.ps1" -Hosts $host -Type run -Script 'C:\ops\SelfHealAutomation.ps1' -Args -Once | Out-Null
  }
}

Write-Host "Bootstrapped package $pkgName to: $($Targets -join ', ')"
