param(
  [Parameter(Mandatory=$false)]
  [string]$GovernanceRoot = "Governance"
)

$ErrorActionPreference = 'Stop'

function Ensure-Dir([string]$p) {
  if (-not (Test-Path -LiteralPath $p)) {
    New-Item -ItemType Directory -Force -Path $p | Out-Null
  }
}

function Ensure-File([string]$path, [string]$content) {
  if (-not (Test-Path -LiteralPath $path)) {
    $parent = Split-Path -Parent $path
    Ensure-Dir $parent
    $content | Out-File -Encoding utf8 -LiteralPath $path
  }
}

$docsRoot = Join-Path $GovernanceRoot 'docs'
$futureGov = Join-Path $docsRoot 'future governance'
$phase3 = Join-Path $futureGov 'phase3_dynamic'
$phase4 = Join-Path $GovernanceRoot 'phase4_chain'

Ensure-Dir $phase3
Ensure-Dir $phase4

Ensure-File (Join-Path $futureGov 'README.md') @"
# Future Governance (Roadmap)

- Phase 2: Constitution (immutable law)
- Phase 3: Dynamic automation (self-executing operating logic)
- Phase 4: Chain substrate (trust + permanence)

This folder contains scaffolds only; no runtime assumptions.
"@

Ensure-File (Join-Path $phase3 'README.md') @"
# Phase 3 — Dynamic Automation (Scaffold)

Purpose:
- Host the self-executing automation layer that operates within the Constitution (Phase 2).
- Generate repeatable, auditable actions from local logs/ledgers without modifying sealed law.

Scope (scaffold-only):
- Scheduled/cadenced jobs (e.g. 2-hour loop review)
- Memo compilation + staging rules
- Owner “nudge” outputs (notifications are out-of-scope until explicitly wired)

Invariants:
- Phase 2 remains immutable: this phase reads constraints, does not rewrite them.
- All actions must emit verifiable logs (hash-chained where applicable).
"@

Ensure-File (Join-Path $phase4 'README.md') @"
# Phase 4 — Chain Substrate (Scaffold)

Purpose:
- Provide the trust substrate for permanence and verification.
- Keep the system verifiable even when copied/mirrored.

Scope (scaffold-only):
- Hash-chain conventions for JSONL ledgers
- Anchoring/export formats (Merkle/anchor bundles) for future decentralization

Invariants:
- Chain is append-only.
- Verification must be deterministic and reproducible.
"@

Write-Host "[roadmap] Phase 3 + Phase 4 scaffold ensured." -ForegroundColor Green
Write-Host "[roadmap] Phase 3: $phase3" -ForegroundColor Green
Write-Host "[roadmap] Phase 4: $phase4" -ForegroundColor Green
