# Agent Spine v1 — Replication Runbook (Canonical)

**Purpose:** deterministically reproduce the sealed baseline on any machine (PC, laptop, air-gapped USB) with no drift.

## Prerequisites

* Git installed
* Python **3.11** available as `py -3.11` (Windows) or `python3.11`
* No internet required after clone (except for initial fetch)

---

## 1) Clone & pin to the sealed baseline

```bash
git clone <REPO_URL>
cd <REPO_NAME>
git fetch --tags
git checkout agent-spine-v1-sealed
```

**Verify pin:**

```bash
git rev-parse HEAD
# expect: e1e991ec126736bbf541cac7fb6a11bb0db6a52c
```

---

## 2) Create an isolated runtime (no artifacts copied)

**Windows:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe --version
```

**macOS/Linux:**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python --version
```

---

## 3) Run the spine (expected hard stop)

```bash
# Windows
.\.venv\Scripts\python.exe agents\orchestration\agent_runner.py

# macOS/Linux
python agents/orchestration/agent_runner.py
```

**Expected behavior (by design):**

* Inventory runs
* Topography merges
* Verifier prints `PASS`
* Training/eval placeholders run
* **Promotion gate halts** with:

  ```
  DEPLOY BLOCKED — promotion approval required in registry/promotions.yaml
  ```

This confirms correct replication.

---

## 4) USB / air-gapped replication (optional)

On source machine:

```powershell
.\scripts\export_elite_node.ps1
```

On target machine:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe agents\orchestration\agent_runner.py
```

---

## Notes

* Do **not** run from `main` for v1 replication—always use the tag.
* Do **not** copy `.venv`, `env`, or build outputs between machines.
* All future work should branch **after** `agent-spine-v1-sealed`.
