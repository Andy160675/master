# sync_conversation

This folder is **tracked in git** and is intended for lightweight, low-conflict cross-IDE / cross-machine coordination via git `pull` + `push`.

Design goals
- Avoid accidental commits of the wider repo (venv, builds, caches).
- Avoid merge conflicts by writing **append-only, per-author message files**.

Conventions
- Messages are stored under `sync_conversation/messages/<AuthorId>/...`.
- Each message is a new timestamped `.md` file.

VS Code tasks
- Use the `Ops: Convo Sync Loop (Pull/Rebase/Auto-commit/Push)` task to keep this folder synchronized on a timer.
- Use `Ops: Convo Send Message (Commit+Push Once)` to write a message file and push it.
