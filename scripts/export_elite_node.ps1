Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

param(
    [Parameter(Mandatory = $false)]
    [string]$Destination = 'ELITE_NODE_V1'
)

$repoRoot = (Get-Location).Path
$destPath = Join-Path $repoRoot $Destination

if (Test-Path $destPath) {
    Write-Host "DEST_EXISTS=$destPath"
} else {
    New-Item -ItemType Directory -Path $destPath | Out-Null
    Write-Host "DEST_CREATED=$destPath"
}

# Minimal, boring replication export: exclude VCS + venvs + runtime/build noise.
$excludeDirs = @(
    '.git',
    '.venv',
    'env',
    '__pycache__',
    '.pytest_cache',
    'node_modules',
    '.vs',
    'obj',
    'bin',
    'logs',
    'evidence',
    'Governance\\Logs',
    'data',
    'reports'
)

$excludeFiles = @(
    '*.pyc',
    '*.pdb',
    '*.obj',
    '*.ilk'
)

# Mirror-like copy without deleting destination extras.
# /E: copy subdirs incl empty
# /R:1 /W:1: fast fail
# /NFL /NDL /NJH /NJS: quieter output
$robocopyArgs = @(
    $repoRoot,
    $destPath,
    '/E',
    '/R:1',
    '/W:1',
    '/NFL',
    '/NDL',
    '/NJH',
    '/NJS',
    '/XD'
) + $excludeDirs + @('/XF') + $excludeFiles

Write-Host "EXPORT_FROM=$repoRoot"
Write-Host "EXPORT_TO=$destPath"

& robocopy @robocopyArgs | Out-Host

# Robocopy returns codes >= 8 on failure.
if ($LASTEXITCODE -ge 8) {
    throw "Robocopy failed with exit code $LASTEXITCODE"
}

Write-Host "EXPORT_OK=1"
Write-Host "NEXT_STEPS:"
Write-Host "  cd $Destination"
Write-Host "  py -3.11 -m venv .venv"
Write-Host "  .\\.venv\\Scripts\\python.exe agents\\orchestration\\agent_runner.py"
