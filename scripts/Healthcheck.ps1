Write-Host "=== Sovereign Healthcheck ===" -ForegroundColor Cyan
$results = @()
# Check git status
try {
  $gitStatus = git status --short 2>$null
  $results += [PSCustomObject]@{Check='GitDirty'; Value=(-not [string]::IsNullOrWhiteSpace($gitStatus)); Detail=$gitStatus }
} catch { $results += [PSCustomObject]@{Check='GitStatusError'; Value=$false; Detail=$_.Exception.Message } }
# Check python availability
try { python --version 2>&1 | Write-Host -ForegroundColor Gray } catch { Write-Warning 'Python missing' }
# Check ledger file existence
$ledgerPath = Join-Path (Get-Location) 'boardroom_ledger.jsonl'
$results += [PSCustomObject]@{Check='LedgerExists'; Value=(Test-Path $ledgerPath); Detail=$ledgerPath }
$results | Format-Table -AutoSize
