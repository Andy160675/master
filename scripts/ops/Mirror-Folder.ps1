[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Source,
    [Parameter(Mandatory=$true)][string]$Destination,
    [ValidateSet('Copy','Mirror')][string]$Mode = 'Copy',
    [string[]]$ExcludeDirs = @(),
    [string[]]$ExcludeFiles = @(),
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$p) {
    if (-not (Test-Path -LiteralPath $p)) {
        New-Item -ItemType Directory -Force -Path $p | Out-Null
    }
}

$src = $Source
$dst = $Destination

try { $src = (Resolve-Path -LiteralPath $src).Path } catch {}
try { $dst = (Resolve-Path -LiteralPath $dst).Path } catch {}

if (-not (Test-Path -LiteralPath $src)) {
    throw "Source not found: $src"
}

Ensure-Dir $dst

$robocopyArgs = New-Object System.Collections.Generic.List[string]
$robocopyArgs.Add($src)
$robocopyArgs.Add($dst)

# Copy semantics
$robocopyArgs.Add('/E')           # include subdirs (including empty)
$robocopyArgs.Add('/COPY:DAT')    # data, attributes, timestamps
$robocopyArgs.Add('/DCOPY:T')
$robocopyArgs.Add('/R:2')
$robocopyArgs.Add('/W:1')
$robocopyArgs.Add('/NFL')
$robocopyArgs.Add('/NDL')
$robocopyArgs.Add('/NP')
$robocopyArgs.Add('/XJ')          # avoid junction loops

if ($Mode -eq 'Mirror') {
    # Mirror semantics (deletes extras in Destination)
    $robocopyArgs.Add('/MIR')
}

if ($ExcludeDirs.Count -gt 0) {
    $robocopyArgs.Add('/XD')
    foreach ($d in $ExcludeDirs) {
        if (-not $d) { continue }

        # Robocopy /XD behaves best with full paths. If user provided a simple
        # folder name (e.g. 'env', '.git'), treat it as relative to source.
        $xd = $d
        if (-not [System.IO.Path]::IsPathRooted($d)) {
            $xd = Join-Path $src $d
        }

        $robocopyArgs.Add($xd)
    }
}

if ($ExcludeFiles.Count -gt 0) {
    $robocopyArgs.Add('/XF')
    foreach ($f in $ExcludeFiles) { if ($f) { $robocopyArgs.Add($f) } }
}

Write-Host "[Mirror-Folder] Source:      $src"
Write-Host "[Mirror-Folder] Destination: $dst"
Write-Host "[Mirror-Folder] Mode:        $Mode"

& robocopy @robocopyArgs
$rc = $LASTEXITCODE

# Robocopy exit codes: 0-7 are success-ish; 8+ indicates failure.
$ok = ($rc -lt 8)

if (-not $ok) {
    Write-Error "Robocopy failed with exit code $rc"
    if ($Gate) { exit 1 }
}

Write-Host "[Mirror-Folder] Completed (robocopy exit code: $rc)"
exit 0
