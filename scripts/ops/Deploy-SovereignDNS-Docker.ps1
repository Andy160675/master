[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Host,
    [string]$User = "root",
    [string]$IdentityFile = "",
    [int]$Port = 22,
    [string]$RemoteDir = "/opt/sovereign-dns",
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function Fail([string]$msg) {
    Write-Error $msg
    if ($Gate) { exit 1 }
}

function Get-SshArgs {
    $args = @(
        "-p", "$Port",
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

$sshArgs = Get-SshArgs
$target = "$User@$Host"

$bundleRoot = Join-Path $PSScriptRoot "..\\..\\services\\sovereign_dns"
try { $bundleRoot = (Resolve-Path -LiteralPath $bundleRoot).Path } catch {}

if (-not (Test-Path -LiteralPath $bundleRoot)) {
    Fail "Bundle not found: $bundleRoot"
    exit 0
}

Write-Host "[Deploy-SovereignDNS] Host: $Host" -ForegroundColor Cyan
Write-Host "[Deploy-SovereignDNS] RemoteDir: $RemoteDir" -ForegroundColor Cyan
Write-Host "[Deploy-SovereignDNS] Bundle: $bundleRoot" -ForegroundColor Cyan

# 1) Create remote dir
& ssh @sshArgs $target "mkdir -p '$RemoteDir' && mkdir -p '$RemoteDir/data/unbound_logs'"
if ($LASTEXITCODE -ne 0) { Fail "ssh mkdir failed (exit $LASTEXITCODE)"; exit 0 }

# 2) Copy bundle
# scp on Windows sometimes needs forward slashes; keep paths quoted.
& scp @sshArgs -r "$bundleRoot/*" "$target:$RemoteDir/"
if ($LASTEXITCODE -ne 0) { Fail "scp failed (exit $LASTEXITCODE)"; exit 0 }

# 3) Bring it up (docker compose preferred)
$upCmd = @(
    "cd '$RemoteDir'",
    "(docker compose version >/dev/null 2>&1 && docker compose up -d) || (docker-compose up -d)"
) -join " && "

& ssh @sshArgs $target $upCmd
if ($LASTEXITCODE -ne 0) { Fail "docker compose up failed (exit $LASTEXITCODE)"; exit 0 }

# 4) Show status
$statusCmd = @(
    "cd '$RemoteDir'",
    "(docker compose ps 2>/dev/null || docker-compose ps 2>/dev/null || true)",
    "(ls -la '$RemoteDir/data' 2>/dev/null || true)"
) -join " && "

& ssh @sshArgs $target $statusCmd
if ($LASTEXITCODE -ne 0) { Fail "status check failed (exit $LASTEXITCODE)"; exit 0 }

Write-Host "[Deploy-SovereignDNS] Deployed. Verify port 53 from a client." -ForegroundColor Green
exit 0
