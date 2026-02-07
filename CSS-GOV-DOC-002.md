# CSS-GOV-DOC-002 — Governance & Canonical Truth Integration (Canonical)

Status: Draft (canonical seed)

Effective date: 2026-02-06

## 0. Purpose
This document defines how “canonical truth” is recorded and maintained in this repository, and how governance is applied to operational automation.

## 1. Governance Principles
- **Evidence over assertion:** claims should be grounded in artifacts, logs, or deterministic checks.
- **Viewer-first, Gate-second:** always provide a non-destructive Viewer workflow; Gate is an explicit escalation.
- **Least privilege:** tools operate on explicitly scoped paths.
- **No credential guessing:** access must be provided by the operator; the system does not fabricate secrets.

## 2. Canonical Truth Rules
### 2.1 Canonical Sources
Canonical truth is encoded in:
- signed or versioned policy artifacts under `constitution/`
- governance specs under `Governance/`
- operational runbooks under `docs/ops/`
- reproducible scripts under `scripts/` and `scripts/ops/`

Chat logs and summaries are **inputs**; they only become canonical once written into:
- a document (like this one), or
- an executable script/task with auditable outputs.

### 2.2 Recording Canonical Updates
Every canonical update should include:
- what changed
- why it changed
- how to verify it
- what artifacts to review (paths under `validation/` or log locations)

## 3. Constitutional Triad (Formal)
The Sovereign decision pipeline is evaluated and emitted by a triad:
- **Specialist:** produces a structured draft.
- **Validator:** checks safety/policy/evidence anchors; flags or redacts.
- **Arbiter:** resolves conflicts and emits the final canonical output.

Additional roles (non-mutative):
- **Interpreter:** simplifies the Arbiter output without changing the verdict.
- **Assistant (discussion layer):** explains and coaches without altering the verdict.

Authoritative reference: `SOVEREIGN_MODEL_POLICY.md`.

## 4. Operational Controls
### 4.1 Git Hygiene
- Avoid `git add -A` in repositories that contain runtime artifacts.
- Automation must stage/commit **only** explicit paths (e.g., `sync_conversation/`).

### 4.2 Mirroring Controls
- Copy vs mirror are distinct modes.
- Mirror mode is destructive and must be explicit.
- Excludes must prevent copying `.git`, `env/`, `node_modules/`, `__pycache__/`, `evidence/`, and similar artifact directories.

### 4.3 Fleet Controls
- Fleet execution uses a queue + pull agent model.
- Commands must be auditable (log to JSONL) and produce receipts when possible.
- Gate mode is permitted only when the operator intends fail/stop semantics.

## 5. Audit Artifacts
Preferred artifacts include:
- `validation/**/*.json`
- JSONL logs with stable fields and timestamps
- hash-chained ledgers (prev_hash + hash)

## 6. Secure Cloud Folder Structure
The repository provides a **skeleton** structure under `secure_cloud/` for secure synchronized workflows.
- It is ignored by default.
- Only documentation and `.gitkeep` files are tracked.

## 7. Enforcement Notes
- Signed policy manifests under `constitution/` are treated as enforcement boundaries.
- Adding new constitutional documents does not automatically make them “enforced” until the signing/enforcement layer is updated.

