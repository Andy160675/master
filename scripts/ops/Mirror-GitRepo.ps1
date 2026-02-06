[CmdletBinding()]
param(
    [string]$SourceRepoPath = "$PSScriptRoot\\..\\..",
    [Parameter(Mandatory=$true)][string]$DestinationPath,
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function Fail([string]$msg) {
    Write-Error $msg
    if ($Gate) { exit 1 }
}

$src = $SourceRepoPath
try { $src = (Resolve-Path -LiteralPath $src).Path } catch {}

if (-not (Test-Path -LiteralPath $src)) {
    Fail "Source repo path not found: $src"
    exit 0
}

$dst = $DestinationPath

Write-Host "[Mirror-GitRepo] Source: $src"
Write-Host "[Mirror-GitRepo] Dest:   $dst"

if (-not (Test-Path -LiteralPath $dst)) {
    $parent = Split-Path -Parent $dst
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    Write-Host "[Mirror-GitRepo] Creating new mirror..."
    & git clone --mirror $src $dst
    if ($LASTEXITCODE -ne 0) { Fail "git clone --mirror failed (exit $LASTEXITCODE)"; exit 0 }

    Write-Host "[Mirror-GitRepo] Mirror created."
    exit 0
}

if (-not (Test-Path -LiteralPath (Join-Path $dst 'config'))) {
    Fail "Destination exists but does not look like a bare mirror repo: $dst"
    exit 0
}

Write-Host "[Mirror-GitRepo] Updating existing mirror..."
& git -C $dst remote update --prune
if ($LASTEXITCODE -ne 0) { Fail "git remote update failed (exit $LASTEXITCODE)"; exit 0 }

Write-Host "[Mirror-GitRepo] Mirror updated."
exit 0
