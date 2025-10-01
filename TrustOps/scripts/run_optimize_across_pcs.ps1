<#!
Run Optimization Across PCs (Windows domain/workgroup, PowerShell 5.1)

Pre-reqs:
 - Admin credentials on target PCs
 - File and Printer Sharing enabled (for ADMIN$), Task Scheduler service running
 - PowerShell remoting optional; this script uses SMB + schtasks for broad compatibility

Inputs:
 - A list of target computer names (CSV or inline array)
 - Credentials (Get-Credential)
 - Flags passed through to dev_optimize.ps1

Behavior:
 - Copies dev_optimize.ps1 to target ADMIN$ share
 - Creates a one-shot scheduled task to run it elevated with switches
 - Monitors task completion and logs result per machine

Examples:
  .\run_optimize_across_pcs.ps1 -Computers @('PC1','PC2') -SetLongPaths -ApplyLiveShareVSCode -WhatIf
  .\run_optimize_across_pcs.ps1 -ComputersCsv .\pcs.csv -SetLongPaths -SetPowerPlan -CleanCaches
!#>

[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
param(
  [string[]]$Computers,
  [string]$ComputersCsv,
  [switch]$SetLongPaths,
  [switch]$SetPowerPlan,
  [switch]$CleanCaches,
  [switch]$ApplyLiveShareVSCode,
  [switch]$ApplyLiveShareVS,
  [string]$VSIXPathVS,
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Note($m) { Write-Host "[orchestrator] $m" }

function Resolve-Computers {
  if ($ComputersCsv) {
    if (-not (Test-Path -LiteralPath $ComputersCsv)) { throw "ComputersCsv not found: $ComputersCsv" }
    $rows = Import-Csv -LiteralPath $ComputersCsv
    $list = @()
    foreach ($r in $rows) {
      $name = $null
      if ($r.PSObject.Properties['Computer']) { $name = $r.Computer }
      elseif ($r.PSObject.Properties['Hostname']) { $name = $r.Hostname }
      elseif ($r.PSObject.Properties['Name']) { $name = $r.Name }
      if ($name) { $list += "$name" }
    }
    return $list
  }
  return @($Computers)
}

[CmdletBinding(SupportsShouldProcess=$true)]
function New-RemoteTask {
  param(
    [string]$Computer,
    [pscredential]$Cred,
    [string]$ScriptRemotePath,
    [string]$ArgsLine
  )
  $taskName = 'DevOptimize_Once'
  $cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ScriptRemotePath`" $ArgsLine"
  $createArgs = "/Create /F /RL HIGHEST /SC ONCE /ST 00:00 /TN $taskName /TR `"$cmd`""
  $runArgs = "/Run /TN $taskName"
  $queryArgs = "/Query /TN $taskName /FO LIST"

  if ($PSCmdlet.ShouldProcess($Computer, 'Create scheduled task')) {
    & schtasks.exe /S $Computer /U $Cred.UserName /P $Cred.GetNetworkCredential().Password $createArgs | Out-Null
  }
  if ($PSCmdlet.ShouldProcess($Computer, 'Run scheduled task')) {
    & schtasks.exe /S $Computer /U $Cred.UserName /P $Cred.GetNetworkCredential().Password $runArgs | Out-Null
  }

  # Wait up to 5 minutes for completion
  $deadline = (Get-Date).AddMinutes(5)
  while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
    $out = & schtasks.exe /S $Computer /U $Cred.UserName /P $Cred.GetNetworkCredential().Password $queryArgs 2>$null
    if ($out -match 'Last Run Time') {
      if ($out -match 'Last Run Result:\s+0x0') {
        return @{ Computer=$Computer; Status='Success' }
      }
    }
  }
  return @{ Computer=$Computer; Status='TimeoutOrUnknown' }
}

try {
  $targets = Resolve-Computers
  if ($targets.Count -eq 0) { throw 'No target computers provided.' }
  Write-Note ("Targets: {0}" -f ($targets -join ', '))

  $cred = Get-Credential -Message 'Enter admin credentials for target PCs'
  $localScript = Join-Path $PSScriptRoot 'dev_optimize.ps1'
  if (-not (Test-Path -LiteralPath $localScript)) { throw "dev_optimize.ps1 not found next to this script: $localScript" }

  # Build argument line for remote execution
  $argsList = @()
  if ($SetLongPaths) { $argsList += '-SetLongPaths' }
  if ($SetPowerPlan) { $argsList += '-SetPowerPlan' }
  if ($CleanCaches) { $argsList += '-CleanCaches' }
  if ($ApplyLiveShareVSCode) { $argsList += '-ApplyLiveShareVSCode' }
  if ($ApplyLiveShareVS) { $argsList += '-ApplyLiveShareVS' }
  if ($VSIXPathVS) { $argsList += ('-VSIXPathVS "{0}"' -f $VSIXPathVS) }
  if ($DryRun) { $argsList += '-DryRun' }
  $argsLine = $argsList -join ' '

  $results = @()
  foreach ($t in $targets) {
    Write-Note "Processing $t"
    $adminShare = "\\\\$t\\ADMIN$"
    $remoteDir = "$adminShare\\Temp"
    $remoteScriptPath = "$remoteDir\\dev_optimize.ps1"

    if ($PSCmdlet.ShouldProcess($t, "Copy script to $remoteScriptPath")) {
      New-Item -ItemType Directory -Force -Path $remoteDir -ErrorAction SilentlyContinue | Out-Null
      Copy-Item -LiteralPath $localScript -Destination $remoteScriptPath -Force
    }

    # The scheduled task will run from C:\Windows\Temp; ensure script exists there
    $scriptWindowsTemp = "\\\\$t\\ADMIN$\\Temp\\dev_optimize.ps1"
    if ((Test-Path -LiteralPath $scriptWindowsTemp) -and ($remoteScriptPath -ne $scriptWindowsTemp)) {
      Copy-Item -LiteralPath $remoteScriptPath -Destination $scriptWindowsTemp -Force
    }

    $res = New-RemoteTask -Computer $t -Cred $cred -ScriptRemotePath 'C:\\Windows\\Temp\\dev_optimize.ps1' -ArgsLine $argsLine
    $results += $res
  }

  Write-Output ($results | Format-Table -AutoSize | Out-String)
  Write-Note 'Done.'
} catch {
  Write-Error $_
  exit 1
}
