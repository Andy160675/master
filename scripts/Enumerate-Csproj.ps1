Param(
    [string]$Root = "C:\Users\andyj\AI_Agent_Research"
)

Write-Host "=== SOVEREIGN ENUMERATION: .sln + .csproj ===" -ForegroundColor Cyan
Write-Host "Root: $Root`n"

if (-not (Test-Path $Root)) {
    Write-Host "Root path not found: $Root" -ForegroundColor Red
    exit 1
}

# 1) Solutions
Write-Host "[1] Solution files (.sln)" -ForegroundColor Yellow
$slns = Get-ChildItem -Path $Root -Recurse -Filter *.sln -ErrorAction SilentlyContinue

if (-not $slns) {
    Write-Host "  (none found)" -ForegroundColor DarkYellow
} else {
    $slns | Select-Object `
        @{n="Name";e={$_.Name}},
        @{n="RelativePath";e={$_.FullName.Substring($Root.Length+1)}} |
        Format-Table -AutoSize
}

# 2) Projects
Write-Host "`n[2] C# project files (.csproj)" -ForegroundColor Yellow
$csprojs = Get-ChildItem -Path $Root -Recurse -Filter *.csproj -ErrorAction SilentlyContinue

if (-not $csprojs) {
    Write-Host "  (none found)" -ForegroundColor DarkYellow
} else {
    $csprojs | Select-Object `
        @{n="Project";e={$_.BaseName}},
        @{n="RelativePath";e={$_.FullName.Substring($Root.Length+1)}} |
        Sort-Object Project |
        Format-Table -AutoSize
}

Write-Host "`n=== ENUMERATION COMPLETE ===" -ForegroundColor Cyan
