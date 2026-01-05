Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Utf8NoBomFile {
  param(
    [Parameter(Mandatory)] [string]$Path,
    [Parameter(Mandatory)] [string]$Content
  )
  $parent = Split-Path -Parent $Path
  if ($parent -and !(Test-Path $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
  $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location $repoRoot

$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$E = Join-Path $repoRoot ("evidence/session-logs/outreach0_{0}" -f $ts)
New-Item -ItemType Directory -Force -Path $E | Out-Null

$name  = Read-Host "Lead name"
$email = Read-Host "Lead email"
$src   = Read-Host "Source (LinkedIn/Email/etc)"
$chan  = Read-Host "Channel (email/linkedin/etc)"
$note  = Read-Host "Note (e.g., Sent proposal)"

# Use venv python if present; else fall back to python on PATH
$py = Join-Path $repoRoot 'env/Scripts/python.exe'
if (!(Test-Path $py)) { $py = 'python' }

# 0) Anchor capture
& git rev-parse --show-toplevel | Tee-Object (Join-Path $E '00_repo_root.txt') | Out-Null
& git branch --show-current | Tee-Object (Join-Path $E '00_branch.txt') | Out-Null
& git rev-parse HEAD | Tee-Object (Join-Path $E '00_head.txt') | Out-Null
& git tag -l | Sort-Object | Tee-Object (Join-Path $E '00_tags_sorted.txt') | Out-Null

# 1) Log lead + outreach (safe input passing via env vars)
$env:LEAD_NAME = $name
$env:LEAD_EMAIL = $email
$env:LEAD_SOURCE = $src
$env:OUTREACH_CHANNEL = $chan
$env:OUTREACH_NOTE = $note

$pyScript = Join-Path $E 'run_outreach0.py'
Write-Utf8NoBomFile -Path $pyScript -Content @'
from governance.phase2_5_engine.pipeline_manager import PipelineManager

pm = PipelineManager()
lead_id = pm.add_lead(
    name=str(__import__('os').environ.get('LEAD_NAME','')),
    contact=str(__import__('os').environ.get('LEAD_EMAIL','')),
    source=str(__import__('os').environ.get('LEAD_SOURCE','')),
)
pm.log_outreach(
    lead_id,
    'A1_Audit',
    str(__import__('os').environ.get('OUTREACH_CHANNEL','')),
    str(__import__('os').environ.get('OUTREACH_NOTE','')),
)
print('LEAD_ID=', lead_id)
'@

& $py $pyScript 2>&1 | Tee-Object (Join-Path $E '01_outreach_log.txt')

# Clear env vars (avoid leaking to later steps)
Remove-Item Env:LEAD_NAME,Env:LEAD_EMAIL,Env:LEAD_SOURCE,Env:OUTREACH_CHANNEL,Env:OUTREACH_NOTE -ErrorAction SilentlyContinue

# 2) Generate daily report
$pyReport = Join-Path $E 'run_report.py'
Write-Utf8NoBomFile -Path $pyReport -Content @'
from governance.phase2_5_engine.report_generator import generate_daily_report
print(generate_daily_report())
'@

& $py $pyReport 2>&1 | Tee-Object (Join-Path $E '02_daily_report_output.txt')

# 3) Snapshot + hashes (data + reports)
$Snap = Join-Path $E "snapshot"
New-Item -ItemType Directory -Force -Path $Snap | Out-Null
if (Test-Path .\data)    { Copy-Item -Force -Recurse .\data    (Join-Path $Snap "data") }
if (Test-Path .\reports) { Copy-Item -Force -Recurse .\reports (Join-Path $Snap "reports") }

$lines = Get-ChildItem $Snap -Recurse -File |
  Sort-Object FullName |
  ForEach-Object {
    $h = Get-FileHash -Algorithm SHA256 $_.FullName
    $rel = $_.FullName.Substring($Snap.Length).TrimStart('\\','/')
    "{0}  snapshot/{1}" -f $h.Hash.ToLowerInvariant(), ($rel -replace '\\','/')
  }

$manifestPath = Join-Path $E '03_snapshot_sha256.txt'
Write-Utf8NoBomFile -Path $manifestPath -Content (($lines -join "`n") + "`n")

Write-Host "✅ Outreach-0 captured + hashed: $E" -ForegroundColor Green
