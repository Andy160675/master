# Secure Cloud Folder Structure (Skeleton)

This folder is a **tracked skeleton** for a secure synchronized (cloud/NAS) working area.

Design goals:
- Provide consistent paths across nodes
- Keep real evidence files out of git
- Support an evidence-first workflow with clear boundaries

Security posture:
- The contents of `secure_cloud/` are **ignored by default**.
- Only this `README.md` and `.gitkeep` files should be tracked.

## Structure
- `01_inbox/`
  - Drop-only intake (untrusted)
- `02_working/`
  - In-progress processing
- `03_verified/`
  - Verified/promoted outputs
- `04_exports/`
  - Deliverables for external systems
- `05_receipts/`
  - Audit receipts and hashes (non-secret)
- `06_quarantine/`
  - Suspicious/malware-risk or policy-violating content
- `99_admin/`
  - Admin-only notes, mapping, and SOPs

## Mapping (Optional)
If your runtime uses different local folders (e.g., `Evidence/Inbox`, `Property/Leads`), record the mapping in `99_admin/mapping.md`.
