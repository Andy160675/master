# Phase 2B — Operational Verification (Skeleton)

## Status
- NOT ACTIVE
- Blocked by FREEZE
- Requires evidence: `TAMPER_TEST_RESULT=PASS`

---

## Purpose
Define a hostile-but-stable execution surface that can:
- execute verifier logic deterministically,
- against externally hosted artifacts,
- while retaining authority and evidence-of-record offline.

---

## Preconditions (Non-Negotiable)
- SiteGround tamper test PASS recorded as offline evidence.
- FREEZE explicitly lifted by an evidence-gated decision.
- Verifier code and policy artifacts authored offline and integrity-anchored (hashes recorded).

---

## Authority Model
- Policy: offline
- Evidence of record: offline
- Verifier code: offline authored, integrity-anchored
- Host (SiteGround): hostile execution surface

---

## Allowed Host Actions (Execution Surface)
- Read static verifier code
- Read externally hosted artifacts (read-only)
- Execute deterministic logic
- Emit unsigned, informational outputs labeled non-authoritative

---

## Forbidden Host Actions
- Policy edits or policy selection
- Signing
- Promotion decisions
- Creation or mutation of sovereign evidence
- Any authority claims

---

## Minimal File Layout (Conceptual)

/public_html/verifier/
  verifier.*              (static logic, if used)
  verifier_policy.*       (read-only)
  receipts/
    receipt_<hash>.*      (informational only; reproducible offline)

---

## Receipt Semantics
- Receipt is NOT evidence-of-record.
- Receipt is NOT authoritative.
- Receipt must be reproducible offline from inputs.

---

## Governance Boundary
- Phase 2B does not change promotion gating.
- Any trust elevation requires new evidence and an explicit decision.

---

## Exit Conditions
- Downgrade back to presentation-only.
- Or escalate to a subsequent phase only via new constitutional analysis.
