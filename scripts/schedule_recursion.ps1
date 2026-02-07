param(
    [string]$PythonPath = "${PSScriptRoot}\..\.venv\Scripts\python.exe",
    [string]$RepoRoot = "${PSScriptRoot}\..",
    [string]$TaskName = "Sovereign Recursion Engine",
    [int]$Rating = 4,
    [string]$NasHost = "192.168.4.114",
    [switch]$Gated,
    [switch]$Offline,
    [int]$IntervalMinutes = 60
)

$ErrorActionPreference = 'Stop'

function Test-IsAdmin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) {
    Write-Host "❌ Please run as Administrator" -ForegroundColor Red
    Write-Host "   Right-click PowerShell → Run as administrator" -ForegroundColor Yellow
    exit 1
}

$python = (Resolve-Path $PythonPath).Path
$root = (Resolve-Path $RepoRoot).Path

if (-not (Test-Path $python)) {
    Write-Host "❌ Python not found: $python" -ForegroundColor Red
    exit 1
}

$argsList = @('-m','sovereign_recursion','--rating',"$Rating")
if ($NasHost) { $argsList += @('--nas-host', $NasHost) }
if ($Gated) { $argsList += '--gated' }
if ($Offline) { $argsList += '--offline' }

$argumentString = ($argsList | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } }) -join ' '

Write-Host "🚀 Scheduling: $TaskName" -ForegroundColor Cyan
Write-Host "Python: $python"
Write-Host "RepoRoot: $root"
Write-Host "Args: $argumentString"
Write-Host "IntervalMinutes: $IntervalMinutes"

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute $python -Argument $argumentString -WorkingDirectory $root

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration ([TimeSpan]::MaxValue)

$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -RestartInterval (New-TimeSpan -Minutes 1) -RestartCount 3

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "Autonomous sovereignty verification loop (repo-local)." -Force | Out-Null

Write-Host "✅ Scheduled successfully." -ForegroundColor Green
Write-Host "Run now: Start-ScheduledTask -TaskName \"$TaskName\""
Write-Host "Delete:  Unregister-ScheduledTask -TaskName \"$TaskName\""