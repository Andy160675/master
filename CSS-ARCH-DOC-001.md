# CSS-ARCH-DOC-001 — Sovereign System Architecture (Canonical)

Status: Draft (canonical seed)

Effective date: 2026-02-06

## 0. Purpose
This document records the **canonical architecture** of the Sovereign system as implemented in this repository.

It exists to:
- make the system reproducible across nodes
- define the boundaries between **code**, **runtime data**, and **evidence artifacts**
- keep operational changes auditable and low-risk

## 1. Scope
In-scope:
- local/offline-first operation across a small fleet (Windows + NAS/Linux)
- evidence-first pipelines with deterministic verification artifacts
- controlled deployment and synchronization mechanisms

Out-of-scope:
- storing or transmitting secrets in-repo
- automatic broad data movement without explicit target paths

## 2. Architectural Invariants (Non-Negotiables)
- **Evidence-first:** outputs must be reviewable; never “trust the model” without verification.
- **Viewer-first operations:** provide a Viewer mode (collect/report) before Gate mode (fail/stop).
- **Scoped change:** never use blanket operations (e.g., repository-wide staging or destructive mirroring) without explicit allowlists.
- **No secret material in git:** runtime data, evidence files, and credentials are excluded by `.gitignore`.

## 3. Major Components
### 3.1 Ops Orchestration (VS Code Tasks + PowerShell)
- Primary entrypoint: `.vscode/tasks.json`
- Scripts: `scripts/ops/` and `scripts/`
- Pattern:
  - Viewer task produces artifacts under `validation/`.
  - Gate task fails the task when a policy or integrity violation is detected.

### 3.2 Fleet Execution (Windows: NAS Queue Agent)
- Queue writer: `scripts/Queue-Command.ps1`
- Node agent: `scripts/FleetPullAgent.ps1`
- Bootstrap: `scripts/FleetBootstrap.ps1`

Mechanism:
- Command files are dropped under a NAS UNC path (default `\\dxp4800plus-67ba\ops\Queue\<node>`).
- Each node’s `FleetPullAgent.ps1` polls its queue directory, executes commands, and produces `.done` receipts.
- Node logs are written to `C:\ops\logs\*.jsonl` and can be shipped to the NAS via `scripts/Ship-Logs.ps1`.

### 3.3 Cross-IDE Conversation Sync (Git-scoped)
- Tracked area: `sync_conversation/`
- Send/loop scripts:
  - `scripts/ops/Sync-ConvoSend.ps1`
  - `scripts/ops/Sync-ConvoLoop.ps1`

Invariant:
- Only `sync_conversation/` is staged/committed by automation; this prevents accidental staging of runtime artifacts.

### 3.4 Sovereign DNS (Phase 2) — NAS Resolver + Audit Ledger (Docker)
- Bundle: `services/sovereign_dns/`
- Deployment scripts:
  - `scripts/ops/SovereignDNS-Preflight.ps1`
  - `scripts/ops/Deploy-SovereignDNS-Docker.ps1`
  - `scripts/ops/Test-SovereignDNS.ps1`

Design:
- Unbound resolver in Docker exposes TCP/UDP 53.
- Sidecar tails DNS logs and appends to a hash-chained JSONL ledger.

## 4. Data Boundaries
- `data/`: runtime state (ignored by default)
- `evidence/`: evidence artifacts (ignored by default, allowlisted subtrees only)
- `validation/`: viewer-mode outputs and receipts
- `secure_cloud/`: optional synchronized folder skeleton (ignored by default)

## 5. Verification & Audit
Preferred verification outputs:
- JSON reports under `validation/…`
- Hash-chained JSONL ledgers for event trails
- Optional `.sha256` receipts where available

## 6. Known Operational Blockers (Non-code)
Some actions require operator-provided access:
- NAS SSH access (key-based or authorized user)
- NAS share authentication to write to the fleet queue path

## 7. Change Control
Any architecture change should include:
- updated tasks/scripts
- updated verification artifacts
- documentation updates (this file + governance spec)

