[CmdletBinding()]
param(
    [string]$RepoRoot = "${PSScriptRoot}\\..\\..",
    [string]$ConvoDir = "${PSScriptRoot}\\..\\..\\sync_conversation",
    [string]$AuthorId = $env:COMPUTERNAME,
    [Parameter(Mandatory=$true)][string]$Message,
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [switch]$AutoStash,
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function Fail([string]$msg) {
    Write-Error $msg
    if ($Gate) { exit 1 }
}

function New-StampUtc { (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }

try { $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path } catch {}

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) {
    Fail "Not a git repo root (or .git missing): $RepoRoot"
    exit 0
}

Push-Location -LiteralPath $RepoRoot
try {
    if (-not $AuthorId) { $AuthorId = 'UNKNOWN' }
    $stamp = New-StampUtc

    # Ensure convo directory exists
    if (-not (Test-Path -LiteralPath $ConvoDir)) {
        New-Item -ItemType Directory -Force -Path $ConvoDir | Out-Null
    }

    $msgRoot = Join-Path $ConvoDir 'messages'
    $authorDir = Join-Path $msgRoot $AuthorId
    New-Item -ItemType Directory -Force -Path $authorDir | Out-Null

    $safeAuthor = ($AuthorId -replace '[^a-zA-Z0-9_.-]', '_')
    $fileName = "${stamp}_${safeAuthor}.md"
    $outFile = Join-Path $authorDir $fileName

    $body = @(
        "# Sync Message",
        "",
        "- utc: $stamp",
        "- author: $AuthorId",
        "",
        "---",
        "",
        $Message.TrimEnd(),
        ""
    ) -join "`n"

    $body | Out-File -FilePath $outFile -Encoding utf8

    Write-Host "[ConvoSend] Wrote: $outFile"

    # If repo has unrelated local edits, either fail fast (default) or autostash.
    & git diff --quiet
    $dirtyWorktree = ($LASTEXITCODE -ne 0)
    & git diff --cached --quiet
    $dirtyIndex = ($LASTEXITCODE -ne 0)

    if (($dirtyWorktree -or $dirtyIndex) -and (-not $AutoStash)) {
        Fail "Repo has local changes; refusing to pull/rebase. Re-run with -AutoStash to allow git to stash/apply automatically."
        exit 0
    }

    # Pull first to reduce push failures
    if ($AutoStash) {
        & git pull --rebase --autostash $Remote $Branch
    } else {
        & git pull --rebase $Remote $Branch
    }
    if ($LASTEXITCODE -ne 0) {
        Fail "git pull --rebase failed (exit $LASTEXITCODE). Resolve and retry."
        exit 0
    }

    # Stage only convo dir
    & git add -A -- $ConvoDir
    if ($LASTEXITCODE -ne 0) {
        Fail "git add failed (exit $LASTEXITCODE)"
        exit 0
    }

    # Commit only if there is something staged
    & git diff --cached --quiet
    $hasStaged = ($LASTEXITCODE -ne 0)

    if ($hasStaged) {
        $commitMsg = "chore(sync): convo $AuthorId $stamp"
        & git commit -m $commitMsg
        if ($LASTEXITCODE -ne 0) {
            Fail "git commit failed (exit $LASTEXITCODE)"
            exit 0
        }

        & git push $Remote $Branch
        if ($LASTEXITCODE -ne 0) {
            Fail "git push failed (exit $LASTEXITCODE)"
            exit 0
        }

        Write-Host "[ConvoSend] Committed + pushed."
    } else {
        Write-Host "[ConvoSend] Nothing to commit (already up to date)."
    }

    exit 0
} finally {
    Pop-Location
}
