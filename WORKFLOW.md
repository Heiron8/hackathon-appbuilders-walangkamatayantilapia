# End-to-End Workflow

## 1. Workspace open

`Project Sync` always runs first conceptually:

1. Identify current human.
2. Read project phase/state.
3. Read architecture progress/approval.
4. Read relevant repo docs/ADRs.
5. Read Git/GitHub task, branch, PR, CI/QA state when available.
6. Reconcile obvious stale state when safe.
7. Return the standard Project Sync response contract.

## 2. Phase routing

- `new` → Architecture Kickoff
- `planning` → resume architecture planning
- `implementation` → task/PR/project execution briefing
- `release` → staging/QA/release briefing
- `maintenance` → issue/production-state briefing

If `workspace.config.json` selects `hackathon-24h`, use the compressed kickoff, design, task, review, integration, deployment, and final-stretch guidance in `docs/workspace/hackathon-mode.md`. The phase routing and approval gates below still apply.

## 3. Architecture planning

One meaningful question at a time. Persist each approved/known answer into repo docs and `.orchestrator/architecture-state.json`.

Architecture planning covers, as relevant:

problem → users/stakeholders → system boundary → journeys → functional/non-functional requirements → MVP/scope → modules → data ownership/model → APIs/events/contracts → security → deployment/infrastructure → observability/failure handling → UX/wireframes → QA/acceptance strategy → review

Status lifecycle:

`not_started → in_progress → review_pending → changes_requested → approved`

Implementation tasks are normally not released before `approved`.

## 4. Architecture → tasks

Task Planner produces tasks with:
- stable workspace task key
- title/goal
- module
- acceptance criteria
- dependencies
- risk
- Definition of Ready
- likely review specialists

Approved tasks are published idempotently to GitHub Issues/Projects.

## 5. Task execution

`Backlog → Definition of Ready satisfied → Ready → claim → owner assignment + isolated branch/worktree → In Progress → scoped worker context → implementation → checkpoint(s) → verification`

Workers must inspect before creating, reuse existing assets where appropriate, respect module boundaries, and avoid unrelated changes.

## 6. Delivery

Verification passes → logical commit → push → PR linked to task → board status In Review → independent reviewer → fix loop if needed → merge policy → task closes/Done.

High-risk changes require stronger human approval.

## 7. Recovery

A restarted/new session never trusts prior chat. It reconstructs from repo/GitHub truth. Repeated similar failures trigger anti-thrashing and the Harness Improvement Loop.
