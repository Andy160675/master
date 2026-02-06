[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$BaselineA,
    [Parameter(Mandatory=$true)][string]$BaselineB,
    [string]$OutDir = "${PSScriptRoot}\\..\\..\\validation\\evidence_baseline",
    [switch]$EmitJson,
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function New-StampUtc { (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }

$stamp = New-StampUtc
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if (-not (Test-Path -LiteralPath $BaselineA)) { throw "Missing BaselineA: $BaselineA" }
if (-not (Test-Path -LiteralPath $BaselineB)) { throw "Missing BaselineB: $BaselineB" }

$a = Get-Content -LiteralPath $BaselineA -Raw -Encoding UTF8 | ConvertFrom-Json
$b = Get-Content -LiteralPath $BaselineB -Raw -Encoding UTF8 | ConvertFrom-Json

$mapA = @{}
foreach ($e in $a) { $mapA[[string]$e.path] = [string]$e.sha256 }

$mapB = @{}
foreach ($e in $b) { $mapB[[string]$e.path] = [string]$e.sha256 }

$allPaths = @($mapA.Keys + $mapB.Keys | Sort-Object -Unique)

$mismatches = @()
foreach ($p in $allPaths) {
    $ha = if ($mapA.ContainsKey($p)) { $mapA[$p] } else { $null }
    $hb = if ($mapB.ContainsKey($p)) { $mapB[$p] } else { $null }

    if ($ha -ne $hb) {
        $mismatches += [pscustomobject]@{ path = $p; sha256_a = $ha; sha256_b = $hb }
    }
}

$report = [pscustomobject]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    baseline_a = (Resolve-Path -LiteralPath $BaselineA).Path
    baseline_b = (Resolve-Path -LiteralPath $BaselineB).Path
    mismatch_count = $mismatches.Count
    mismatches = $mismatches
}

$outPath = Join-Path $OutDir ("evidence_baseline_diff_{0}.json" -f $stamp)
$report | ConvertTo-Json -Depth 6 | Out-File -FilePath $outPath -Encoding utf8

$receiptScript = Join-Path $PSScriptRoot 'Write-Sha256-Receipt.ps1'
if (Test-Path -LiteralPath $receiptScript) {
    & $receiptScript -InputFile $outPath -OutputFile "$outPath.sha256" -DisplayPath (Split-Path -Leaf $outPath) | Out-Null
}

if ($EmitJson) {
    $report | ConvertTo-Json -Depth 6
} else {
    Write-Host "Diff report -> $outPath" -ForegroundColor Green
    Write-Host "Mismatches  -> $($mismatches.Count)" -ForegroundColor Cyan
}

if ($Gate -and ($mismatches.Count -gt 0)) { exit 1 }
