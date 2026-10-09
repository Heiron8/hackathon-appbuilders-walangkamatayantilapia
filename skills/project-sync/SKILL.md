# Project Sync Skill

## Purpose
Reconstruct current project truth without relying on prior chat.

## Steps
0. Run `python scripts/project_sync.py`: safely synchronize clean `main` with `origin/main` before reading shared state. Report UPDATED, ALREADY CURRENT, NOT UPDATED (reason/action), or OFFLINE. Preserve task branches, all dirty work, local-ahead/divergent history and interrupted operations; never reset, rebase, stash or repair automatically. Offline Sync uses local files; unavailable remote truth remains unknown.
1. Identify local member from `.workspace-local/member.json` if present.
2. Read project, architecture, team, and relevant task state.
3. Read relevant docs/ADRs.
4. Query Git/GitHub state when tooling/auth are available.
5. Reconcile obvious stale state only when safe and idempotent.
6. Respond using `response-contracts/project-sync.md`.

Be concise: expand team details only when relevant.
