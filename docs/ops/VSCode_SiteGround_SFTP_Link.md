# VS Code ↔ SiteGround (SFTP over SSH)

This is the minimal, non-drifting way to link VS Code to a SiteGround-hosted execution surface.

**Principle:** SiteGround is an execution surface, not a source of truth. Prefer manual, explicit uploads; avoid auto-sync.

---

## Option A (Recommended): VS Code + SFTP extension

### Install

Install the VS Code extension:

```vscode-extensions
natizyskunk.sftp
```

### Get credentials (SiteGround)

From **Site Tools → Dev → FTP Manager / SSH Manager**:

- Host: `yourdomain.com` (or the server hostname)
- Username
- Password *or* SSH key
- Port: `22`
- Remote path: usually `.../public_html/` (varies by SiteGround setup)

### Configure

1. Open your local project folder.
2. Run `Ctrl+Shift+P` → **SFTP: Config**.
3. VS Code creates `.vscode/sftp.json`.
4. Replace its contents with your settings.

A safe starting point is the committed template:
- Copy [.vscode/sftp.example.json](.vscode/sftp.example.json) → `.vscode/sftp.json`

**Important:** `.vscode/sftp.json` is ignored by git in this repo.

### Use

- Right-click a file/folder → **Upload to Server**

---

## Option B: VS Code Remote-SSH

Install:

```vscode-extensions
ms-vscode-remote.remote-ssh
```

Then:

1. `Ctrl+Shift+P` → **Remote-SSH: Add New Host**
2. Enter: `ssh your_sg_username@yourdomain.com`
3. Connect and open the target folder under your web root (e.g., `public_html/`).

**Caution:** this edits files in place on the server.

---

## What to avoid

- Don’t enable auto-sync (`uploadOnSave: true`) for constitutional artifacts.
- Don’t store private keys or long-lived secrets on the server.
- Don’t treat the server as your canonical repo.

---

## Minimal connectivity check

- You can list `public_html/`.
- You can create a folder like `verifier/`.
- You can upload a static file and view it in the browser.

That’s enough for connectivity.
