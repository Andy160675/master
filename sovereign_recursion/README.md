# Sovereign Recursion (repo-local)

This folder is a cross-platform, Python-first implementation of a minimal **Sovereign Recursion Engine**.

Core properties:
- **Append-only evidence ledger**: `validation/sovereign_recursion/ledger.jsonl`
- **Per-run artifacts**: `validation/sovereign_recursion/run_<UTCSTAMP>/run_report.json`
- **No hidden authority**: checks report `STABLE/DEGRADED/WARNING/UNKNOWN` (not “truth”)

## Run

- Engine run (writes a run report + appends to ledger):
  - `python -m sovereign_recursion --rating 4 --nas-host 192.168.4.114`

- Gated run (non-zero exit if any layer is `DEGRADED/OVERLOADED/CORRUPTED`):
  - `python -m sovereign_recursion --gated --rating 4 --nas-host 192.168.4.114`

- Offline run (skips outbound probes; useful for deterministic runs/tests):
  - `python -m sovereign_recursion --offline --rating 4`

Layers include `codex` (required Codex docs present + SHA256 evidence).

## Ledger

- Verify chaining + hashes:
  - `python -m sovereign_recursion.ledger verify`

- Tail entries:
  - `python -m sovereign_recursion.ledger tail -n 20`

## Dashboard

- Generate HTML dashboard from the ledger:
  - `python -m sovereign_recursion.dashboard --output validation/sovereign_recursion/sovereignty_dashboard.html`

## Unified Loop Runner

This is the smallest repeatable stabilization primitive:

`collect signals → compare invariants (gate) → bounded retry (act) → append evidence (record)`

- Run once (offline + gated):
  - `python -m sovereign_recursion.loop_runner --iterations 1 --offline --gated --rating 4`

- Run 5 iterations, 60s apart, retry once on gate-fail:
  - `python -m sovereign_recursion.loop_runner --iterations 5 --interval-seconds 60 --max-retries 1 --gated --rating 4 --nas-host 192.168.4.114 --dashboard`

Loop artifacts land in `validation/sovereign_recursion/loop_<stamp>/` with a `loop_summary.jsonl`.

### Classification

- `PASS` → log only
- `SOFT_FAIL` → retry (bounded by `--max-retries`)
- `HARD_FAIL` → emit `alert.json` (no retry)

Enable alerts with `--emit-alerts`.

### Policy (externalized)

Classification boundaries can be moved into an auditable JSON file.

- Default policy file: `sovereign_recursion/policy.default.json`
- Use it:
  - `python -m sovereign_recursion.loop_runner --policy sovereign_recursion/policy.default.json --iterations 1 --gated --emit-alerts --rating 4`
