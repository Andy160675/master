[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$HostName,
  [Parameter(Mandatory = $true)][string]$User,
  [string]$IdentityFile = "",
  [int]$Port = 22,
  [switch]$UseSudo,
  [switch]$Gate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL] $m" -ForegroundColor Red }

function Invoke-Ssh([string]$Command) {
  $target = "$User@$HostName"
  $sshArguments = @(
    '-o', 'BatchMode=yes',
    '-o', 'StrictHostKeyChecking=accept-new',
    '-p', "$Port"
  )
  if ($IdentityFile -and $IdentityFile.Trim().Length -gt 0) {
    $sshArguments += @('-i', "$IdentityFile")
  }

  $full = @($sshArguments + @($target, $Command))
  $out = & ssh @full 2>&1
  $code = $LASTEXITCODE
  return [ordered]@{ exit = $code; output = ($out | Out-String).Trim() }
}

$workspaceRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$outDir = Join-Path $workspaceRoot 'validation\docker_fix'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')
$outPath = Join-Path $outDir ("ssh_docker_fix_${HostName}_${stamp}.json")

Info ("Checking Docker over SSH: {0}@{1}:{2}" -f $User, $HostName, $Port)

$pre = [ordered]@{
  ts = (Get-Date).ToString('o')
  host = $HostName
  user = $User
  port = $Port
  pre = [ordered]@{}
  actions = @()
  post = [ordered]@{}
}

$pre.pre.docker = Invoke-Ssh "docker version; docker info" 
$pre.pre.systemctl = Invoke-Ssh "command -v systemctl >/dev/null 2>&1 && systemctl --no-pager status docker || true"

# Try restart (best-effort, different init systems)
$restartCmd = @(
  "command -v systemctl >/dev/null 2>&1 && " + ($(if ($UseSudo) { 'sudo ' } else { '' })) + "systemctl restart docker",
  "command -v service >/dev/null 2>&1 && " + ($(if ($UseSudo) { 'sudo ' } else { '' })) + "service docker restart",
  "test -x /etc/init.d/docker && " + ($(if ($UseSudo) { 'sudo ' } else { '' })) + "/etc/init.d/docker restart"
) -join " || "

$pre.actions += [ordered]@{ kind = 'restart'; cmd = $restartCmd; result = (Invoke-Ssh $restartCmd) }

# Also check that dockerd is bound and responding
$pre.actions += [ordered]@{ kind = 'ps'; cmd = "ps aux | egrep 'dockerd|containerd' | head"; result = (Invoke-Ssh "ps aux | egrep 'dockerd|containerd' | head") }

$pre.post.docker = Invoke-Ssh "docker version; docker info"
$pre.post.systemctl = Invoke-Ssh "command -v systemctl >/dev/null 2>&1 && systemctl --no-pager status docker || true"

($pre | ConvertTo-Json -Depth 10) | Set-Content -Encoding UTF8 $outPath
Info "Wrote report: $outPath"

$ok = ($pre.post.docker.exit -eq 0)
if (-not $ok) {
  $msg = "Docker over SSH still failing (exit=$($pre.post.docker.exit))."
  if ($Gate) { Fail $msg; exit 1 }
  Warn $msg
} else {
  Info "Docker over SSH looks healthy."
}
