[CmdletBinding()]
param(
    [string]$RootPath = "S:\\",
    [Parameter(Mandatory=$true)][string]$NodeId,
    [string]$BaselinesSubdir = "baselines",
    [int]$MaxFiles = 5000,
    [switch]$ResolveDns,
    [switch]$EmitJson,
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

$nodeSafe = ($NodeId.Trim() -replace '[^a-zA-Z0-9_.-]', '_')

if (-not (Test-Path -LiteralPath $RootPath)) {
    throw "RootPath not found (is the share mounted?): $RootPath"
}

$publishDir = Join-Path (Join-Path $RootPath $BaselinesSubdir) $nodeSafe
New-Item -ItemType Directory -Force -Path $publishDir | Out-Null

$capScript = Join-Path $PSScriptRoot 'Capture-EvidenceBaseline.ps1'
if (-not (Test-Path -LiteralPath $capScript)) {
    throw "Missing Capture-EvidenceBaseline.ps1 at: $capScript"
}

# Exclude the publication subtree (and baselines generally) so creating baseline artifacts
# does not change the measured dataset.
$exclude = @($BaselinesSubdir)

& $capScript -RootPath $RootPath -MaxFiles $MaxFiles -OutDir $publishDir -ExcludeSubdirs $exclude -EmitJson:$EmitJson -Gate:$Gate
