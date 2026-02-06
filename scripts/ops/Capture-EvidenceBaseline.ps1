[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RootPath,
    [int]$MaxFiles = 5000,
    [string]$OutDir = "${PSScriptRoot}\\..\\..\\validation\\evidence_baseline",
    [string[]]$ExcludeSubdirs = @(),
    [switch]$EmitJson,
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function New-StampUtc { (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }

if (-not (Test-Path -LiteralPath $RootPath)) {
    throw "RootPath not found: $RootPath"
}

$stamp = New-StampUtc
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$outDirFull = $OutDir
try { $outDirFull = (Resolve-Path -LiteralPath $OutDir).Path } catch {}

# Normalize to a full path if possible
$rootFull = $RootPath
try { $rootFull = (Resolve-Path -LiteralPath $RootPath).Path } catch {}

$files = Get-ChildItem -LiteralPath $RootPath -File -Recurse -ErrorAction Stop

# Exclude output dir and any requested subdirs (relative to RootPath unless absolute)
$excludeRoots = New-Object System.Collections.Generic.List[string]
if ($outDirFull -and $rootFull -and $outDirFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    [void]$excludeRoots.Add($outDirFull)
}

foreach ($ex in @($ExcludeSubdirs)) {
    if ([string]::IsNullOrWhiteSpace($ex)) { continue }
    $exTrim = $ex.Trim()
    $exFull = $exTrim

    if (-not ([System.IO.Path]::IsPathRooted($exTrim))) {
        if ($rootFull) {
            $exFull = Join-Path $rootFull $exTrim
        }
    }

    try { $exFull = (Resolve-Path -LiteralPath $exFull).Path } catch {}
    if ($exFull) { [void]$excludeRoots.Add($exFull) }
}

if ($excludeRoots.Count -gt 0) {
    $files = $files | Where-Object {
        $p = $_.FullName
        foreach ($xr in $excludeRoots) {
            if ($p.StartsWith($xr, [System.StringComparison]::OrdinalIgnoreCase)) { return $false }
        }
        return $true
    }
}
if ($MaxFiles -gt 0 -and $files.Count -gt $MaxFiles) {
    $files = $files | Select-Object -First $MaxFiles
}

$entries = @()
foreach ($f in $files) {
    $rel = $f.FullName
    if ($rootFull -and $rel.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        $rel = $rel.Substring($rootFull.Length).TrimStart('\\')
    }

    $h = ''
    try { $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $f.FullName -ErrorAction Stop).Hash.ToLowerInvariant() } catch { $h = '' }

    $entries += [ordered]@{
        path = ($rel -replace '\\','/')
        sha256 = $h
        size = [int64]$f.Length
        mtime_utc = $f.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')
    }
}

# Deterministic ordering
$entries = @($entries | Sort-Object path)

$baselineListPath = Join-Path $OutDir ("evidence_baseline_{0}.json" -f $stamp)
($entries | ConvertTo-Json -Depth 4) | Out-File -FilePath $baselineListPath -Encoding utf8

# Merkle root over the list-of-objects (using existing helper)
$merkle = $null
$merkleScript = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'compute_merkle_root.py'
if (Test-Path -LiteralPath $merkleScript) {
    try {
        $merkle = & python $merkleScript $baselineListPath
        $merkle = ($merkle | Select-Object -First 1).ToString().Trim()
    } catch {
        $merkle = $null
    }
}

$summary = [ordered]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    root_path = $RootPath
    root_resolved = $rootFull
    max_files = $MaxFiles
    file_count = $entries.Count
    merkle_root = $merkle
    baseline_list = $baselineListPath
}

$summaryPath = Join-Path $OutDir ("evidence_baseline_summary_{0}.json" -f $stamp)
($summary | ConvertTo-Json -Depth 4) | Out-File -FilePath $summaryPath -Encoding utf8

# Hash receipts
$receiptScript = Join-Path $PSScriptRoot 'Write-Sha256-Receipt.ps1'
if (Test-Path -LiteralPath $receiptScript) {
    & $receiptScript -InputFile $baselineListPath -OutputFile "$baselineListPath.sha256" -DisplayPath (Split-Path -Leaf $baselineListPath) | Out-Null
    & $receiptScript -InputFile $summaryPath -OutputFile "$summaryPath.sha256" -DisplayPath (Split-Path -Leaf $summaryPath) | Out-Null
}

if ($EmitJson) {
    $summary | ConvertTo-Json -Depth 4
} else {
    Write-Host "Baseline list   -> $baselineListPath" -ForegroundColor Green
    Write-Host "Baseline summary-> $summaryPath" -ForegroundColor Green
    if ($merkle) { Write-Host "Merkle root     -> $merkle" -ForegroundColor Cyan }
}

if ($Gate -and (-not $merkle)) { exit 1 }
