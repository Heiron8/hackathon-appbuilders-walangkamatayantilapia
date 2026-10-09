# Tanaw Approved Four-Person Implementation Handoff

Status: ARCHITECTURE AND COMPACT PLAN APPROVED by the requesting Lead Architect on October 9, 2026. Canonical task input: [approved-tasks.json](../approved-tasks.json). Publication/status evidence is recorded below. All tasks are UNASSIGNED; actual member identities and independent reviewers must be supplied before claims. Human editable-design approval is required before frontend implementation. Developer numbers are approved lanes, not invented identities. This planning session does not authorize application edits, installations, commits or pushes.

Target: demo-ready **October 10, 2026 08:00 Philippine time**; official submission **10:00**. Follow [compact architecture](../../architecture/overview.md) and [contracts](../../architecture/contracts.md).

## Minimal ownership and tasks

| Key / priority | Owner / scope | Acceptance / exit evidence | Real dependencies / reviewer |
| --- | --- | --- | --- |
| TANAW-01 / P0 | Developer 1: shared vocabulary/contracts, pinned manifests, startup, existing verification configuration | One canonical vocabulary consumed by both sides; final loopback static serving; build/tests configured in existing runner; documented setup; already loaded board operates when inference API/backend stops; disconnected reload works with local server running | Architecture/task approval; Developer 3 reviews shared/backend setup, Developer 4 reviews setup/verification |
| TANAW-06 / P0 | Developer 2: editable Figma foundation and human review | Exactly three screen families and required states from the approved UX brief; editable components and responsive variants; Figma link plus explicit human approval/corrections recorded before frontend code | Approved brief; Figma access; human reviewer; Developer 4 performs read-only accessibility/state review |
| TANAW-02 / P0 | Developer 2: approved communication shell, board, message/review states | Exact fixed IDs/order; ordered selection/removal/clear; keyboard/focus/targets; stale AI/approval invalidation; no auto-speech; three approved views responsive | Architecture/task + human design approval; shared contract; Developer 4 does Design QA, Developer 1 reviews code |
| TANAW-03 / P0 | Developer 3: local model experiment, expand/health endpoints and adapter | Actual disconnected inference; bounded JSON/grammar checks; supported expansion success and zero accepted unsupported additions in fixtures; timeout/model-stop preserve AAC; dated latency/memory report | Architecture/task approval; shared contract; Developer 1 reviews, Developer 4 witnesses offline/meaning checks |
| TANAW-04 / P0 | Developer 4: offline speech/assets, fresh-user checks, demo | Local full-sentence voice proven on demo browser; complete licensed card audio fallback; stop/replay; no silent text-to-card substitution; fresh disconnected startup and final video/disclosures | Architecture/task approval; speech contract and IDs; human design approval for UI wiring; Developer 2 reviews speech code, Developer 1 reviews evidence |
| TANAW-05 / P1 CONDITIONAL | Developer 3: conversation suggestions, with Developer 2's separately owned UI wiring | Only valid unique vocabulary IDs; >=90% independently reviewed relevance; no imposed answers; primary grid remains intact; runtime-offline, injection, stale-question checks pass | TANAW-03 feasible model + Lead accepts suggestion evidence before enabling; Developer 1 reviews backend, Developer 4 reviews behavior/UI |

Risk: TANAW-01 integration/contracts medium; TANAW-06 design medium; TANAW-02 AAC/accessibility high; TANAW-03 intent/local inference high; TANAW-04 offline speech/assets high; TANAW-05 suggestion bias/intent high. Common Definition of Ready: approved architecture/task plan, real named owner/reviewer, frozen interface snapshot, available inputs, task-specific acceptance criteria. Frontend tasks additionally need approved design. All published issues start Backlog while owner/reviewer identities are missing. P0 means demo-critical; P1 cannot consume the fallback/testing buffer.

File ownership: Lead owns shared vocabulary/config/manifests/CI/startup; Developer 2 owns UI and interaction state; Developer 3 owns backend/AI; Developer 4 owns speech helper/assets and QA/demo docs. Changes across lanes need owner coordination. The speech owner can prepare/test a standalone helper after architecture approval while design is pending; frontend UI implementation still waits for design approval. Split later integration into small PRs instead of one large branch per person.

## Coordination without a GitHub Project

Reuse GitHub Issues as durable task truth after approval. Each approved issue carries the stable key, goal, acceptance criteria, dependencies, Definition of Ready, risk, single human assignee, reviewer, and exit evidence. Lead serializes initial assignments and rechecks ownership; no claim is atomic. Use a documented `Backlog / Ready / In Progress / In Review / Blocked / Done` issue-body status convention; avoid adding new automation during the event. Linked PR closes the issue only after review/merge.

Project-dependent `publish_tasks.py` / `claim_task.py` must not be used without verified Project configuration/permissions. The Lead has approved manual Issues-first coordination; reuse the publisher's architecture-release validator, stable-key lookup and task-body formatting with ordinary GitHub issue creation. No new automation/framework is added. Keep project_number null until access is actually verified.

Each developer uses a separate clone/worktree and short task branch. Do not share one mutable checkout. Before beginning work: Project Sync, confirm current owner/dependencies, inspect contract. Before merge: applicable deterministic checks, short independent PASS/CHANGES REQUIRED review, then Lead integration. Use 5-10-minute review windows for small PRs, but unresolved correctness/security/intent failures still block merge. Conventional Commits and linked PRs stay in force.

## Execution sequence after approval

1. Architecture/task-plan approval is recorded. Publish approved issue records unassigned. Before claims, register the four real members/Lead and nominate real independent reviewers; configure hooks in each developer's isolated checkout under its implementation task. Repository identity is configured; no Projects/settings/identity changes are inferred.
2. After ownership and the approved planning package are available, open four separate implementation sessions: `tanaw-dev1-integration` (TANAW-01), `tanaw-dev2-design-frontend` (TANAW-06 then TANAW-02), `tanaw-dev3-local-ai` (TANAW-03 then conditional TANAW-05), and `tanaw-dev4-speech-qa` (TANAW-04). Developer 2 owns Figma generation/human review. Developer 4 prioritizes offline speech and supports read-only design QA. No frontend implementation before human design approval. No automatic agent spawning is authorized by these human-session assignments.
3. Within 90 minutes of implementation/design authorization, integrate a usable direct AAC slice (board -> selection -> offline speech), without waiting for AI. Integrate manifests/shared files first to avoid conflicting scaffolds. Exercise internet disconnected and AI/backend unavailable.
4. Integrate expansion next with genuine local inference and mandatory approval/stale-result/timeout paths. A deterministic baseline or mock is never described as passing local AI. If the model/speech gate fails, surface the P0 blocker rather than silently removing local inference/full-sentence voice from the promised demo.
5. Decide suggestions within two hours after runtime/setup is ready. Keep disabled if relevance, safety, latency, or offline evidence fails. Developer 2 may prepare the approved disabled/empty view; no working-feature claim or enablement before the gate passes.
6. Integrate small PRs continuously, ideally every 30-60 minutes of reviewable work; synchronize shared changes after each merge. Never accumulate four long-lived branches for a final merge.
7. Feature freeze October 10 **06:00**; final configured product/harness checks and fresh offline setup by **07:00**; demo/video/rehearsal and disclosure checks completed by **08:00**. **08:00-10:00** is submission/correction buffer, not new-feature time. Re-cut optional scope if approval/setup takes longer.

## Verification evidence to collect (not run yet)

- Backend contract, grammar/negation, invalid input/output, timeout/unavailable model, busy/disabled suggestions, origin/body-limit tests.
- Frontend ordered selection, correction, approval invalidation, stale responses, explicit speech, retained board during failures; production build.
- Browser keyboard/focus, contrast, responsive overflow, local-voice and complete card-audio checks; manual child-oriented usability review without claiming clinical validation.
- At least 12 expansion + 12 suggestion fixtures; >=30 timed warm calls for enabled behavior, cold-load measurement, RAM/VRAM, model/runtime digest, internet-disconnected restart/reload and model stopped.
- Fresh teammate setup from public repo on the supported target; no secret/private data; video actually opens, shows integrated build and fallback, meets confirmed event format; disclose pre-existing harness, libraries, models, assets and coding tools.

Current state: architecture/task plan approved; no product implementation, dependencies/models, runtime test evidence, named assignments, or human editable-design review. Future implementation requires the task-specific gates; this session only records approval and prepares/publishes issue records. Local uncommitted architecture/contracts must be handed to teammate sessions or delivered through an authorized reviewed commit/PR before they reconstruct project truth from a fresh clone.

## Publication evidence

Six durable issue records published on October 9, 2026 via the approved Issues-first path, using existing publisher approval/key/body helpers and GitHub CLI. Each created issue was read back directly; no Project, assignment, label, setting, branch, commit or push mutation was performed. Issues remain Backlog / unassigned, not falsely Ready. The four session lanes are prepared for ownership; frontend is additionally blocked on TANAW-06 human design approval, and suggestions on TANAW-03 plus the separate evaluation gate.

| Session / lane | Issue sequence | Next permitted task after actual owner/reviewer assignment |
| --- | --- | --- |
| `tanaw-dev1-integration` / Developer 1 | [TANAW-01 / #1](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/1) | Shared vocabulary/contracts and integration setup |
| `tanaw-dev2-design-frontend` / Developer 2 | [TANAW-06 / #2](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2) -> [TANAW-02 / #3](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/3) | Editable Figma foundation first; frontend only after human approval |
| `tanaw-dev3-local-ai` / Developer 3 | [TANAW-03 / #4](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/4) -> [TANAW-05 / #6](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/6) | Local-model/expansion experiment first; suggestions remain conditional |
| `tanaw-dev4-speech-qa` / Developer 4 | [TANAW-04 / #5](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/5) | Offline local-voice proof first, then speech fallback/integrated QA/demo |

First implementation checkpoint: within 90 minutes after owners and human design approval are available, the integrated laptop build lets a user choose Want -> Eat -> Apple, correct/clear selections, and explicitly speak offline with Ollama stopped. Record browser/voice, integrated build, disconnected restart/reload with local server running, and independent short-review evidence. This checkpoint does not wait for AI expansion/suggestions.

Deferred harness proposal: immediate post-create issue enumeration can lag. Verify the creation URL directly, then enumerate/reconcile before any retry. The first publication verified this behavior without duplicating its issue; no harness code was changed during kickoff.
