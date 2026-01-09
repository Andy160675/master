# Agent Spine v1 — Runbook & Close-Out (Phase 2A)

## System status (as of 2026-01-09)

- **Agent Spine v1:** Implemented, runnable, pretested.
- **Verifier:** Deterministic PASS/FAIL using canonical SHA-256 hashing.
- **Training:** Placeholder only; does not train or deploy.
- **Promotion gate:** Active; always blocks deployment without approval.
- **Presentation host:** SiteGround remains frozen (presentation-only).
- **Authority:** Offline; no script writes to SiteGround or GitHub.
- **Evidence:** AI_LOCAL_INVENTORY.csv, AI_GIT_INVENTORY.txt, AI_SYSTEM_TOPOGRAPHY.md are generated on every run.

## Canonical execution (one command)

From the repository root on Windows with a fresh `.venv`:

```
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe agents\orchestration\agent_runner.py
```

Expected output sequence:

1. **Inventory** – scans local and Git files and writes `AI_LOCAL_INVENTORY.csv` and `AI_GIT_INVENTORY.txt`.
2. **Merge** – writes `AI_SYSTEM_TOPOGRAPHY.md`.
3. **Verifier** – reads `public_html/verifier/demo/valid.json`, prints `PASS`.
4. **Training placeholders** – print offline and eval messages.
5. **Promotion gate** – halts with  
   `DEPLOY BLOCKED — promotion approval required in registry/promotions.yaml`.

If you see anything else, stop and investigate.

## Replication / Portable nodes

To prepare an offline node (USB or another machine):

1. From your trusted machine:

```
mkdir ELITE_NODE_V1
robocopy . ELITE_NODE_V1 /E /XD .git .venv env __pycache__
```

2. Copy `python-3.11.x-amd64.exe` (or a suitable installer) to the USB root.

3. On the target machine:

```
cd ELITE_NODE_V1
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe agents\orchestration\agent_runner.py
```

This reproduces the exact behavior offline. Each node generates its own inventories and topography; no cross-sync occurs automatically.

## Evidence gate

The system’s further progression is **blocked by design** until the tamper test result is recorded:

```
TAMPER_TEST_RESULT=PASS  or  TAMPER_TEST_RESULT=FAIL
```

Do not attempt to run training, deploy to SiteGround, or modify promotion logs until this evidence is available.

## Final note

This runbook captures the complete state of Agent Spine v1. All future enhancements are **substitutions of internal logic**, not rewrites of the architecture or governance. This document is therefore intended to remain stable and be included with every copy of the system.
