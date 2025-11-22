param(
    [Parameter(Mandatory = $true)]
    [string]$ManifestPath,

    [Parameter(Mandatory = $true)]
    [string]$OutJson
)

# Guard rails
if (-not (Test-Path $ManifestPath)) {
    Write-Error "Manifest file not found: $ManifestPath"
    exit 1
}

$manifestContent = Get-Content -Raw -Path $ManifestPath
$manifestHashBytes = [System.Security.Cryptography.SHA256]::Create().ComputeHash(
    [System.Text.Encoding]::UTF8.GetBytes($manifestContent)
)
$manifestHash = ($manifestHashBytes | ForEach-Object { "{0:x2}" -f $_ }) -join ""

$signatureObject = [pscustomobject]@{
    file              = (Split-Path -Leaf $ManifestPath)
    path              = (Resolve-Path $ManifestPath).Path
    algo              = "SHA-256"
    hash              = $manifestHash
    generated_utc     = (Get-Date).ToUniversalTime().ToString("o")
    schema_version    = "1.0.0"
    node_id           = $env:COMPUTERNAME
    build_source      = $env:GITHUB_RUN_ID -or "local"
    build_commit      = $env:GITHUB_SHA -or "local"
    signing_strategy  = "hash-only"
}

$signatureJson = $signatureObject | ConvertTo-Json -Depth 8

# Ensure output directory exists
$outDir = Split-Path $OutJson -Parent
if ($outDir -and -not (Test-Path $outDir)){
    New-Item -ItemType Directory -Path $outDir | Out-Null
}

$signatureJson | Out-File -FilePath $OutJson -Encoding UTF8

Write-Host "Signed manifest:" -ForegroundColor Green
Write-Host "  File : $ManifestPath"
Write-Host "  Hash : $manifestHash"
Write-Host "  Out  : $OutJson"
