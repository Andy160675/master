[CmdletBinding()]
param(
    [string]$RepoRoot = "${PSScriptRoot}\\..\\..",
    [string]$ConvoDir = "${PSScriptRoot}\\..\\..\\sync_conversation",
    [string]$Remote = "origin",
    [string]$Branch = "main",
    [string]$AuthorId = $env:COMPUTERNAME,
    [int]$IntervalSeconds = 15,
    [switch]$AutoStash,
    [switch]$PullOnly,
    [switch]$Once,
    [switch]$Gate
)

$ErrorActionPreference = 'Stop'

function Fail([string]$msg) {
    Write-Error $msg
    if ($Gate) { exit 1 }
}

function New-StampUtc { (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') }

function Ensure-RepoCleanState([string]$repoRoot) {
    $gitDir = Join-Path $repoRoot '.git'
    if (-not (Test-Path -LiteralPath $gitDir)) {
        throw "Not a git repo root (or .git missing): $repoRoot"
    }

    # If a rebase/merge is in progress, fail fast (don’t automate through it)
    $rebaseApply = Join-Path $gitDir 'rebase-apply'
    $rebaseMerge = Join-Path $gitDir 'rebase-merge'
    $mergeHead = Join-Path $gitDir 'MERGE_HEAD'

    if ((Test-Path -LiteralPath $rebaseApply) -or (Test-Path -LiteralPath $rebaseMerge) -or (Test-Path -LiteralPath $mergeHead)) {
        throw "Git operation in progress (rebase/merge). Resolve manually before running the loop."
    }
}

try { $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path } catch {}

if ($IntervalSeconds -lt 5) { $IntervalSeconds = 5 }

Push-Location -LiteralPath $RepoRoot
try {
    Ensure-RepoCleanState $RepoRoot

    if (-not (Test-Path -LiteralPath $ConvoDir)) {
        New-Item -ItemType Directory -Force -Path $ConvoDir | Out-Null
    }

    Write-Host "[ConvoLoop] Repo:      $RepoRoot"
    Write-Host "[ConvoLoop] ConvoDir:  $ConvoDir"
    Write-Host "[ConvoLoop] Remote:    $Remote"
    Write-Host "[ConvoLoop] Branch:    $Branch"
    Write-Host "[ConvoLoop] AuthorId:  $AuthorId"
    Write-Host "[ConvoLoop] Interval:  ${IntervalSeconds}s"
    Write-Host "[ConvoLoop] Mode:      " -NoNewline
    if ($PullOnly) { Write-Host "PullOnly" } else { Write-Host "Pull/Rebase + AutoCommit ConvoDir + Push" }

    while ($true) {
        try {
            Ensure-RepoCleanState $RepoRoot

            & git diff --quiet
            $dirtyWorktree = ($LASTEXITCODE -ne 0)
            & git diff --cached --quiet
            $dirtyIndex = ($LASTEXITCODE -ne 0)

            if (($dirtyWorktree -or $dirtyIndex) -and (-not $AutoStash)) {
                Fail "Repo has local changes; refusing to pull/rebase. Re-run with -AutoStash to allow git to stash/apply automatically."
                if ($Gate) { exit 1 }
                break
            }

            if ($AutoStash) {
                & git pull --rebase --autostash $Remote $Branch
            } else {
                & git pull --rebase $Remote $Branch
            }
            if ($LASTEXITCODE -ne 0) {
                Fail "git pull --rebase failed (exit $LASTEXITCODE). Resolve and rerun."
                if ($Gate) { exit 1 }
                break
            }

            if (-not $PullOnly) {
                # Stage only the conversation dir
                & git add -A -- $ConvoDir
                if ($LASTEXITCODE -ne 0) {
                    Fail "git add failed (exit $LASTEXITCODE)"
                    if ($Gate) { exit 1 }
                    break
                }

                & git diff --cached --quiet
                $hasStaged = ($LASTEXITCODE -ne 0)

                if ($hasStaged) {
                    $stamp = New-StampUtc
                    $commitMsg = "chore(sync): convo sync $AuthorId $stamp"
                    & git commit -m $commitMsg
                    if ($LASTEXITCODE -ne 0) {
                        Fail "git commit failed (exit $LASTEXITCODE)"
                        if ($Gate) { exit 1 }
                        break
                    }

                    & git push $Remote $Branch
                    if ($LASTEXITCODE -ne 0) {
                        Fail "git push failed (exit $LASTEXITCODE)"
                        if ($Gate) { exit 1 }
                        break
                    }

                    Write-Host "[ConvoLoop] Synced at $stamp" -ForegroundColor Green
                } else {
                    Write-Host "[ConvoLoop] No local convo changes." -ForegroundColor DarkGray
                }
            }

            if ($Once) { break }
            Start-Sleep -Seconds $IntervalSeconds
        } catch {
            Fail $_.Exception.Message
            if ($Gate) { exit 1 }
            break
        }
    }

    exit 0
} finally {
    Pop-Location
}
