param(
  [switch]$Apply,
  [switch]$DeTrackEnv = $true,
  [switch]$DeTrackRuntime = $true,
  [switch]$StageChanges
)

$ErrorActionPreference = 'Stop'

function Invoke-Git([string[]]$Args) {
  $cmd = 'git ' + ($Args -join ' ')
  Write-Host "[git] $cmd" -ForegroundColor Cyan
  if ($Apply) {
    & git @Args
    if ($LASTEXITCODE -ne 0) { throw "git failed: $cmd" }
  }
}

function Assert-Repo {
  & git rev-parse --is-inside-work-tree *> $null
  if ($LASTEXITCODE -ne 0) { throw 'Not inside a git work tree.' }
}

Assert-Repo

Write-Host "[INFO] Apply=$Apply  StageChanges=$StageChanges" -ForegroundColor Gray

# 1) Ensure ignore rules are present (non-destructive; user can edit as needed)
$gitignore = Join-Path (Get-Location) '.gitignore'
if (-not (Test-Path $gitignore)) {
  throw 'Missing .gitignore at repo root.'
}

# 2) De-track committed virtualenv (common accidental repo bloat)
if ($DeTrackEnv) {
  # If env/ is tracked, remove from index only.
  $tracked = & git ls-files env 2>$null
  if ($tracked) {
    Write-Host '[PLAN] De-track env/ from git index (keeps files on disk).' -ForegroundColor Yellow
    Invoke-Git @('rm','-r','--cached','env')
  } else {
    Write-Host '[OK] env/ not tracked (or already de-tracked).' -ForegroundColor Green
  }
}

# 3) De-track runtime artifacts if they were ever added
if ($DeTrackRuntime) {
  foreach ($p in @('validation','Data')) {
    $tracked = & git ls-files $p 2>$null
    if ($tracked) {
      Write-Host "[PLAN] De-track $p/ from git index (keeps files on disk)." -ForegroundColor Yellow
      Invoke-Git @('rm','-r','--cached',$p)
    }
  }
}

# 4) Optional staging
if ($StageChanges) {
  Write-Host '[PLAN] Stage current working tree changes.' -ForegroundColor Yellow
  Invoke-Git @('add','-A')
}

Write-Host '[DONE] Hygiene plan complete.' -ForegroundColor Green
Write-Host '       Next: review `git status`, then commit and proceed with sync/seal.' -ForegroundColor Green
