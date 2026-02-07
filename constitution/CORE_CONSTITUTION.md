# Core Constitution (Draft)

Effective date: 2026-02-06

This document records baseline constitutional invariants for the Sovereign system.

Note:
- This file is a **canonical documentation layer**.
- Enforcement is controlled by the existing signed policy artifacts in `constitution/` and by runtime enforcement code.

## 1. Non-Negotiable Invariants
- Evidence-first: prefer verifiable artifacts over claims.
- Viewer-first: produce auditable output before fail/stop gates.
- No fabrication: if evidence is missing, say so and request next evidence.
- No secrets in git: credentials and real-world evidence files must not be committed.
- Scoped operations: automation must operate on explicit allowlists.

## 2. Constitutional Triad (Formal Record)
The system uses a triad to produce canonical outputs:
- Specialist: generates structured draft output.
- Validator: performs safety/policy/evidence checks and flags issues.
- Arbiter: resolves conflicts and produces final canonical output with decision metadata.

Optional, non-mutative layers:
- Interpreter: simplifies the Arbiter output without changing verdict.
- Assistant discussion layer: explains and coaches without changing verdict.

Authoritative details are in `SOVEREIGN_MODEL_POLICY.md`.

## 3. Canonical Artifact Locations
- `constitution/`: policy and constitutional documents
- `Governance/`: governance specs and runbooks
- `docs/ops/`: operational documentation
- `validation/`: viewer-mode reports and receipts

## 4. Change Control
Any constitutional change should:
- be written into a tracked document (not only chat)
- include verification steps and expected artifacts
- avoid modifying signed policy artifacts unless the signing flow is run

