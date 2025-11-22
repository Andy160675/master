Param(
    [string]$Root = "C:\Users\andyj\AI_Agent_Research",
    [string]$Output = "dependency_manifest.json"
)

Write-Host "=== SOVEREIGN DEPENDENCY MANIFEST ===" -ForegroundColor Cyan
Write-Host "Root:   $Root"
Write-Host "Output: $Output`n"

if (-not (Test-Path $Root)) {
    Write-Host "Root path not found: $Root" -ForegroundColor Red
    exit 1
}

function Get-FileSha256([string]$Path){
    try{
        $bytes = [System.IO.File]::ReadAllBytes($Path)
        $hashBytes = [System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)
        ($hashBytes | ForEach-Object { "{0:x2}" -f $_ }) -join ""
    } catch {
        ""
    }
}

$manifest = [ordered]@{
    generated_utc = (Get-Date).ToUniversalTime().ToString('o')
    root         = (Resolve-Path $Root).Path
    projects     = @()
    python_envs  = @()
    node_envs    = @()
    lockfiles    = @()
}

# 1) C# / .NET projects (.csproj)
Write-Host "[1] Collecting .csproj files..." -ForegroundColor Yellow
Get-ChildItem -Path $Root -Recurse -Filter *.csproj -ErrorAction SilentlyContinue |
    ForEach-Object {
        $full = $_.FullName
        $rel = $full.Substring($Root.Length+1).TrimStart('\','/')
        $entry = [ordered]@{
            name = $_.BaseName
            path = $rel
            target_framework = ''
            package_references = @()
        }
        try {
            $xml = [xml](Get-Content -LiteralPath $full -Raw)
            $tf = ($xml.Project.PropertyGroup.TargetFramework, $xml.Project.PropertyGroup.TargetFrameworks | Where-Object { $_ }) -join ';'
            $entry.target_framework = $tf
            $pkgRefs = @()
            if ($xml.Project.ItemGroup){
                $xml.Project.ItemGroup | ForEach-Object {
                    if ($_.PackageReference){
                        $_.PackageReference | ForEach-Object {
                            $pkgRefs += [ordered]@{ id = $_.Include; version = $_.Version }
                        }
                    }
                }
            }
            $entry.package_references = $pkgRefs
        } catch {
            Write-Host "  ?? Failed to parse $rel as XML" -ForegroundColor DarkYellow
        }
        $manifest.projects += $entry
    }

# 2) Python environments (requirements.txt)
Write-Host "[2] Collecting requirements.txt..." -ForegroundColor Yellow
Get-ChildItem -Path $Root -Recurse -Filter requirements.txt -ErrorAction SilentlyContinue |
    ForEach-Object {
        $full = $_.FullName
        $rel = $full.Substring($Root.Length+1).TrimStart('\','/')
        $lines = Get-Content $full | Where-Object { $_ -and (-not $_.Trim().StartsWith('#')) }
        $hash = Get-FileSha256 -Path $full
        $manifest.python_envs += [ordered]@{
            path = $rel
            packages = $lines
            hash_sha256 = $hash
        }
    }

# 3) Node / JS projects (package.json)
Write-Host "[3] Collecting package.json..." -ForegroundColor Yellow
Get-ChildItem -Path $Root -Recurse -Filter package.json -ErrorAction SilentlyContinue |
    ForEach-Object {
        $full = $_.FullName
        $rel = $full.Substring($Root.Length+1).TrimStart('\','/')
        try {
            $raw = Get-Content $full -Raw
            $pkg = $raw | ConvertFrom-Json
            $hash = Get-FileSha256 -Path $full

            $manifest.node_envs += [ordered]@{
                path = $rel
                name = $pkg.name
                version = $pkg.version
                dependencies = $pkg.dependencies
                devDependencies = $pkg.devDependencies
                hash_sha256 = $hash
            }
        } catch {
            Write-Host "  ?? Failed to parse $rel as JSON" -ForegroundColor DarkYellow
        }
    }

# 4) Lockfile scanning
Write-Host "[4] Collecting lockfiles..." -ForegroundColor Yellow
$lockfilePatterns = @(
    'package-lock.json',
    'yarn.lock',
    'pnpm-lock.yaml',
    'poetry.lock',
    'Pipfile.lock',
    'requirements.lock'
)

foreach ($pattern in $lockfilePatterns){
    Get-ChildItem -Path $Root -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue |
        ForEach-Object {
            $full = $_.FullName
            $rel = $full.Substring($Root.Length+1).TrimStart('\','/')
            $type = switch -Wildcard ($_.Name) {
                'package-lock.json' { 'npm' }
                'yarn.lock' { 'yarn' }
                'pnpm-lock.yaml' { 'pnpm' }
                'poetry.lock' { 'poetry' }
                'Pipfile.lock' { 'pipenv' }
                default { 'generic' }
            }
            $hash = Get-FileSha256 -Path $full
            $manifest.lockfiles += [ordered]@{
                path = $rel
                full_path = $full
                type = $type
                hash_sha256 = $hash
            }
        }
}

# 5) Optionally include top-level files (README/license) etc.

# 6) Write manifest
$outPath = Join-Path $Root $Output
$manifest | ConvertTo-Json -Depth 10 | Set-Content $outPath -Encoding utf8

Write-Host "`n? Dependency manifest written to $outPath" -ForegroundColor Green
