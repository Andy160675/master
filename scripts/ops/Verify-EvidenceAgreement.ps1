[CmdletBinding()]
param(
    # UNC path to the evidence share (collector reads from here)
    [Parameter(Mandatory=$true)][string]$ShareRoot,

    # Relative folder under share where node baselines are published:
    #   <ShareRoot>\baselines\<NodeId>\evidence_baseline_summary_*.json
    [string]$BaselinesSubdir = "baselines",

    # Comma/space/semicolon-separated node ids (e.g., PC1,PC2,PC4)
    [string]$NodeIds = "",

    # Optional JSON file: { "nodes": [ { "node_id": "PC1" }, ... ] }
    [string]$NodesFile = "",

    [string]$OutDir = "${PSScriptRoot}\\..\\..\\validation\\evidence_agreement",
    [switch]$EmitJson,
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function New-StampUtc { (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }

function Parse-NodeIds([string]$s) {
    if ([string]::IsNullOrWhiteSpace($s)) { return @() }
    return @(
        $s -split '[,;\s]+' |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ }
    )
}

function Read-NodesFile([string]$path) {
    if (-not $path) { return @() }
    if (-not (Test-Path -LiteralPath $path)) { throw "NodesFile not found: $path" }
    $obj = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json

    $ids = @()
    if ($obj.PSObject.Properties.Name -contains 'nodes') {
        foreach ($n in @($obj.nodes)) {
            if ($n -and ($n.PSObject.Properties.Name -contains 'node_id') -and $n.node_id) {
                $ids += [string]$n.node_id
            }
        }
    }
    return $ids
}

function Get-LatestSummary([string]$nodeId,[string]$shareRoot,[string]$subdir) {
    $nodeDir = Join-Path (Join-Path $shareRoot $subdir) $nodeId
    if (-not (Test-Path -LiteralPath $nodeDir)) {
        return $null
    }

    $candidates = Get-ChildItem -LiteralPath $nodeDir -Filter 'evidence_baseline_summary_*.json' -File -ErrorAction SilentlyContinue
    if (-not $candidates -or $candidates.Count -eq 0) {
        return $null
    }

    return ($candidates | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1)
}

$stamp = New-StampUtc
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$ids = @()
$ids += Parse-NodeIds $NodeIds
$ids += Read-NodesFile $NodesFile
$ids = @($ids | Where-Object { $_ } | Sort-Object -Unique)

if ($ids.Count -eq 0) {
    throw "No nodes specified. Provide -NodeIds or -NodesFile."
}

$observations = @()
$missing = @()

foreach ($id in $ids) {
    $latest = Get-LatestSummary -nodeId $id -shareRoot $ShareRoot -subdir $BaselinesSubdir
    if (-not $latest) {
        $missing += $id
        continue
    }

    $summary = Get-Content -LiteralPath $latest.FullName -Raw -Encoding UTF8 | ConvertFrom-Json

    $merkle = $null
    if ($summary.PSObject.Properties.Name -contains 'merkle_root') { $merkle = [string]$summary.merkle_root }

    $sha = ''
    try { $sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $latest.FullName).Hash.ToLowerInvariant() } catch { $sha = '' }

    $observations += [pscustomobject]@{
        node_id = $id
        summary_path = $latest.FullName
        summary_sha256 = $sha
        generated_utc = if ($summary.generated_utc) { [string]$summary.generated_utc } else { $null }
        root_path = if ($summary.root_path) { [string]$summary.root_path } else { $null }
        file_count = if ($summary.file_count) { [int]$summary.file_count } else { $null }
        merkle_root = $merkle
    }
}

$uniqueRoots = @(
    $observations |
        Where-Object { $_.merkle_root -and $_.merkle_root.Trim() -ne '' } |
        Select-Object -ExpandProperty merkle_root -Unique
)

$agreement = ($missing.Count -eq 0) -and ($uniqueRoots.Count -eq 1)

# Dissent telemetry: group nodes by merkle root (including null)
$byRoot = @()
foreach ($g in ($observations | Group-Object merkle_root)) {
    $byRoot += [pscustomobject]@{
        merkle_root = if ($g.Name) { $g.Name } else { $null }
        nodes = @($g.Group | Select-Object -ExpandProperty node_id)
        count = $g.Count
    }
}

$report = [pscustomobject]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    share_root = $ShareRoot
    baselines_subdir = $BaselinesSubdir
    expected_nodes = $ids
    missing_nodes = $missing
    observation_count = $observations.Count
    agreement = $agreement
    unique_merkle_roots = $uniqueRoots
    groups = $byRoot
    observations = $observations
}

$outPath = Join-Path $OutDir ("evidence_agreement_{0}.json" -f $stamp)
$report | ConvertTo-Json -Depth 8 | Out-File -FilePath $outPath -Encoding utf8

$receiptScript = Join-Path $PSScriptRoot 'Write-Sha256-Receipt.ps1'
if (Test-Path -LiteralPath $receiptScript) {
    & $receiptScript -InputFile $outPath -OutputFile "$outPath.sha256" -DisplayPath (Split-Path -Leaf $outPath) | Out-Null
}

if ($EmitJson) {
    $report | ConvertTo-Json -Depth 8
} else {
    Write-Host "Agreement report -> $outPath" -ForegroundColor Green
    if ($agreement) {
        Write-Host "AGREEMENT: 1 merkle root across $($observations.Count) nodes" -ForegroundColor Green
        Write-Host "Root: $($uniqueRoots[0])" -ForegroundColor Cyan
    } else {
        Write-Host "DISAGREEMENT OR MISSING NODES" -ForegroundColor Yellow
        if ($missing.Count -gt 0) { Write-Host "Missing: $($missing -join ', ')" -ForegroundColor Yellow }
        foreach ($g in $byRoot) {
            $r = if ($g.merkle_root) { $g.merkle_root } else { '<null>' }
            Write-Host ("{0} -> {1}" -f $r, ($g.nodes -join ', '))
        }
    }
}

if ($Gate -and (-not $agreement)) { exit 1 }
