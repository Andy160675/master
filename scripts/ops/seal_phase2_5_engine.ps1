[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Write-TextFile {
  param(
    [Parameter(Mandatory)] [string]$Path,
    [Parameter()] [AllowNull()] [AllowEmptyCollection()] [object]$Lines
  )

  $parent = Split-Path -Parent $Path
  if ($parent -and !(Test-Path $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }

  $normalized = @()
  if ($null -ne $Lines) {
    if ($Lines -is [string]) { $normalized = @($Lines) }
    else { $normalized = @($Lines) }
  }

  $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
  $content = ($normalized -join "`n")
  [System.IO.File]::WriteAllText($Path, $content + "`n", $utf8NoBom)
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location $repoRoot

$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$evidenceRoot = Join-Path $repoRoot 'evidence/phase2_5_engine_live'
$evidenceDir = Join-Path $evidenceRoot $ts

New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

# Ensure expected folders exist (engine state seal includes structure)
New-Item -ItemType Directory -Force -Path (Join-Path $repoRoot 'governance/phase2_5_engine') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $repoRoot 'data') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $repoRoot 'reports') | Out-Null

# Minimal placeholders so empty dirs can be tracked if needed
$gitkeepData = Join-Path $repoRoot 'data/.gitkeep'
$gitkeepReports = Join-Path $repoRoot 'reports/.gitkeep'
if (!(Test-Path $gitkeepData)) { Write-TextFile -Path $gitkeepData -Lines @('') }
if (!(Test-Path $gitkeepReports)) { Write-TextFile -Path $gitkeepReports -Lines @('') }

# Evidence snapshots (pre-seal)
Write-TextFile -Path (Join-Path $evidenceDir 'pre_git_status.txt') -Lines @(git status)
Write-TextFile -Path (Join-Path $evidenceDir 'pre_git_status_porcelain.txt') -Lines @(git status --porcelain=v1)
Write-TextFile -Path (Join-Path $evidenceDir 'pre_head.txt') -Lines @((git rev-parse HEAD))
Write-TextFile -Path (Join-Path $evidenceDir 'pre_branch.txt') -Lines @((git rev-parse --abbrev-ref HEAD))

# Deterministic SHA256 manifest for engine state paths (the same paths you will git add)
$targets = @('governance/phase2_5_engine', 'data', 'reports')
$files = @()
foreach ($t in $targets) {
  $abs = Join-Path $repoRoot $t
  if (Test-Path $abs) {
    $files += Get-ChildItem -Recurse -File -Path $abs | ForEach-Object {
      $_.FullName.Substring($repoRoot.Length).TrimStart('\','/') -replace '\\','/'
    }
  }
}
$files = $files | Sort-Object
Write-TextFile -Path (Join-Path $evidenceDir 'artifact_list.txt') -Lines $files

$hashLines = foreach ($rel in $files) {
  $abs = Join-Path $repoRoot $rel
  $hash = (Get-FileHash -Algorithm SHA256 -Path $abs).Hash.ToLowerInvariant()
  "$hash  $rel"
}
Write-TextFile -Path (Join-Path $evidenceDir 'sha256_manifest.txt') -Lines $hashLines

Write-Output "[seal] Phase 2.5 engine seal complete."
Write-Output "[seal] Evidence capsule: $evidenceDir"
Write-Output "[seal] Files hashed: $($files.Count)"