<#!
Dev Optimization Script (Windows, PowerShell 5.1)

What it does (opt-in by switches):
 - Enable NTFS Long Paths (HKLM)           [-SetLongPaths]
 - Switch Power Plan to High/Ultimate      [-SetPowerPlan]
 - Clean common dev caches/temp            [-CleanCaches]
 - Install VS Code Live Share extension    [-ApplyLiveShareVSCode]
 - Install Visual Studio Live Share VSIX   [-ApplyLiveShareVS -VSIXPathVS <path>]

Safe defaults: No changes without explicit switches; supports -DryRun and ShouldProcess.

Examples:
  .\dev_optimize.ps1 -DryRun -SetLongPaths -SetPowerPlan -CleanCaches -ApplyLiveShareVSCode
  .\dev_optimize.ps1 -SetLongPaths -ApplyLiveShareVS -VSIXPathVS "C:\temp\LiveShare.vsix"
!#>

[CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='Medium')]
param(
  [switch]$DryRun,
  [switch]$SetLongPaths,
  [switch]$SetPowerPlan,
  [switch]$CleanCaches,
  [switch]$ApplyLiveShareVSCode,
  [switch]$ApplyLiveShareVS,
  [string]$VSIXPathVS
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Note($msg) { Write-Host "[opt] $msg" }
function Test-Admin {
  $id = [System.Security.Principal.WindowsIdentity]::GetCurrent()
  $p = New-Object System.Security.Principal.WindowsPrincipal($id)
  return $p.IsInRole([System.Security.Principal.WindowsBuiltinRole]::Administrator)
}

function Enable-LongPaths {
  if (-not $SetLongPaths) { return }
  $regPath = 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem'
  $name = 'LongPathsEnabled'
  $val = 1
  Write-Note "Enable NTFS Long Paths ($regPath\\$name=$val)"
  if ($DryRun) { return }
  if (-not (Test-Admin)) { throw 'Admin privileges required for LongPaths registry change.' }
  New-Item -Path $regPath -Force | Out-Null
  New-ItemProperty -Path $regPath -Name $name -PropertyType DWord -Value $val -Force | Out-Null
}

function Set-HighPerformancePlan {
  if (-not $SetPowerPlan) { return }
  Write-Note 'Set power plan to High/Ultimate performance if available'
  if ($DryRun) { return }
  $plans = & powercfg -L 2>$null
  if (-not $plans) { Write-Note 'powercfg not available'; return }
  $guidUltimate = ($plans | Select-String -Pattern 'Ultimate Performance' | ForEach-Object { ($_ -split '\s+')[3].Trim() }) | Select-Object -First 1
  $guidHigh = ($plans | Select-String -Pattern 'High performance' | ForEach-Object { ($_ -split '\s+')[3].Trim() }) | Select-Object -First 1
  $target = $guidUltimate
  if (-not $target) { $target = $guidHigh }
  if ($target) {
    & powercfg -S $target | Out-Null
  } else {
    Write-Note 'No High/Ultimate plan found.'
  }
}

function Remove-ItemSafe($path) {
  try { if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue } }
  catch { Write-Note "Skip remove error: $($PSItem.Exception.Message)" }
}

function Clean-DevCaches {
  if (-not $CleanCaches) { return }
  Write-Note 'Clean temp and common dev caches (npm/yarn/dotnet/nuget/pip)'
  if (-not $DryRun) {
    # Temp folders
    Remove-ItemSafe (Join-Path $env:TEMP '*')
    Remove-ItemSafe 'C:\Windows\Temp\*'
    # Recycle Bin (may not exist on ServerCore)
    try { if (Get-Command Clear-RecycleBin -ErrorAction SilentlyContinue) { Clear-RecycleBin -Force -ErrorAction SilentlyContinue } } catch {}
  }
  # dotnet nuget locals
  if (Get-Command dotnet -ErrorAction SilentlyContinue) {
    Write-Note 'dotnet nuget locals all --clear'
    if (-not $DryRun) { & dotnet nuget locals all --clear | Out-Null }
  }
  if (Get-Command nuget -ErrorAction SilentlyContinue) {
    Write-Note 'nuget locals all -clear'
    if (-not $DryRun) { & nuget locals all -clear | Out-Null }
  }
  if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Note 'npm cache clean --force'
    if (-not $DryRun) { & npm cache clean --force | Out-Null }
  }
  if (Get-Command yarn -ErrorAction SilentlyContinue) {
    Write-Note 'yarn cache clean'
    if (-not $DryRun) { & yarn cache clean | Out-Null }
  }
  if (Get-Command pip -ErrorAction SilentlyContinue) {
    Write-Note 'pip cache purge'
    if (-not $DryRun) { & pip cache purge | Out-Null }
  }
}

function Install-LiveShareVSCode {
  if (-not $ApplyLiveShareVSCode) { return }
  Write-Note 'Install VS Code Live Share (ms-vsliveshare.vsliveshare)'
  $code = Get-Command code -ErrorAction SilentlyContinue
  if (-not $code) { Write-Note 'VS Code CLI (code) not found in PATH; skipping.'; return }
  if ($DryRun) { return }
  & $code.Source --install-extension ms-vsliveshare.vsliveshare --force | Out-Null
}

function Install-LiveShareVS {
  if (-not $ApplyLiveShareVS) { return }
  if (-not $VSIXPathVS) { Write-Note 'VSIXPathVS not provided; skipping Visual Studio Live Share.'; return }
  $vsix = Resolve-Path -LiteralPath $VSIXPathVS -ErrorAction SilentlyContinue
  if (-not $vsix) { Write-Note "VSIX not found: $VSIXPathVS"; return }
  Write-Note "Install Visual Studio Live Share from VSIX: $($vsix.Path)"
  if ($DryRun) { return }
  # Try vsixinstaller.exe discovery
  $installerCandidates = @(
    'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vsixinstaller.exe',
    'C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\VSIXInstaller.exe',
    'C:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\VSIXInstaller.exe',
    'C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\VSIXInstaller.exe'
  )
  $inst = $installerCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  if (-not $inst) { Write-Note 'VSIXInstaller.exe not found; please install Visual Studio first or provide installer path.'; return }
  & $inst /quiet $vsix.Path | Out-Null
}

Write-Note ('DryRun: {0}' -f ($DryRun.IsPresent))
Enable-LongPaths
Set-HighPerformancePlan
Clean-DevCaches
Install-LiveShareVSCode
Install-LiveShareVS

Write-Note 'Optimization script finished.'