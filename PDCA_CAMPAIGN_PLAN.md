# PDCA Stabilization Campaign Plan (10 × 15)

Date: 2026-02-07

## Objective
Execute a repeatable, auditable stabilization campaign using the Sovereign Recursion PDCA loop runner.

- **Batch**: 10 loop iterations
- **Campaign**: 15 batches
- **Total iterations**: $10 \times 15 = 150$

The campaign is designed to be **repeatable**, **resumable**, and **evidence-first**.

## Execution Modes
- **Offline**: enabled by default (safe / no external dependencies)
- **Gated**: enabled by default (failures are classified and recorded)
- **Keep going**: enabled by default (`ContinueOnFail=true`) to finish the campaign and produce a complete evidence set.

## Evidence & Outputs
Default output root (when `-OutRoot` is not supplied):

- `sovereign_recursion/artifacts/pdca_campaigns/campaign_<stamp>/`
  - `batch_01/ .. batch_15/` (per-batch artifacts)
  - `campaign_summary.csv` (one row per batch)
  - `campaign_final.json` (final campaign outcome + ledger verify rc)

Ledger used by default:
- `validation/sovereign_recursion/ledger.jsonl`

## How to Run
### PowerShell (repo root)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-PDCA-Campaign.ps1 \
  -Batches 15 -IterationsPerBatch 10 -Offline -Gated -EmitAlerts -ContinueOnFail
```

### Resume / Repair an existing campaign

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-PDCA-Campaign.ps1 \
  -OutRoot .\sovereign_recursion\artifacts\pdca_campaigns\campaign_YYYYMMDD_HHMMSS \
  -Batches 15 -IterationsPerBatch 10 -Offline -Gated -EmitAlerts -ContinueOnFail
```

## Success Criteria
- All 15 batches complete and appear in `campaign_summary.csv`.
- `campaign_final.json` reports `failed_batches: 0`.
- Ledger verification succeeds (`ledger_verify_rc: 0`).
