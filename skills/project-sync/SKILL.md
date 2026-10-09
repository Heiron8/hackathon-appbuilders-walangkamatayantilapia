# Project Sync Skill

## Purpose
Reconstruct current project truth without relying on prior chat.

## Steps
1. Identify local member from `.workspace-local/member.json` if present.
2. Read project, architecture, team, and relevant task state.
3. Read relevant docs/ADRs.
4. Query Git/GitHub state when tooling/auth are available.
5. Reconcile obvious stale state only when safe and idempotent.
6. Respond using `response-contracts/project-sync.md`.

Be concise: expand team details only when relevant.
