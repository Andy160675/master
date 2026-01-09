Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Get-Location).Path

$pythonCandidates = @(
    (Join-Path $repoRoot '.venv\Scripts\python.exe')
    (Join-Path $repoRoot 'env\Scripts\python.exe')
)

$pythonExe = $null
foreach ($candidate in $pythonCandidates) {
    if (Test-Path $candidate) {
        $pythonExe = $candidate
        break
    }
}

if (-not $pythonExe) {
    $pythonExe = 'python'
}

Write-Host "PYTHON=$pythonExe"

& $pythonExe 'agents/orchestration/agent_runner.py'
exit $LASTEXITCODE
