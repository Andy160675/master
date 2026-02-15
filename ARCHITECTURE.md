# Sovereign Elite OS — Governance Architecture (Grounded)

**Status:** Authoritative
**Scope:** Maps governance concepts to *actual code*
**Rule:** Nothing in this document implies functionality that does not exist

---

## 0. Purpose of This Document

This file exists to do one thing only:

> **Map governance intent to concrete implementation.**

It distinguishes clearly between:

* what is **implemented**
* what is **partially implemented**
* what is **explicitly planned but not present**

Any concept not mapped to code here **does not exist in the system**.

---

## 1. Canonical Model (Target, Not Assumed)

The long-term governance target is a **layered model with strict separation of function**:

| Canonical Layer | Function                                | Operational Alias         |
| --------------- | --------------------------------------- | ------------------------- |
| L0              | Human Accountability                    | Accountable Officer       |
| L1              | Context Preservation & Decision Support | Paperclip (alias)         |
| L2              | Hard Constraint Enforcement             | Sentinel                  |
| L3              | Drift & Pattern Detection               | Watchtower                |
| L4              | Separation of Duties                    | (Architectural invariant) |
| L5              | Process Conformance Attestation         | Sovereign Seal            |
| L6              | Evidence & Memory Integrity             | Ledger                    |

**Important:**
This table is a *reference model*.
Only layers mapped in Section 2 are implemented.

---

## 2. Implemented Layers (Code-Backed)

### Layer 1 — Context Preservation & Decision Support

**Alias:** Paperclip
**Status:** IMPLEMENTED (partial)

**Primary file(s):**

* `agi/core/assistant_channel.py`

**What exists:**

* Explanatory assistant channel
* Provides reasoning / discussion
* Cannot override verdicts
* Cannot escalate or block actions

**What it is:**

* A *discussion layer*
* A context and explanation surface

**What it is not:**

* Not authoritative
* Not a gate
* Not an approver

This is the **closest concrete implementation** of the original "Paperclip" idea.

---

### Layer 2 — Hard Constraint Enforcement

**Alias:** Sentinel
**Status:** IMPLEMENTED

**Primary file(s):**

* `agi/core/mcp_gatekeeper.py`
* `agi/core/diff_validator.py`
* `agi/core/policy_signature.py`
* `agi/core/empathy_engine.py`

**What exists:**

* AST diffing (blocks unsafe Python constructs)
* Policy signature verification (SHA256)
* Deterministic allow / block behavior
* Crisis language detection and coercion blocking

**Properties:**

* Binary enforcement
* No discretion
* Logged decisions

This is a true **gate**, not an assistant.

---

### Layer 3 — Drift & Pattern Detection

**Alias:** Watchtower
**Status:** IMPLEMENTED (minimal)

**Primary file(s):**

* `agi/core/drift_detector.py`
* `agi/core/drift_store.sqlite`

**What exists:**

* SHA256 tracking of two files (`SOVEREIGN_MODEL_POLICY.md`, `agi/core/model_stack.yaml`)
* Baseline storage in SQLite
* Change detection on every triad run
* `drift_detected` flag in receipts

**What it is:**

* A minimal drift detector

**What it is not yet:**

* No trend aggregation
* No periodic scheduled analysis
* No reporting layer
* No HARLS metric integration

---

### Layer 6 — Evidence & Memory Integrity

**Alias:** Ledger
**Status:** IMPLEMENTED

**Primary file(s):**

* `src/recorder/core.py`
* `agi/core/receipt.py`
* `config/recorder_config.yaml`
* `schemas/event_*.json`

**What exists:**

* Append-only JSONL ledger
* Hash-based JSON receipts (7+ actual receipt files in `agi/core/receipts/`)
* JSON Schema validation for events
* CI ledger integrity check (`.github/workflows/ledger-integrity.yml`)
* C++ evidence verifier (`src/verifier/`)

This layer is **solid and real**.

---

## 3. HARLS Theory — Correct Placement

**Status:** NOT IN THIS REPO

HARLS is:

* a **measurement theory**
* a **coherence invariant**
* a **diagnostic substrate**

HARLS is **not**:

* a governance layer
* an enforcement mechanism
* a policy profile

Current status:

* No HARLS spec file exists in this repository
* No HARLS rate computed in code
* No coherence ratio enforced
* No thresholds wired to Sentinel

HARLS is **conceptually referenced but not operationally present**.

---

## 4. Non-Implemented Concepts (Explicitly Not Present)

The following **do not exist in code** and should not be assumed:

* Sanctuary layer / mode
* Named constructs register
* HARLS-driven Sentinel thresholds
* Watchtower HARLS reporting
* Sovereign Seal automation (multi-chain anchoring is placeholder only)
* QMS documentation
* Panel Protocol
* Removal Framework
* Universal Access Doctrine

These may be future work, but they are **not part of the current system**.

---

## 5. Naming Clarification (Operational Honesty)

* **Paperclip** is the operational alias for Layer 1
* Canonical names are used for documentation and audit
* Aliases are human-facing only
* Names do not confer authority

---

## 6. Design Rule Going Forward

> **No governance concept may be added to documentation unless it is either:**
>
> 1. implemented in code, or
> 2. explicitly marked as planned

This prevents architectural inflation.

---

## 7. Next Legitimate Step (Single-Track)

The next *non-expansive* step is **one of**:

* Integrate HARLS metrics into Watchtower (measurement only), **or**
* Wire HARLS thresholds to Sentinel (hard gate), **or**
* Formalize Paperclip behavior in code (not prose)

Only one. Not all three.

---

## 8. Final Statement

This system is small, real, and honest.
It enforces boundaries.
It records evidence.
It explains itself.

Everything else is optional — and must earn its place in code.

---

## Related Documents

* [`docs/LAYER_MAP.md`](docs/LAYER_MAP.md) — Detailed per-layer gap analysis with full file paths
* [`SOVEREIGN_MODEL_POLICY.md`](SOVEREIGN_MODEL_POLICY.md) — Model policy specification (v0.1a)
* [`SOVEREIGN_IMPLEMENTATION_STATUS.md`](SOVEREIGN_IMPLEMENTATION_STATUS.md) — Honest self-assessment
* [`Codex/CHARTER.md`](Codex/CHARTER.md) — Governance charter

---

*Generated: 2026-02-15. Grounded against actual codebase.*
