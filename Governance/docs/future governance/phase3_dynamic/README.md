# Phase 3 — Dynamic Automation (Scaffold)

Purpose:
- Host the self-executing automation layer that *operates within* the Constitution (Phase 2).
- Generate repeatable, auditable actions from local logs/ledgers without modifying sealed law.

Scope (scaffold-only):
- Scheduled/cadenced jobs (e.g. 2-hour loop review)
- Memo compilation + staging rules
- Owner “nudge” outputs (notifications are out-of-scope until explicitly wired)

Invariants:
- Phase 2 remains immutable: this phase reads constraints, does not rewrite them.
- All actions must emit verifiable logs (hash-chained where applicable).
