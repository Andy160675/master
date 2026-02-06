# Sovereign DNS (Phase 2)

Goal
- Bring up a local DNS resolver on the NAS (e.g. `192.168.4.114`) listening on TCP/UDP 53.
- Log all DNS queries to an **append-only, hash-chained JSONL ledger**.

This bundle is designed to be deployed over SSH once you have an authorized control path.

## Docker deployment

Files:
- `docker-compose.yml`
- `unbound/unbound.conf`
- `audit/dns_audit_tail.py`

What runs:
- `unbound` recursive resolver (no dependency on public resolvers like `1.1.1.1`).
- `dns-audit` sidecar tails Unbound logs and appends each line as an event into a local ledger file.

Ledger output (inside deployment directory):
- `./data/audit_chain.jsonl`

## Notes
- This is evidence-first: it does not modify your fleet DNS settings. Once port 53 is live, you can point clients to the NAS resolver.
- If you want per-query structured fields (qname/qtype/rcode), we can tighten parsing once we see the exact Unbound log format on UGREEN OS.
