# Professional Workspace v1 — Frozen Specification

## Goals

1. Preserve project truth outside chat memory.
2. Guide system planning from idea to approved architecture.
3. Turn approved planning into GitHub execution work automatically and idempotently.
4. Keep progress synchronized through task, PR, review, QA, and merge states.
5. Support a dynamic team registry; current team size is not a platform limit.
6. Let each member use a compatible IDE/runtime without changing the engineering process.
7. Provide professional role charters, engineering standards, anti-slop rules, token efficiency, and evidence-based completion.
8. Provide UX/wireframe/design governance with a curated design-skill strategy.
9. Recover after session loss and learn from reusable failures through a governed harness-improvement loop.

## Required capabilities

### Project initialization and planning
- New-project detection
- First-open member onboarding
- Guided Architecture Kickoff, one meaningful question at a time
- Persistent planning progress and open questions
- Requirements, users, journeys, MVP/scope, modules, data, contracts, security, deployment, UX, QA
- Explicit architecture review and approval gate
- Architecture may be revised later through governance/ADR flow

### GitHub control plane
- GitHub Issues/Projects as shared task truth
- Architecture → implementation task planning
- Acceptance criteria, dependencies, risk, readiness
- Publish tasks only after architecture approval
- Idempotent task publication
- Claiming updates ownership/status
- PR open → In Review
- Merge/closure → Done
- Project Sync reconciles stale state

### Team identity
- Dynamic team registry with stable IDs
- Name, GitHub identity, role, status
- Local machine identity stored outside Git
- Human ownership separated from AI worker attribution
- Project Sync personalized to current human

### Professional agent behavior
- Shared engineering constitution
- Role-specific charters
- Reuse-before-create
- KISS/YAGNI/clear boundaries
- No silent architecture changes
- No fake certainty
- Evidence-based completion
- Independent reviewer separation
- Security and database specialists invoked conditionally

### Design
- Architecture before final UI implementation
- UX planning → wireframe → approval → design context → frontend implementation → Design QA
- Impeccable is the core general design skill, version pinned when adopted
- Project-specific design skills only when relevant (e.g. shadcn, mobile, visualization)
- External design MCP/API/account integrations optional only

### Efficiency
- Task-scoped context
- Minimum necessary retrieval
- Deterministic checks before AI judgment
- No unnecessary whole-repo scans
- Specialist invocation only when relevant
- Stable summaries/state instead of replaying chat history

### Reliability
- Idempotent automation
- Anti-thrashing after repeated materially similar failures
- Failure evidence collection and escalation
- Safe retry semantics
- Harness Improvement Loop for reusable lessons

### Portability
- Core workflow independent of IDE/model vendor
- Root `AGENTS.md` is the shared entrypoint
- Runtime-specific adapters may map canonical skills/rules to local mechanisms
- VS Code, Orca, Kiro, Codex, Claude, Gemini are supported as adapter targets; v1 validation begins with VS Code + Codex

## Optional / future
- Graphify/repository-intelligence integration
- External design MCP/API connectors
- Advanced presence/heartbeat server
- Large-scale distributed orchestrator
- Additional cloud/provider adapters

## Non-goals
- Automatic permission grants to GitHub
- Uncontrolled recursive self-modification
- Loading every available skill into every session
- Making any external tool a single point of failure
