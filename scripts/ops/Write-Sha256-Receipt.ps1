[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$InputFile,
  [Parameter(Mandatory = $true)][string]$OutputFile,
  [string]$DisplayPath = "",
  [switch]$Gate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$m) {
  Write-Host "[FAIL] $m" -ForegroundColor Red
  if ($Gate) { exit 1 }
}

try {
  if (-not (Test-Path -LiteralPath $InputFile)) {
    Fail "InputFile not found: $InputFile"
    exit 0
  }

  $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $InputFile).Hash.ToLowerInvariant()
  $p = if ($DisplayPath) { $DisplayPath } else { $InputFile }
  $line = "{0}  {1}" -f $hash, $p

  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputFile) | Out-Null
  $line | Out-File -FilePath $OutputFile -Encoding ascii
  $line

} catch {
  Fail $_.Exception.Message
}

exit 0
