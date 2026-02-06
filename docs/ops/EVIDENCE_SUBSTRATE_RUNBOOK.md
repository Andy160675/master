# Evidence Substrate (SMB) — Mount + Measure

This runbook operationalizes the invariant:
**decorrelated validation + explicit accountability + disagreement telemetry**.

## 1) Mount the substrate (S:)
Recommended: map a drive letter to the evidence share.

Task:
- `Ops: Mount Evidence Share (S:)`

## 2) Capture a baseline (hashes + merkle root)
Task:
- `Ops: Capture Evidence Baseline (S:)`

Artifacts:
- `validation/evidence_baseline/evidence_baseline_<stamp>.json`
- `validation/evidence_baseline/evidence_baseline_summary_<stamp>.json`
- `.sha256` receipts for each JSON

## 3) Compare baselines (disagreement telemetry)
Task:
- `Ops: Compare Evidence Baselines (Gate on mismatch)`

Outcome:
- If hashes differ, treat as investigation trigger.

## Notes
- These scripts are **viewer-first**: they do not modify remote content.
- Drive mapping is a local state change; credentials are never written to disk by these scripts.

## 4) Cross-node agreement (decorrelated validation)
Pattern:
- Each node captures a baseline **to the shared substrate** under a node-specific folder.
- A collector reads the latest baseline summary from each node folder.
- Any disagreement (different Merkle roots) becomes investigation telemetry and can fail-stop.

Recommended publication layout:
`\\<share>\baselines\<NodeId>\evidence_baseline_summary_*.json`

Collector task:
- `Ops: Verify Evidence Agreement (Gate)`
