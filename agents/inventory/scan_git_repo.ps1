Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Generates AI_GIT_INVENTORY.txt using tracked files only.
# Run from repo root.

$patterns = @(
  '*truth*', '*kernel*', '*verifier*', '*epistemic*',
  '*.py', '*.ipynb', '*.js', 'docker-compose*.yml', 'docker-compose*.yaml'
)

$out = 'AI_GIT_INVENTORY.txt'

$files = foreach($p in $patterns){
  git ls-files $p 2>$null
}

$files |
  Where-Object { $_ -and $_.Trim() -ne '' } |
  Sort-Object -Unique |
  Set-Content -Path $out -Encoding UTF8

Write-Output ("WROTE=" + (Resolve-Path $out))
