# ✅ Verification Checklist — Phase 2.5 (Audit-Grade)

## A) Repo + State Anchors (10 seconds)
- `git rev-parse --show-toplevel`
- `git branch --show-current`
- `git rev-parse HEAD`
- `git tag -l | sort`

## B) Tag Proof
- `git show PHASE-2_5-ENGINE-LIVE --no-patch --decorate`
- `git rev-parse PHASE-2_5-ENGINE-LIVE^{}`

## C) Seal Evidence Pack Proof
- List capsules:
  - `dir evidence\phase2_5_engine_live`
- Inspect most recent capsule:
  - `dir evidence\phase2_5_engine_live\<timestamp>`
- Verify manifest exists:
  - `type evidence\phase2_5_engine_live\<timestamp>\sha256_manifest.txt`

## D) Phase 2 Dashboard Proof (if present)
- `Get-FileHash -Algorithm SHA256 evidence/session-logs/dashboard_8787_20260105T122756Z.png`

## E) Dry-Run Outreach-0 (governed runtime)
- `./scripts/ops/break_outreach0.ps1`

Expected outputs:
- `evidence/session-logs/outreach0_<timestamp>/00_head.txt`
- `evidence/session-logs/outreach0_<timestamp>/02_daily_report_output.txt`
- `evidence/session-logs/outreach0_<timestamp>/03_snapshot_sha256.txt`
