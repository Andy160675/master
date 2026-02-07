# ??? Sovereign Stack Status
[![Continuous Assurance Status](https://github.com/PrecisePointway/master/actions/workflows/continuous-assurance.yml/badge.svg)](https://github.com/PrecisePointway/master/actions/workflows/continuous-assurance.yml)

Cryptographic ledger integrity is continuously verified (hash + rogue file check) via scheduled CI. Any drift invalidates the build.

# master
Project management file

## Canonical docs (2026-02-06)
- Architecture: `CSS-ARCH-DOC-001.md`
- Governance: `CSS-GOV-DOC-002.md`
- Constitution (core record): `constitution/CORE_CONSTITUTION.md`
- Secure cloud skeleton: `secure_cloud/README.md`

## Quickstart (Clone ? Verify ? Portal ? Evidence PDF)
```bash
# 1. Clone
git clone https://github.com/PrecisePointway/master.git
cd master

# 2. (Optional) Install libsodium (if not already detected)
# Windows: set LIBSODIUM_ROOT=C:\path\to\libsodium
# Linux (Debian/Ubuntu): sudo apt-get install libsodium-dev

# 3. Build C++ verifier (CMake, C++14)
cd src/verifier
cmake -S . -B build
cmake --build build --config Release
ctest --test-dir build || ./build/verify_evidence_tests

# 4. Return to repo root and install portal deps (Node 18+)
cd ../../..
npm install
# (Ensure: jspdf, jspdf-autotable, d3 installed; type shims included)

# 5. Run portal (Dashboard + Merkle Viz + PDF export)
npm run dev
# Open http://localhost:5173 (or framework dev URL)

# 6. Generate signed compliance PDF (manual trigger in UI or script)
# Example script call (if added): node scripts/generate-pdf-report.js

# 7. Tamper evidence demo (PowerShell)
pwsh -File scripts/TamperEvidenceDemo.ps1
# Artifacts ? logs/tamper/

# 8. Security regression check (full harness)
pwsh -File scripts/sovereign.ps1 -Action security
```
**Outputs:**
- Merkle + signature test results (ctest)
- Dashboard live compliance snapshot
- `dist/reports/compliance-report-<build>.pdf` (if script executed)
- Tamper JSON: `logs/tamper/tamper_evidence.json`
- Verification logs: `logs/compliance/*.json`

> For air?gapped pilot: build with static libsodium, copy `Verify-Evidence` + `constitution/` + `logs/` seed.

## Governance script: `sovereign.ps1`
A single-file PowerShell governance stack is available at `scripts/sovereign.ps1`.

Quickstart (Windows, elevated PowerShell recommended):

```powershell
# First time setup (creates directories, keys, initial attestation)
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\sovereign.ps1 -Action setup

# Daily security check
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\sovereign.ps1 -Action security

# Run full governance stack
pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\sovereign.ps1 -Action full
```

See `docs/audit/DEPENDENCY_MANIFEST_APPENDIX.md` for dependency manifest governance and CI details.

## Compliance & Tamper Evidence
This repository includes an automated compliance and tamper-evidence pack:

- `scripts/BuildAndTest.ps1`: Builds verifier (libsodium-enabled) and runs tests.
- `scripts/TamperEvidenceDemo.ps1`: Demonstrates deterministic tamper overwrite, SHA256 diff, and Merkle root change; emits JSON artifact.
- `docs/dashboard.yaml` / `docs/dashboard.mmd`: Regulator-facing summary + Mermaid diagram.
- `docs/portal_wireframe.md`: Wireframe specification for compliance portal.
- `docs/evidence_schema.json`: JSON schema for drill-down evidence bundles.
- `docs/requirements_traceability.md`: Initial scaffold for clause-to-artifact mapping.
- GitHub Actions workflow `.github/workflows/compliance.yml`: Nightly + on-push build, tamper demo, static analysis, artifact archival.

### Running Locally
```powershell
# Build and test
pwsh -File scripts/BuildAndTest.ps1
# Run tamper evidence demonstration
pwsh -File scripts/TamperEvidenceDemo.ps1
```
Artifacts are written under `logs/tamper/` and can be extended with signature sealing.

### CI Outputs
- Tamper evidence JSON (`tamper_evidence.json`)
- Static analysis report (`cppcheck_report.xml`)
- Future: signed bundles and compliance clause logs.

> Extend `VerificationHarness.ps1` (to be added) to populate `logs/compliance/*.json` per standard and link Merkle + signature verification per artifact.

## Sovereign System Overview

### Investment Thesis
- Operationalized compliance: automated evidence generation mapped to standards.
- Tamper detection moat: cryptographic hashing + Merkle root persistence and regression alerts.
- Deterministic integrity: reproducible builds and chain verification guard against silent drift.
- Audit velocity: regulators can independently re-run harnesses and validate artifacts via published schema.

### Technical Architecture
- Evidence Verifier: `scripts/VerificationHarness.ps1` executes signature auth, Merkle recompute, regression detection.
- Merkle + Hashing Core: recompute logic for artifact set; persisted roots with optional signing.
- CI Pipelines: GitHub workflow [`compliance.yml`](./.github/workflows/compliance.yml) runs nightly compliance & tamper suite.
- Evidence Schema: JSON validation via [`docs/evidence_schema.json`](./docs/evidence_schema.json) for structured artifact bundles.
- Policy Artifacts: `constitution/policy_manifest.yml` + signature `constitution/policy_manifest.sig`.
- Additional Automation Scripts:
  - Build & test: `scripts/BuildAndTest.ps1`
  - Tamper demo: `scripts/TamperEvidenceDemo.ps1`
  - Merkle utilities & anchoring: assorted scripts under `scripts/` (e.g. anchoring, integrity checks).

### Compliance & Audit
- Harness Output Directory: `logs/compliance/` (JSON summary + artifact list).
- Standards Mapping: dynamic roll?up per run; partial states downgraded to warn/fail.
- Exit Codes (from `VerificationHarness.ps1`):
  - 0 = PASSED (signature + Merkle both pass)
  - 1 = PARTIAL (one passes; degraded assurance)
  - 2 = Missing required files (prerequisites absent; harness aborted early)
  - 3 = FAILED (verification and Merkle integrity not satisfied)
- Regression Signaling: merkle mismatch + weakened verification emits `merkle_regression_event.json`.
- Root Persistence: accepted Merkle root stored & optionally signed for chain?of?custody.
- Schema Validation: artifacts checked against evidence schema; status embedded in summary.

Contact: security@sovereign.example

## Connection endpoints (Distributed / Sovereign Process Isolation)

Hardcoded `localhost` dependencies are avoided by using environment variables for service endpoints.

**Environment variables** (see [.env.example](.env.example)):
- `TRUTH_ENGINE_URL` (default `http://localhost:8000`)
- `TRUTH_ENGINE_CORS_ORIGINS` (default `*`; set to a comma-separated list to restrict)
- `OLLAMA_HOST` (default `http://localhost:11434`)
- `OLLAMA_BASE_URL` (optional; defaults to `${OLLAMA_HOST}/v1` when used)

**Connectivity verification**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-connections.ps1
```

Example (NAS/LAN):

```powershell
$env:TRUTH_ENGINE_URL = 'http://192.168.4.114:8000'
$env:OLLAMA_HOST = 'http://192.168.4.114:11434'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-connections.ps1
```

**Truth Engine bind address**:
The VS Code task "Blade: Start Truth Engine API" is set up to bind for distributed access. If you need to restrict exposure, use OS firewall rules or run uvicorn with a loopback-only `--host`.
