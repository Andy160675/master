[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Host,
    [string]$User = "root",
    [string]$IdentityFile = "",
    [int]$Port = 22,
    [string]$OutDir = "${PSScriptRoot}\\..\\..\\validation\\sovereign_dns",
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function New-StampUtc { (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }

function Fail([string]$msg) {
    Write-Error $msg
    if ($Gate) { exit 1 }
}

function Get-SshArgs {
    $args = @(
        "-p", "$Port",
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=8"
    )

    if ($IdentityFile) {
        if (-not (Test-Path -LiteralPath $IdentityFile)) {
            throw "IdentityFile not found: $IdentityFile"
        }
        $args += @("-i", $IdentityFile)
    }

    return $args
}

function Invoke-Ssh([string]$cmd) {
    $sshArgs = Get-SshArgs
    $target = "$User@$Host"
    $full = @($sshArgs + @($target, $cmd))
    $out = & ssh @full 2>&1
    $code = $LASTEXITCODE
    return [pscustomobject]@{ code = $code; output = ($out | Out-String).TrimEnd() }
}

$stamp = New-StampUtc
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$report = [ordered]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    host = $Host
    user = $User
    port = $Port
    checks = @()
}

$checks = @(
    @{ name = 'whoami'; cmd = 'whoami' },
    @{ name = 'uname'; cmd = 'uname -a' },
    @{ name = 'os_release'; cmd = 'cat /etc/os-release 2>/dev/null || true' },
    @{ name = 'docker_version'; cmd = 'docker --version 2>/dev/null || true' },
    @{ name = 'docker_compose_version'; cmd = 'docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || true' },
    @{ name = 'apt_present'; cmd = 'command -v apt-get 2>/dev/null && apt-get --version | head -n 1 || true' },
    @{ name = 'opkg_present'; cmd = 'command -v opkg 2>/dev/null && opkg --version || true' },
    @{ name = 'port53_listeners'; cmd = 'ss -lntup 2>/dev/null | grep -E "\\b:53\\b" || netstat -lntup 2>/dev/null | grep -E "\\b:53\\b" || true' },
    @{ name = 'resolv_conf'; cmd = 'cat /etc/resolv.conf 2>/dev/null || true' },
    @{ name = 'disk_df'; cmd = 'df -h 2>/dev/null | head -n 20 || true' }
)

foreach ($c in $checks) {
    try {
        $r = Invoke-Ssh $c.cmd
        $report.checks += [ordered]@{
            name = $c.name
            cmd = $c.cmd
            exit_code = $r.code
            output = $r.output
        }
    } catch {
        $report.checks += [ordered]@{
            name = $c.name
            cmd = $c.cmd
            exit_code = 999
            output = "ERROR: $($_.Exception.Message)"
        }
        Fail "Preflight check failed: $($c.name)"
        if ($Gate) { exit 1 }
        break
    }
}

$outPath = Join-Path $OutDir ("dns_preflight_{0}.json" -f $stamp)
$report | ConvertTo-Json -Depth 6 | Out-File -FilePath $outPath -Encoding utf8

$receiptScript = Join-Path $PSScriptRoot 'Write-Sha256-Receipt.ps1'
if (Test-Path -LiteralPath $receiptScript) {
    & $receiptScript -InputFile $outPath -OutputFile "$outPath.sha256" -DisplayPath (Split-Path -Leaf $outPath) | Out-Null
}

Write-Host "DNS preflight report -> $outPath" -ForegroundColor Green
exit 0
