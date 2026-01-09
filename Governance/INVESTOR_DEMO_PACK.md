# Investor Demo Pack — Agent Spine v1 (Sealed)

## The two anchors (share these)

- Engineering baseline (immutable): tag `agent-spine-v1-sealed`
- Replication runbook (docs): [Governance/REPLICATION_RUNBOOK.md](REPLICATION_RUNBOOK.md)

## What this is / isn’t

**This is:** a deterministic, offline-first governance spine that runs an agent pipeline and then *stops itself* at a promotion gate.

**This is not:** a “live AI that can deploy things.” The differentiator is *restraint + proof*, not theatrics.

## Demo modes (pick one)

### A) Demo-safe (static, zero mutation)

Open this file in a browser:

- [public_html/verifier/phase2a_precomputed.html](../public_html/verifier/phase2a_precomputed.html)

What it shows:
- The two demo artifacts (`valid.json` / `invalid.json`)
- The precomputed expected outcomes (PASS / FAIL)
- Explicit guardrails: no hashing, no verification, no receipts on the surface

### B) Full functionality (local, deterministic hard stop)

1) Pin the sealed baseline:

```bash
git fetch --tags
git checkout agent-spine-v1-sealed
```

2) Create runtime:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3) Run:

```powershell
.\.venv\Scripts\python.exe agents\orchestration\agent_runner.py
```

**PASS criteria:**
- Inventory + topography run
- Verifier PASS on `valid.json` and FAIL on `invalid.json`
- Hard stop at the governance gate: `DEPLOY BLOCKED — promotion approval required`

## Hosted demo rule (FREEZE-compliant)

Allowed:
- `https://<site>/verifier/phase2a_precomputed.html` (static)

Not allowed:
- Any server-side verifier, API, uploads, writable state, or “live evaluation” surface

## Talk track (60 seconds)

- “We’re demonstrating governance that prevents unsafe action.”
- “The pipeline runs deterministically, produces auditable artifacts, and then halts at an approval gate.”
- “The hosted surface is intentionally non-authoritative: it only shows static, precomputed proof.”

## FAQ (short)

- **Why does it stop?** Because promotion requires an explicit, auditable human approval entry.
- **Where is truth decided?** Offline, by verifying hashes from retrieved files.
- **What’s next?** v2 work is additive capability, not stabilization.
