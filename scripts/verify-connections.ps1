[CmdletBinding()]
param(
  [string]$TruthEngineUrl = "",
  [string]$OllamaHost = "",
  [int]$TimeoutSec = 4
)

$ErrorActionPreference = 'Stop'

function Resolve-BaseUrl([string]$u) {
  if ([string]::IsNullOrWhiteSpace($u)) { return "" }
  return ($u.TrimEnd('/'))
}

$truth = Resolve-BaseUrl($TruthEngineUrl)
if ([string]::IsNullOrWhiteSpace($truth)) { $truth = Resolve-BaseUrl($env:TRUTH_ENGINE_URL) }
if ([string]::IsNullOrWhiteSpace($truth)) { $truth = 'http://localhost:8000' }

$ollama = Resolve-BaseUrl($OllamaHost)
if ([string]::IsNullOrWhiteSpace($ollama)) { $ollama = Resolve-BaseUrl($env:OLLAMA_HOST) }
if ([string]::IsNullOrWhiteSpace($ollama)) { $ollama = 'http://localhost:11434' }

$report = [ordered]@{
  ts_local = (Get-Date).ToString('o')
  truth_engine_url = $truth
  ollama_host = $ollama
  checks = @()
}

function Add-Check($name, $ok, $details) {
  $report.checks += [pscustomobject]@{ name=$name; ok=[bool]$ok; details=$details }
}

# ---- Truth Engine ----
try {
  $endpoint = "$truth/truth/query"
  $payload = @{ question = 'connectivity check'; k = 1 } | ConvertTo-Json
  $resp = Invoke-RestMethod -Method Post -Uri $endpoint -ContentType 'application/json' -Body $payload -TimeoutSec $TimeoutSec
  $hasAnswer = $null -ne $resp.answer
  Add-Check 'truth-engine:http' ($hasAnswer) (@{ endpoint=$endpoint; answer_present=$hasAnswer })
} catch {
  Add-Check 'truth-engine:http' $false (@{ endpoint="$truth/truth/query"; error=$_.Exception.Message })
}

# ---- Ollama ----
# Prefer the native Ollama endpoint for a quick sanity check.
try {
  $endpoint = "$ollama/api/tags"
  $resp = Invoke-RestMethod -Method Get -Uri $endpoint -TimeoutSec $TimeoutSec
  $count = 0
  if ($resp.models) { $count = @($resp.models).Count }
  Add-Check 'ollama:api/tags' $true (@{ endpoint=$endpoint; models_count=$count })
} catch {
  Add-Check 'ollama:api/tags' $false (@{ endpoint="$ollama/api/tags"; error=$_.Exception.Message })
}

$okAll = -not ($report.checks | Where-Object { -not $_.ok } | Measure-Object).Count
$report.ok = [bool]$okAll

$report | ConvertTo-Json -Depth 6
if (-not $okAll) { exit 2 }
exit 0
