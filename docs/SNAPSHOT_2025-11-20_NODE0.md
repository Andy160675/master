# SNAPSHOT: SOVEREIGN NODE 0 (2025-11-20)

## Scope
Single-node, offline-first governance harness (PC4) proving:
- Dual jurisdiction tracks (stable vs insider)
- Router-enforced safety + legislative defect trap
- Evidence & Property agents under constitutional control
- Orchestrated boot, verification, health, and governed shutdown

## Operational Topology
- PC4 = Sovereign Execution Node (agents, ledger, backups E:/ F:/)
- PC5 = Viewport (read-only oversight; no asset residence)
- Law Assets: `SOVEREIGN_NODE_LAW.md`, `WATCH_CARD.md`

## Core Artifacts
| Category | Files |
|----------|-------|
| Law / Governance | SOVEREIGN_NODE_LAW.md, WATCH_CARD.md |
| Orchestration | sovereign_up.py, integration_verify.sh, verify_integration.py, healthcheck.py, sovereign_down.sh, sovereign-backup.ps1 |
| Agents | src/agents/evidence_validator.py, src/agents/property_analyst.py |
| Safety / Router | src/core/router.py, src/core/config.py |
| Prompts | src/prompts/property_analyst_system.md |
| Readiness / Review | scripts/agent_readiness.py, scripts/review_property.py |
| Tests | tests/test_tracks.py (track separation), integration_verify.sh (10 checks) |
| Research Intake | research/nate_agents_transcript.txt, NATE_AGENT_TRIANGLE.md, anthropic_security.md, google_a2a.md, video_summary.md |
| Ledger | Governance/Logs/audit-insider.jsonl, audit-stable.jsonl, promotions.jsonl |
| Backup Protocol | sovereign-backup.ps1 (mirrors to E:/ F:/) |

## Boot & Verification Sequence
1. `python3 sovereign_up.py` (creates genesis, seeds sample files, boots boardroom ? agents)
2. `bash integration_verify.sh` (10-phase integration assertions)
3. Continuous: `watch -n 60 python3 healthcheck.py`
4. Shutdown: `./sovereign_down.sh --backup` (tar snapshot + external drive mirror)

## Post-Backup Health Validation
- Run: `./integration_verify.sh`
- Confirms: evidence stable output, property insider drafts, defect trap score ? 5, ledgers writable

## Integrity Anchors
- Git Tag: `node0-backup-20251120`
- Ledger Hash (SHA256 of audit-stable.jsonl): 9f1b34a2b3fd73c530ecf6c8b7e4d5e20e06d0e6fac25570b8aaaeec8477ee3a
- External mirrors: E:\Sovereign_Backups, F:\Sovereign_Backups

## Integrity Anchor
- Source log: `Governance/Logs/audit-stable.jsonl`
- SHA256: `9f1b34a2b3fd73c530ecf6c8b7e4d5e20e06d0e6fac25570b8aaaeec8477ee3a`
- Date: 2025-11-20 (UTC)

## Demonstrated Governance Patterns
- Track separation: stable writes only to `_verified`, insider to `_drafts`
- Legislative trap: structural defects force `condition_score <= 5`
- Agent jurisdiction encoded via env vars + directory routing (not prompt-only)
- Immutable audit append (JSONL chain + external hash anchor)

## Truth-Aligned Claims (Safe to Present)
- Running local sovereign node with constitutional artifacts
- Code-level enforcement of dual tracks & safety rules
- Repeatable orchestration + verification + health monitoring
- Evidence & Property agents produce governed outputs
- Research ingestion pipeline integrated without cloud leakage
- Backups & provenance established (tag + hash)

## Non-Claims (Do NOT State Yet)
- Multi-node coordination / mesh
- Production external customer usage
- Full domain-general truth engine
- Automated legal compliance across all sectors

## Current Status Line
"Node 0: operational, single-domain governance harness validated. Next: harden, add second domain, prepare narrow investor demo UI."

## Next Milestones
1. Add second governed domain (e.g. Contracts risk pass) with parallel track logic
2. Implement hash-chain ledger verifier + periodic integrity CRON
3. Lightweight local UI (read-only) for investor demo
4. Promotion workflow expansion (automatic candidate queue + boardroom vote simulation)
5. Security hardening (template sandboxing, stricter prompt diff validation)

## Promotion Readiness Criteria (Preview)
- Insider agent defect recall > target threshold
- Zero hallucination flags in last N runs
- Consistent constitutional compliance (no score trap breaches)
- Ledger audit uninterrupted (no tamper events)

## Investor Summary (One Sentence)
"We have converted raw AI scripts into a governed, offline sovereign node with enforceable constitutional rules, dual safety tracks, audited ledger, and a repeatable orchestration lifecycle—ready to scale domains, not just demos."
