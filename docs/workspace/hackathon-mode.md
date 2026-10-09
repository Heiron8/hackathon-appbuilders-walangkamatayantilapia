# 24-Hour Hackathon Operating Mode

`hackathon-24h` is the Professional Workspace's lightweight mode for roughly four humans working for one day. It simplifies ceremony, not engineering quality. `workspace.config.json` activates the mode; Project Sync reports it.

## What changes

- Plan the smallest credible MVP around the demo-critical end-to-end journey.
- Use small, reviewable vertical slices and integrate frequently instead of maintaining long-lived parallel branches.
- Compress architecture into one kickoff and one explicit human approval.
- Use one design approval for the core user flow and visual direction; resolve routine details during implementation.
- Timebox independent review and invoke specialist roles only when the task's risk or subject requires them.
- Defer nonblocking documentation, ADRs, integrations, observability detail, and harness improvements until after the event.

## What stays mandatory

- The engineering constitution: KISS, DRY, YAGNI, reuse before create, separation of concerns, small responsibilities, clear interfaces, readable code, and no unnecessary dependencies, god files, or premature services.
- Explicit architecture approval before implementation tasks are published.
- Shared task truth, ownership, acceptance criteria, real dependencies, canonical verification, independent review, and a stable integration branch.
- Secrets outside source, boundary validation, safe external API handling, applicable auth/authorization, least privilege where practical, and secret scanning.
- Failure-state handling, deployment evidence, technical explainability, and honest reporting of untested areas.

## Compressed architecture kickoff

Record the concise kickoff in `docs/architecture/overview.md`; update other architecture documents or ADRs only when a decision genuinely needs them. Mark these sections complete in `.orchestrator/architecture-state.json`:

1. `product-boundary`
2. `primary-user-journey`
3. `architecture-style`
4. `modules-responsibilities`
5. `interfaces-contracts`
6. `data-flow`
7. `persistence-strategy`
8. `external-integrations`
9. `failure-fallback`
10. `security-boundaries`
11. `deployment-route`
12. `constraint-tradeoffs`

Select architecture from the challenge; MVC is not required. After the checklist is complete and a human explicitly approves it, record approval with:

```powershell
python scripts/architecture_state.py --approve-by "Human Name"
```

Task publication still fails closed without the approved status, complete compact checklist, and matching approval record. Fuller documents and ADRs remain available for decisions that genuinely need them.

## UX and design

Before demo-critical UI implementation, capture the primary flow, key screens and states, basic visual direction/design system, responsive intent, and loading, empty, error, and success behavior. Obtain one human approval for that core flow and direction. Frontend and design responsibilities may then resolve routine details without repeated approvals. Design QA concentrates on demo-critical screens, usability, responsiveness, accessibility, and visible failure states.

## Tasks and four-person operation

Use a few coherent vertical slices rather than dozens of microscopic tasks:

- **P0:** integrated core journey and its critical fallback.
- **P1:** supporting behavior needed for a credible product.
- **P2:** polish only after P0 is stable.

Each task needs a clear human owner, acceptance criteria, reviewable scope, and only real dependencies. A trivial same-scope correction may stay inside its already-owned task; new scope requires shared task truth.

Suggested responsibilities are fluid:

1. Lead / integration / development
2. Product development
3. Product development / QA
4. Demo / submission / fresh-user testing

Use specialist charters by task: frontend, backend, database, QA, security, deployment, UI design, or Design QA only where relevant. No autonomous multi-agent spawning and no requirement that every task visit every specialist.

## Build lifecycle

Repeat: `small vertical slice -> verify -> independent review -> integrate -> Project Sync`. Keep main/integration usable and avoid four large branches that converge near submission. Review remains `PASS` or `CHANGES REQUIRED` and covers both correctness and engineering quality, including duplication, complexity, responsibility size, layer placement, consistency, dependencies, readability, and whether a simpler correct implementation exists.

Configure project-specific verification commands as soon as the stack exists. Do not defer integration or critical testing until the end.

Choose the simplest viable deployment route only after the challenge and stack are known. Deploy early enough to expose problems. Before submission, verify environment configuration, secret handling, public accessibility, a public smoke test, a fallback plan, and the final deployed build. Production-scale infrastructure and enterprise rollback paperwork are optional unless the challenge actually requires them.

## Final stretch and deferred work

As submission approaches: feature freeze -> canonical verification plus configured product checks -> public smoke test when applicable -> [technical-defense preparation](../../skills/technical-defense/SKILL.md) -> demo/video preparation -> [submission readiness check](../qa/submission-readiness.md). Use actual build evidence and known event requirements; unverified required checks remain open. This is a transition based on product risk, not a fixed clock, and adds no architecture approval gate. Demo/video preparation uses the team's existing process; the technical-defense skill only checks the resulting artifacts.

Fix the harness during the event only when a blocking or repeated defect prevents delivery. Record and defer nonblocking reusable improvements. Optional external design tools, repository-intelligence integrations, advanced orchestration, extensive release governance, full observability documentation, nonessential ADRs, and handoffs without real benefit remain available but are skipped by default in this mode.

Switching modes never deletes completed architecture information. The active mode recalculates its required sections and remains pending until its own gaps are completed and approved. Switching `operating_mode` back to `professional` restores the normal full workflow; Hackathon Mode does not delete or replace any Professional capability.
