# Recompute and update the policy SHA256 hash in-place.
#
# Hashing rule (important):
# - The policy hash is computed over the exact JSON text with the value of
#   crypto.policy_hash set to an empty string "". This avoids self-reference
#   and keeps the result stable across runs without reformatting the file.
# - We preserve all other bytes (including whitespace, indentation, and CRLF)
#   so audits can reproduce the same hash by applying the same blanking rule.
#
# Usage examples (PowerShell):
#   ./update_policy_hash.ps1                    # Update default policy
#   ./update_policy_hash.ps1 -DryRun            # Show computed hash, no write
#   ./update_policy_hash.ps1 -PolicyPath "./TrustOps/CODEX/Policies/Scaffolded_Freedom.json"
#
# Exit codes:
#   0 success, 1 error.

[CmdletBinding(SupportsShouldProcess=$true)]
param(
    [Parameter(Position=0)]
    [string]$PolicyPath = Join-Path $PSScriptRoot '..' | Join-Path -ChildPath 'Policies' | Join-Path -ChildPath 'Scaffolded_Freedom.json',

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-FileText {
    param([string]$Path)
    if (!(Test-Path -LiteralPath $Path)) {
        throw "Policy file not found: $Path"
    }
    # -Raw preserves line endings (CRLF) as-is
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

function Set-FileText {
    param([string]$Path, [string]$Text)
    # Use UTF8 without BOM, preserve newline at end if present
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $encoding)
}

function Get-PolicyHash {
    param([string]$PolicyJsonText)
    # Blank the policy_hash value for hashing (stable rule)
    $pattern = '"policy_hash"\s*:\s*"[A-Fa-f0-9]*"'
    $blanked = [System.Text.RegularExpressions.Regex]::Replace($PolicyJsonText, $pattern, '"policy_hash": ""',
        [System.Text.RegularExpressions.RegexOptions]::Singleline)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($blanked)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $hashBytes = $sha.ComputeHash($bytes)
    } finally {
        $sha.Dispose()
    }
    # Uppercase hex, no separators
    return ([System.BitConverter]::ToString($hashBytes)).Replace('-', '')
}

try {
    $fullPath = (Resolve-Path -LiteralPath $PolicyPath).Path
} catch {
    Write-Error $_
    exit 1
}

try {
    $originalText = Get-FileText -Path $fullPath
} catch {
    Write-Error $_
    exit 1
}

# Compute new hash per stable rule
$newHash = Get-PolicyHash -PolicyJsonText $originalText

Write-Host "Computed SHA256 (policy_hash blanked): $newHash"

# Prepare updated text: replace current policy_hash value with new
$pattern = '("policy_hash"\s*:\s*")([A-Fa-f0-9]*)(")'
$replacement = "`$1$newHash`$3"
$updatedText = [System.Text.RegularExpressions.Regex]::Replace($originalText, $pattern, $replacement,
    [System.Text.RegularExpressions.RegexOptions]::Singleline)

if ($updatedText -eq $originalText) {
    Write-Host "No change to file content (hash is already current or policy_hash field missing)."
} else {
    if ($DryRun) {
        Write-Host "DryRun: not writing changes. File would be updated with the new hash."
    } else {
        if ($PSCmdlet.ShouldProcess($fullPath, "Update policy_hash to $newHash")) {
            try {
                Set-FileText -Path $fullPath -Text $updatedText
                Write-Host "Updated: $fullPath"
            } catch {
                Write-Error $_
                exit 1
            }
        }
    }
}

# Optional verification: show the first 16 chars to aid audit trails
Write-Host ("policy_hash preview: {0}" -f $newHash.Substring(0,16))
exit 0
