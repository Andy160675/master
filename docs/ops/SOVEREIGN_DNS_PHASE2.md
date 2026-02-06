# Sovereign DNS (Phase 2) — NAS Resolver + Audit Trail

## What you asked for
- Target host: `192.168.4.114` (NAS)
- Target service: DNS on TCP/UDP 53
- Goal: stop relying on `1.1.1.1` as a resolver and make DNS queries visible/auditable.

## Constraint: SSH control path
I cannot provide credentials.

To establish authorized access, use one of:
- Add your **public key** to the NAS user’s `~/.ssh/authorized_keys`.
- Provide a temporary password + MFA / console access for initial key install.

Suggested operator flow (safe):
1. Generate a dedicated keypair on your admin workstation:
   - `ssh-keygen -t ed25519 -f ~/.ssh/sovereign_nas_ed25519 -C "sovereign-nas"`
2. Share **only** the public key (`.pub`) with the NAS admin.

## Deployment option A (preferred): Docker Unbound + audit sidecar
Repo bundle: [services/sovereign_dns/](services/sovereign_dns/)

What it does:
- Runs **Unbound recursive resolver** (no upstream forwarders like 1.1.1.1).
- Writes query logs to a file.
- A python sidecar tails that log and appends each line as a hash-chained ledger event:
  - `data/audit_chain.jsonl`

Deploy script:
- [scripts/ops/Deploy-SovereignDNS-Docker.ps1](scripts/ops/Deploy-SovereignDNS-Docker.ps1)

## Deployment option B (fallback): apt install unbound
If Docker isn’t available but `apt-get` exists:
- Install `unbound`
- Enable `log-queries: yes`
- Write logs to a fixed file path
- Run a small “tail → ledger append” service (can be systemd) using `dns_audit_tail.py`

## Verification
- Preflight (detect Docker/apt/port 53 listener):
  - [scripts/ops/SovereignDNS-Preflight.ps1](scripts/ops/SovereignDNS-Preflight.ps1)
- Client-side DNS resolution test:
  - [scripts/ops/Test-SovereignDNS.ps1](scripts/ops/Test-SovereignDNS.ps1)

Success criteria
- Port 53 is open on `192.168.4.114` (TCP+UDP).
- A client can resolve: `Resolve-DnsName -Server 192.168.4.114 -Name example.com`.
- Ledger is being appended on the NAS: `data/audit_chain.jsonl` grows with `DNS_QUERY_LOG` events.
