param(
  [int]$MonteCarloN = 1000
)
$ErrorActionPreference = 'Stop'

function New-Dir($p){ if (-not [string]::IsNullOrWhiteSpace($p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }

function Invoke-LoggedNative(
  [Parameter(Mandatory=$true)][string]$Exe,
  [Parameter(Mandatory=$true)][string[]]$Args,
  [Parameter(Mandatory=$true)][string]$OutFile
){
  $prev = $ErrorActionPreference
  try {
    # Windows PowerShell surfaces native stderr as ErrorRecord(s). With $ErrorActionPreference='Stop'
    # that becomes terminating and prevents us from writing the log file.
    $ErrorActionPreference = 'Continue'
    & $Exe @Args 2>&1 |
      ForEach-Object { $_.ToString() } |
      Tee-Object -FilePath $OutFile |
      Out-Null
    return $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $prev
  }
}

$ws = Split-Path -Parent $PSScriptRoot
$runRoot = Join-Path $ws 'Data/test_runs'
New-Dir $runRoot
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runDir = Join-Path $runRoot $stamp
New-Dir $runDir

$python = Join-Path $ws '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = 'python' }

$deterministicModule = 'agi.tests.deterministic.test_cases'
$monteModule = 'agi.tests.monte_carlo.run_redteam'
$fuzzModule = 'agi.tests.fuzz.run_dep_fuzz'

Write-Host "[RUN] Deterministic" -ForegroundColor Cyan
$detRc = Invoke-LoggedNative -Exe $python -Args @('-m', $deterministicModule) -OutFile (Join-Path $runDir 'deterministic.out')
if ($detRc -ne 0) { Write-Host "[FAIL] Deterministic tests" -ForegroundColor Red }

Write-Host "[RUN] Monte Carlo ($MonteCarloN)" -ForegroundColor Cyan
$env:MC_N = "${MonteCarloN}"
$mcRc = Invoke-LoggedNative -Exe $python -Args @('-m', $monteModule) -OutFile (Join-Path $runDir 'monte_carlo.out')
if ($mcRc -ne 0) { Write-Host "[WARN] Redteam script exited non-zero" -ForegroundColor Yellow }

Write-Host "[RUN] Fuzz" -ForegroundColor Cyan
$fuzzRc = Invoke-LoggedNative -Exe $python -Args @('-m', $fuzzModule) -OutFile (Join-Path $runDir 'fuzz.out')
if ($fuzzRc -ne 0) { Write-Host "[WARN] Fuzz script exited non-zero" -ForegroundColor Yellow }

Write-Host "[DONE] Logs -> $runDir" -ForegroundColor Green

if ($detRc -ne 0) { exit $detRc }
exit 0
