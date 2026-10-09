# Professional Workspace v1 Traceability

A local verification pass checks the template harness, not live GitHub or product behavior.

| Capability | Source | Check |
|---|---|---|
| Planning and recovery | `.orchestrator/`, `scripts/architecture_state.py`, `scripts/project_sync.py` | State and contract checks |
| Team identity | `.orchestrator/team.json`, `scripts/onboard_member.py`, ignored `.workspace-local/` | Onboarding and scope checks |
| Role guidance | `agents/`, `skills/`, `response-contracts/` | Structure and contract checks |
| Task lifecycle | `scripts/publish_tasks.py`, `claim_task.py`, `github_project.py`, `reconcile_project.py` | Deterministic tests; live integration separately |
| Git and review controls | `.githooks/`, `.github/`, `scripts/guardrails.py` | Hook and CI checks |
| Architecture and design governance | `docs/workspace/`, `docs/{architecture,design,decisions}/` | Review against the new project's approved decisions |
| Optional runtimes and integrations | `adapters/`, `integrations/`, `external-skills.lock.json` | Configuration inspection |

New repositories must verify their own GitHub permissions, Project fields, product tests, and deployment evidence before claiming an end-to-end pass.
