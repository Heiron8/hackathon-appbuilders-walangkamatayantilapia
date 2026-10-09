# Agent Operating Instructions

This repository is the canonical project operating system. Do not rely on chat memory as project truth.

## Startup rule

Before substantial work, reconstruct current truth using the `project-sync` skill and relevant state/docs. If project state is `new` or architecture is unfinished, route to planning rather than silently implementing unapproved architecture.

Read `operating_mode` from `workspace.config.json`. When it is `hackathon-24h`, read `docs/workspace/hackathon-mode.md` and apply its compressed ceremony while preserving architecture approval, verification, independent review, security, task ownership, and current phase gates. The mode never makes unapproved implementation work available.

## Shared priorities

1. Safety and hard guardrails
2. Approved architecture/governance
3. Project/module rules and ADRs
4. Task acceptance criteria and Definition of Ready
5. Role charter / relevant skill
6. Implementation preference

If instructions conflict materially, stop and surface the conflict.

## Engineering behavior

- Understand before changing.
- Inspect existing code/docs before creating new abstractions.
- Reuse before create when it improves clarity/consistency.
- Apply KISS/YAGNI; do not abstract for hypothetical futures.
- Respect module/data/API boundaries.
- Do not make silent architecture, schema, auth, security, payment, or deployment changes.
- Do not add dependencies without need and compatibility review.
- Do not hardcode secrets.
- Do not bypass failing verification.
- Do not claim completion without evidence.
- Do not repeatedly retry the same failing approach without new evidence.
- Keep context task-scoped and token-efficient.

## Source-of-truth map

- GitHub Issues/Projects: task/progress truth
- Git: code/history truth
- Repo docs/ADRs: intended architecture/decisions
- PR/CI/QA: integration/verification truth
- `.workspace-local/`: local human identity only; never authoritative historical attribution

## Role separation

Implementers may write. Independent reviewers should remain read-only whenever practical. UI Designer decides design direction; Frontend Engineer implements approved design; Design QA verifies the rendered result.

## Harness learning

When a failure reveals a reusable lesson, propose a targeted improvement to rules/skills/scripts/tests/docs through the Harness Improvement Loop. High-impact changes require Lead Architect/team approval and normal PR review.
