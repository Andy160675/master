[CmdletBinding()]
param(
  [string]$Query,
  [string]$Prompt,
  [ValidateSet('auto','status','verifier','enforcer','debug')][string]$Mode='auto',
  [string]$Endpoint = "",
  [string]$RouterModel = "llama3",
  [string]$VerifierModel = "llama3",
  [int]$MaxTokens = 512,
  [switch]$NoVerify,
  [switch]$JsonOut
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Endpoint)) {
  $Endpoint = $env:OLLAMA_HOST
}
if ([string]::IsNullOrWhiteSpace($Endpoint)) {
  $Endpoint = 'http://localhost:11434'
}
function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err ($m){ Write-Host "[FAIL] $m" -ForegroundColor Red }
function New-Dir($p){ if (-not [string]::IsNullOrWhiteSpace($p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null } }

# Compose effective prompt
$EffectivePrompt = if ($Query) { $Query } elseif ($Prompt) { $Prompt } else { '' }
if (-not $EffectivePrompt -and $Mode -notin 'status') { Write-Err "Provide -Query or -Prompt."; exit 1 }

# Fail-closed policy gate (skip only for status mode)
if ($Mode -ne 'status') {
  try { & powershell -NoProfile -ExecutionPolicy Bypass -File "$PSScriptRoot/Validate-Policy.ps1" | Out-Null }
  catch { Write-Err "Policy validation failed: $($_.Exception.Message)"; exit 10 }
}

if ($Mode -eq 'status') {
  try {
    $tags = Invoke-RestMethod -Method Get -Uri ("{0}/api/tags" -f $Endpoint) -TimeoutSec 10
    $models = ($tags.models | ForEach-Object { $_.name }) -join ', '
    if (-not $models) { $models = '(none)' }
    $out = [pscustomobject]@{ ok = $true; endpoint=$Endpoint; models=$models }
    if ($JsonOut) { $out | ConvertTo-Json -Depth 4 } else { Write-Host "? Ollama: Running"; Write-Host "?? Models available: $models" }
    exit 0
  } catch {
    Write-Err "Ollama unreachable at $Endpoint : $($_.Exception.Message)"; exit 2
  }
}

# Draft generation (router) when needed
$draft = $null
if ($Mode -in 'auto','verifier','debug','enforcer') {
  $body = @{ model = $RouterModel; prompt = $EffectivePrompt; stream = $false; options = @{ num_predict = $MaxTokens } } | ConvertTo-Json -Depth 6
  Write-Info "Router model: $RouterModel"
  try { $resp = Invoke-RestMethod -Method Post -Uri ("{0}/api/generate" -f $Endpoint) -ContentType 'application/json' -Body $body -TimeoutSec 180 } catch { Write-Err "Router call failed: $($_.Exception.Message)"; exit 20 }
  $draft = [string]$resp.response
}

# Enforcer (standards)
$enforced = $draft
if ($Mode -in 'auto','enforcer','debug','verifier') {
  $tmp = New-TemporaryFile
  Set-Content -LiteralPath $tmp -Value $draft -Encoding UTF8
  $py = @"
import sys
from agi.core.standards import TraumaStandard
p = sys.argv[1]
text = open(p, encoding='utf-8').read()
ts = TraumaStandard()
ok, v = ts.validate_output(text)
if ok:
    print(text)
else:
    print(ts.correct_output(text, v))
"@
  try { $enforced = & python -c $py $tmp 2>$null } catch { Write-Warn "Enforcer fallback to draft: $($_.Exception.Message)"; $enforced = $draft }
  Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
}

# Verifier (optional unless mode explicitly verifier)
$final = $enforced
$verifyNote = 'SKIPPED'
if ($Mode -in 'auto','verifier','debug' -and -not $NoVerify) {
  $verifyPrompt = @"
You are a safety verifier. Given USER PROMPT and ASSISTANT DRAFT below, reply with exactly one of:
OK
FIX: <safe alternative>
Policies: no coercive language; no urgency; no identity inference; calm tone; optional depth.
USER PROMPT:
$EffectivePrompt
ASSISTANT DRAFT:
$enforced
"@
  $vBody = @{ model = $VerifierModel; prompt = $verifyPrompt; stream = $false; options = @{ num_predict = 200 } } | ConvertTo-Json -Depth 5
  try {
    $vResp = Invoke-RestMethod -Method Post -Uri ("{0}/api/generate" -f $Endpoint) -ContentType 'application/json' -Body $vBody -TimeoutSec 120
    $vText = [string]$vResp.response
    if ($vText.Trim().ToUpper().StartsWith('OK')) { $verifyNote='OK' } elseif ($vText.Trim().ToUpper().StartsWith('FIX:')) { $final = ($vText.Substring(4)).Trim(); $verifyNote='FIXED' } else { $verifyNote='UNRECOGNIZED' }
  } catch { $verifyNote = "VERIFIER_ERROR: $($_.Exception.Message)" }
}

# Assemble record
$logRoot = Join-Path (Split-Path -Parent $PSScriptRoot) 'Data/ollama_runs'
New-Dir $logRoot
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$logFile = Join-Path $logRoot ("run_" + $stamp + ".jsonl")
$record = [pscustomobject]@{
  ts = (Get-Date).ToString('o')
  mode = $Mode
  endpoint = $Endpoint
  prompt = $EffectivePrompt
  routerModel = $RouterModel
  verifierModel = $VerifierModel
  draft = $draft
  enforced = $enforced
  final = $final
  verify = $verifyNote
}
($record | ConvertTo-Json -Compress -Depth 6) | Add-Content -LiteralPath $logFile

if ($Mode -eq 'debug') { $JsonOut = $true }

if ($JsonOut) {
  $record | ConvertTo-Json -Depth 6
} else {
  if ($Mode -eq 'verifier') { Write-Host ($record | ConvertTo-Json -Depth 4) }
  else { Write-Host $final }
}
