# Layer Map: Canonical Architecture to Codebase

> Single source of truth mapping the governance layer model to actual files.
> Canonical names are stable (audit/legal). Operational aliases are human-friendly.
> Status is honest: `DONE`, `PARTIAL`, `NOT STARTED`.

---

## Substrate — HARLS (Measurement Theory)

**Not a layer. A measurement substrate that justifies and constrains the layers above.**

| Field | Value |
|-------|-------|
| Canonical name | HARLS Theory |
| Purpose | Measurement and coherence-rate theory for information preservation across transformations |
| Status | `NOT STARTED` |
| Location | *(no code or spec exists in this repo)* |
| Notes | HARLS measures. It does not govern. It defines the Harls Rate, coherence ratios, and drift as a measurable signal. Spec exists in external conversations but has not been committed. |

---

## Layer 0 — Human Accountability & Authority

| Field | Value |
|-------|-------|
| Canonical name | Human Accountability & Authority |
| Industry analogue | Accountable Officer / Responsible Person |
| Purpose | A named human is always accountable for outcomes |
| Status | `PARTIAL` |
| Location | `Codex/CHARTER.md` |
| Notes | Charter exists and establishes governance principles. No formal accountable-person register or sign-off mechanism is implemented in code. The triad (`agi/core/triad_harness.py`) requires human-initiated runs — no autonomous triggers exist. |

**Invariant:** No system action exists without an accountable human anchor.

---

## Layer 1 — Context Preservation & Decision Support

| Field | Value |
|-------|-------|
| Canonical name | Context Preservation & Decision Support |
| Industry analogue | Decision Support System (DSS) |
| Operational alias | Paperclip / Rubber Stamp |
| Purpose | Ever-present, low-ego companion that preserves context and surfaces misalignment. No authority. No escalation. |
| Status | `PARTIAL` |
| Location | `agi/core/assistant_channel.py` |
| Notes | The assistant channel explains and discusses existing Sovereign verdicts without altering them. It can clarify, provide examples, and highlight trade-offs. If it detects a serious error, it requests a re-run rather than overriding. This is the discussion/explanation facet of the companion role. The persistent ambient "nudge during workflows" facet is not yet built. |

**Invariant:** Assistance must never imply approval.

**What exists:**
- System prompt constraining the assistant to explain, not alter (`ASSISTANT_SYSTEM_PROMPT`)
- SQLite-backed message thread per answer (`assistant_messages` table)
- Prompt hash tracked for drift detection
- `RE-RUN RECOMMENDED` signal protocol

**What's missing:**
- Ambient presence in IDE/terminal/UI workflows
- Proactive context surfacing (prior decisions, dropped assumptions)
- Pressure-pattern visibility ("this decision is justified by urgency, not criteria")

---

## Layer 2 — Hard Constraint Enforcement

| Field | Value |
|-------|-------|
| Canonical name | Hard Constraint Enforcement |
| Industry analogue | Safety Interlocks / Control Gates |
| Operational alias | Sentinel |
| Purpose | Binary allow/stop at hard boundaries. No discretion once triggered. |
| Status | `PARTIAL` |
| Location | `agi/core/mcp_gatekeeper.py`, `agi/core/diff_validator.py`, `agi/core/policy_signature.py`, `agi/core/empathy_engine.py` |
| Notes | The MCP Gatekeeper combines AST-level diff validation (blocks unsafe Python constructs) with policy signature verification. The Empathy Engine detects crisis language and blocks coercive output. These are real, working gates — but they cover **code changes** and **language safety**, not the full Sentinel domain (safeguarding, finance, authority misuse, irreversibility). |

**Invariant:** Some constraints are binary and non-discretionary.

**What exists:**
- AST diff validator blocking Try/Assert/Raise/AsyncFunctionDef/YieldFrom (`diff_validator.py`)
- Policy manifest SHA256 signature check (`policy_signature.py`)
- Fail-closed gatekeeper combining both (`mcp_gatekeeper.py`)
- Crisis language detection + coercion blocking (`empathy_engine.py`)
- Trauma-informed communication constraints (`standards.py`)

**What's missing:**
- Safeguarding boundary triggers
- Financial harm gates
- Authority misuse detection
- Irreversibility checks
- Documented trigger conditions per domain

---

## Layer 3 — Retrospective Analysis & Drift Detection

| Field | Value |
|-------|-------|
| Canonical name | Retrospective Analysis & Drift Detection |
| Industry analogue | Audit / QA / Risk Monitoring |
| Operational alias | Watchtower |
| Purpose | Detect slow erosion, normalization of deviance, and pattern drift. Reports only. No real-time intervention. |
| Status | `PARTIAL` |
| Location | `agi/core/drift_detector.py`, `agi/core/drift_store.sqlite` |
| Notes | SHA256-hashes `SOVEREIGN_MODEL_POLICY.md` and `model_stack.yaml`, stores baselines in SQLite, detects mismatches. Sets `drift_detected=true` in receipts. This is real drift detection — but it only tracks 2 files and runs per-invocation, not on a periodic schedule. |

**Invariant:** Patterns are assessed retrospectively, not acted on in real time.

**What exists:**
- Baseline hash storage in `drift_store.sqlite`
- Per-run drift check in `triad_harness.py`
- `drift_detected` flag in receipts
- `stale_policies` signal in agent triad pattern map (HIGH severity)

**What's missing:**
- Periodic scheduled analysis (quarterly, monthly)
- Pattern aggregation across multiple runs
- Normalization-of-deviance detection
- Trend reports and evidence packs
- Coverage beyond 2 files

---

## Layer 4 — Separation of Authority, Function, and Tempo

| Field | Value |
|-------|-------|
| Canonical name | Separation of Authority, Function, and Tempo |
| Industry analogue | Segregation of Duties |
| Purpose | No single component may assist, observe, and enforce. |
| Status | `PARTIAL` |
| Location | *(architectural, not a single file)* |
| Notes | The Specialist/Validator/Arbiter triad enforces role separation within the decision pipeline. The RBAC model in `agi/core/agent_identity.py` defines distinct roles (`observer`, `scout`, `executor`, `guardian`) with separate tool allowlists. However, there is no formal enforcement that Layer 1/2/3 components cannot cross boundaries, and the phrase "separation of duties" appears nowhere in the codebase. |

**Invariant:** Rubber Stamp =/= Sentinel =/= Watchtower. No cross-promotion. No emergency overrides.

**What exists:**
- Triad role separation (Specialist/Validator/Arbiter cannot override each other)
- RBAC agent identities with distinct tool budgets (`agent_identity.py`)
- Assistant channel explicitly barred from altering verdicts

**What's missing:**
- Formal layer-boundary enforcement
- Cross-layer audit (did Layer 1 ever act like Layer 2?)
- Documented anti-collapse rules

---

## Layer 5 — Process Conformance Attestation

| Field | Value |
|-------|-------|
| Canonical name | Process Conformance Attestation |
| Industry analogue | Conformance Attestation |
| Operational alias | Sovereign Seal |
| Purpose | Mechanical attestation that process completed and constraints held. Does not imply correctness, quality, or endorsement. |
| Status | `PARTIAL` |
| Location | `agi/core/receipt.py`, `agi/core/receipts/`, `scripts/seal_ledger_hash.ps1`, `docs/audit/SEAL_v1.0.0-sovereign.md` |
| Notes | JSON receipts are generated per triad run with hashes, model IDs, drift flags, and policy versions. Ledger sealing via SHA256 exists. The SEAL document claims multi-chain anchoring (Bitcoin, Ethereum, Solana, Cosmos, Polkadot) but all chain identifiers are placeholders (`txid_here`). The multi-chain anchoring did not happen. |

**Invariant:** Conformance is not approval.

**What exists:**
- Per-run JSON receipts with full audit fields (`receipt.py`)
- 7+ actual receipt files in `agi/core/receipts/`
- SQLite-backed `sovereign_answers` table
- Ledger hash sealing script (`seal_ledger_hash.ps1`)

**What's missing:**
- Multi-chain anchoring (placeholders only)
- Formal Seal application criteria (when exactly does the Seal apply?)
- Seal vs. non-Seal distinction in receipts

---

## Layer 6 — Evidence, Ledger, and Memory Integrity

| Field | Value |
|-------|-------|
| Canonical name | Evidence, Ledger, and Memory Integrity |
| Industry analogue | Audit Trail / Records Management |
| Purpose | Append-only, deterministic, time-anchored evidence. Assertions without evidence do not exist. |
| Status | `DONE` |
| Location | `src/recorder/core.py`, `config/recorder_config.yaml`, `schemas/`, `.github/workflows/ledger-integrity.yml` |
| Notes | The Recorder writes one JSON event per line in append mode. Event types are validated against JSON Schemas. CI verifies ledger hash integrity. This is the most concretely implemented layer. |

**Invariant:** Nothing important exists unless it leaves a trace.

**What exists:**
- Append-only JSONL recorder (`src/recorder/core.py`)
- Config-driven ledger path and node ID (`config/recorder_config.yaml`)
- JSON Schema validation for events (`schemas/event_*.json`, `agi/core/recorder_schema.py`)
- CI ledger integrity check (`.github/workflows/ledger-integrity.yml`)
- Evidence validator agent (`src/agents/evidence_validator.py`)
- C++ Verify-Evidence binary (`src/verifier/`)

---

## Pressure Field — Pranus (Named Failure Mode, Not a Layer)

Pranus is the ambient pressure environment that bends governance systems:
- urgency, deadlines
- narrative capture, optics
- "just this once"
- convenience drift
- seniority bias
- institutional gravity

**Containment by layer:**
- Layer 1 (Rubber Stamp) — makes pressure visible
- Layer 3 (Watchtower) — measures pressure over time
- Layer 2 (Sentinel) — blocks pressure at boundaries

**Implementation status:** `NOT STARTED` — no code explicitly identifies or surfaces pressure patterns.

---

## Governance Documents (Outside the Layer Stack)

These exist as human-readable documents, not machine-enforced policy:

| Document | Location | Status |
|----------|----------|--------|
| Charter | `Codex/CHARTER.md` | Exists |
| Sovereign Model Policy | `SOVEREIGN_MODEL_POLICY.md` | Exists (v0.1a) |
| Policy Manifest | `constitution/policy_manifest.yml` + `.sig` | Exists, signature-verified |
| Empathy Constitution | `agi/constitution/empathy_v1.1.yaml` | Exists |
| Implementation Status | `SOVEREIGN_IMPLEMENTATION_STATUS.md` | Exists (honest self-assessment) |
| QMS | *(not in repo)* | Not started |
| Panel Protocol | *(not in repo)* | Not started |
| Removal Framework | *(not in repo)* | Not started |
| Universal Access Doctrine | *(not in repo)* | Not started |

---

## Principles of Operation

- **HARLS measures.** It does not govern.
- **Rubber Stamp accompanies.** It does not command.
- **Watchtower observes.** It does not intervene.
- **Sentinel blocks.** It does not interpret.
- **Recorder keeps truth.** It does not edit.
- **Receipts verify.** They do not obscure.
- **Governance authors policy.** It does not execute.

**The separation is the architecture.** Collapse any two layers and the system rots.

---

*Generated: 2026-02-15. Grounded against actual codebase, not aspirational documentation.*
