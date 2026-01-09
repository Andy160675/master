# Phase 2A — Demo-Only Evidence Record

- Timestamp (UTC): 2026-01-09T02:39:54Z
- Execution surface root: https://sovereignsanctuarysystems.co.uk/verifier/
- Demo directory (intended): https://sovereignsanctuarysystems.co.uk/verifier/demo/
- Server posture: static-only, disposable, non-authoritative

## Deployed artifacts (demo-only)

Target server path:

- `/public_html/verifier/demo/`
  - `valid.json`
  - `invalid.json`
  - `README.txt`

## Local integrity (pre-upload) — SHA-256

- `public_html/verifier/demo/valid.json`  size=416  sha256=752a3b955824065baa130498a3584f2750a87c583b79850d3c60931c5a22e36c
- `public_html/verifier/demo/invalid.json` size=394  sha256=f855358af9aacc7d4be177b691bdb96808c6d3100f8c8afb8cb5082887491d72
- `public_html/verifier/demo/README.txt`   size=403  sha256=84462b01c445af3f6d8dce43817edef71092ddf47c799a94651d90ba0119b846

## Local verification outcome (deterministic)

Verification method:

- Canonical JSON for `payload`: `json.dumps(payload, separators=(",", ":"))`
- Hash: `SHA-256(utf8(canonical_payload_json))`

Expected results:

- `valid.json`   → PASS (declared payload hash matches recomputed)
- `invalid.json` → FAIL (declared payload hash does not match recomputed)

## Guardrails

- No secrets stored on server
- No cron jobs/services/database
- No Phase-1 / constitutional artifacts deployed
- No user uploads/auth

## Operator statement

Operator uploaded only the three demo artifacts into `/public_html/verifier/demo/` and kept all other server state unchanged.
