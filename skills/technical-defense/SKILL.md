---
name: technical-defense
description: Prepare technical defense, judge Q&A, architecture explanations for judges, or technical presentation answers from repository evidence. Use for final-stage defense preparation or a submission readiness check; do not load during normal coding work.
---

# Technical Defense

Prepare a compact, truthful defense aid using [the response contract](../../response-contracts/technical-defense.md). For submission checking, use [the submission readiness template](../../docs/qa/submission-readiness.md) and its evidence classifications. Load these supporting files only for the requested output. This is preparation and reporting, not authorization to deploy, upload, submit, change product code, or produce a video. Return the aid in the response unless the user asks to save it.

## Establish actual project truth

Follow Project Sync and the current phase before describing the product. A starter template or approved architecture is not proof of an implemented product. Inspect only relevant sources:

- Product brief or `docs/product/`: problem, primary user, scope, requirements, journeys.
- `docs/architecture/`, `docs/decisions/`, and architecture state: intended structure, data model, interfaces, security, deployment choices, and approved tradeoffs.
- Actual source, manifests, stack configuration, integrations, and deployment configuration: implementation and boundaries. Inspect code where documents need clarification; report conflicts instead of silently treating design intent as implemented behavior.
- Tests and dated verification/QA results, PR/CI and independent review records, deployment/smoke-test records, and known issues: what was actually checked, against which commit/build, with what result.
- Shared team/task records and Git history when useful: actual ownership, roles, reviews, and integration. Do not infer historical contributions from `.workspace-local/` identity or assume four humans used particular specialist roles.

Link each material claim to a repository path/section or recorded review/check result. Do not expose secrets. A test's existence is not evidence that it passed; deployment configuration or a URL is not evidence that public access works. Workspace harness verification is not product verification. Earlier evidence must identify its build and scope; do not claim it verifies later changes.

Never invent answers, sophistication, challenge rules, performance numbers, or production readiness. Use `NOT DOCUMENTED` for missing recorded evidence and `NEEDS TEAM CONFIRMATION` for unresolved intent, ownership, or conflicting sources; these labels do not establish readiness. Apply `VERIFIED`, `KNOWN BUT NOT VERIFIED`, `NOT READY`, or `NOT APPLICABLE` to claims/checks using the submission template's definitions. Mark proposed production improvements as recommendations, not existing functionality.

## Explain and defend

Keep the main aid roughly one page, with only relevant details. Cover the system/user/flow, actual architecture and stack, important decisions and tradeoffs, security boundaries, performed testing and independent review, realistic bottlenecks/production work, limitations, and evidenced team coordination. Use a short text diagram only when repository evidence supports the actual components and connections. Do not force MVC, a database, a backend, or any other predetermined structure.

Include AI usage only when AI is actually present: its role and justification, deterministic responsibility versus model responsibility, output validation, fallback behavior, and limitations. If presence is uncertain, report `NOT DOCUMENTED` or `NEEDS TEAM CONFIRMATION` rather than inventing AI usage or asserting its absence. Omit AI-specific questions when the product has no AI.

Choose a small question bank relevant to the actual product, not a generic list to fill mechanically. Useful prompts include:

- Why this architecture, framework, and storage choice? What alternatives and tradeoffs were recorded?
- How does data move between the actual components?
- If AI exists, where does it operate, why is deterministic code insufficient, and how is output validated?
- If external services exist, what happens when they fail?
- How are secrets, input validation, and applicable auth/authorization handled?
- What product checks were performed, and what remains unverified?
- How did the actual team avoid conflicts and integrate reviewed changes?
- What are the likely bottlenecks, biggest limitations, and changes proposed for another week?
- What was the hardest technical problem, and which tradeoffs came from the time limit? Seek team confirmation if no record supports the answer.

For each selected question, provide `SHORT ANSWER` (1-3 live-judging sentences), `DEEPER ANSWER` (a concise follow-up), and `EVIDENCE` (supporting artifacts plus classification). Both answers must preserve the same qualifications; a shorter answer must not turn an unverified claim into a verified one. When evidence is missing, state the gap and confirmation needed instead of supplying a plausible answer.

## Check submission readiness when requested

Fill the submission template from the actual event requirements and current artifacts. Leave unknown challenge-specific fields blank and identify required confirmations. Assess the repository, primary journey and error path, deployment, required demo artifacts, defense aid, presentation ownership/fallback, and required links/disclosures/team details. Check whether an existing video opens and meets known requirements; this skill does not create it.

Record evidence, check time, commit/build, and open actions. Report outstanding blockers or unverified required checks with an owner when known. Use the template's overall-readiness rule; missing evidence or unknown requirements never become PASS. Preparing an aid or checklist adds no architecture approval gate and does not change normal Professional phase routing.
