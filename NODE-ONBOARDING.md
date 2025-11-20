# Node Onboarding Ritual (Bootstrap v1.1)

Immutable anchor: tag `bootstrap-v1.1`.
Only per-node change: `ROOT` path (username / home root). `REPOS` and `ORG` stay constant unless repo topology or remotes differ.

## 1. Clone orchestration repo & checkout canonical tag
```sh
git clone https://github.com/PrecisePointway/master.git
cd master
git fetch --tags
git checkout bootstrap-v1.1
```

## 2. Set per-node ROOT in Makefile
Edit `Makefile`:
```
ROOT  := C:/Users/<node-username>
REPOS := source/repos/PrecisePointway/master source/repos/Blade2AI
ORG   := PrecisePointway
```
Do NOT alter `REPOS` or `ORG` unless Node uses different repo layout or remote org.

## 3. Sanity discovery (non-destructive)
```powershell
make discovery
```
Expected output lists full paths under new ROOT, e.g.:
```
C:\Users\<node-username>\source\repos\PrecisePointway\master
C:\Users\<node-username>\source\repos\Blade2AI
```
Remotes must match `git remote -v` inside each repo.

## 4. Full bootstrap
If discovery sane:
```powershell
make all
```
Or VS Code task: `Sovereign: ALL Bootstrap Stack`.

## 5. Failure contract (only thing to report)
Format:
```
<target> | <exact PowerShell error text> | <missing path>
```
Valid targets: `discovery | clone | solutions | bootstrap | health | audit`.
No screenshots, no extra commentary.

## 6. Version discipline
- `bootstrap-v1.1` = deterministic baseline (Makefile + PowerShell suite + tasks.json)
- Future structural changes (repos added, multi-org support, layout shifts, new audit phases) ? tag `bootstrap-v1.2`+
- Cosmetic/local tweaks never modify bootstrap tags.

## 7. Adding new nodes
Repeat steps 1–4 with only ROOT changed.

## 8. Multi-org or per-repo overrides (future)
When required, evolve clone logic to accept a manifest mapping repo path ? org. Ship that in a new tagged version.

## 9. Drift prevention checklist
Before declaring node operational:
- [ ] Tag checked out: `bootstrap-v1.1`
- [ ] Makefile ROOT matches real username
- [ ] Discovery shows both repos
- [ ] Remotes correct
- [ ] Bootstrap completes without contract output

## 10. Escalation
If contract output produced, patch Makefile / scripts only to resolve reported path or remote mismatch; re-run from step 3.

End of ritual.
