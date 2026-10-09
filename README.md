# Professional AI Workspace Template

A reusable, GitHub-centered workspace for planning, delivering, reviewing, and recovering software projects. The repository holds durable project truth; chat history and agent runtimes do not.

## Start a new project

1. Create a repository from this template and configure its remote. Keep the starter state unapproved until the new project's architecture is reviewed.
2. Clone/open the repository and run `python scripts/bootstrap.py` from its root.
3. Follow the reported next action: fix only a reported prerequisite/access blocker, continue Architecture Kickoff, or claim an available Ready task.

Bootstrap checks Git, supported Python and GitHub CLI availability; runs Project Sync; checks authentication and repository access; resolves the local member identity; installs Git hooks; runs canonical workspace verification; then reports `READY FOR ARCHITECTURE`, `READY TO CLAIM`, or `NOT READY`. It is safe to rerun. Local identity is stored in ignored `.workspace-local/`; new shared members are registered in `.orchestrator/team.json` and should be reviewed through the normal Git workflow.

Run `python scripts/project_sync.py` for normal synchronization. Clean main automatically fetches origin/main and fast-forwards safely before reading project context. It reports UPDATED, ALREADY CURRENT, NOT UPDATED with a reason/action, or OFFLINE using local state. Dirty/staged/untracked work, task branches, local-ahead/divergent history and unfinished operations are preserved. No automatic reset, rebase, stash or conflict resolution occurs. Bootstrap runs Sync after prerequisites and before shared config/identity reads; authentication, onboarding, hooks and verification remain required. Offline Sync works independently of Bootstrap's authenticated setup requirements.

Projects is optional: use the [Issues-first claiming procedure](docs/workspace/github-projects.md#issues-first-claiming). The Lead assigns one registered owner to a Ready Issue; that developer runs `python scripts/claim_task.py ISSUE_NUMBER`. Only explicit Ready/owned In Progress retries are accepted, and failed Project mutations never silently fall back.

This AppBuilders-ready template currently selects `hackathon-24h` in `workspace.config.json`. See the concise [24-Hour Hackathon Operating Mode](docs/workspace/hackathon-mode.md); it compresses ceremony without weakening architecture approval, verification, review, security, or engineering standards.

Enter the project name in `workspace.config.json`. Set GitHub owner, repository, and Project number only after creating the new repository and Project. A GitHub Project is not required while it remains unconfigured. Product dependencies may be added later after the project stack is selected; the workspace harness itself uses only the Python standard library.

Persist requirements, decisions, UX, and review evidence in `docs/`. Publish an approved task plan only after architecture approval and a deliberate GitHub configuration check. Work then proceeds through claim, isolated branch or worktree, verification, PR, independent review, merge, and reconciliation.

The template has no approved product architecture, published tasks, members, GitHub identity, or live integration claims. `docs/plans/approved-tasks.example.json` shows the publication format; create `approved-tasks.json` only after approving a project-specific plan. The external Impeccable design skill is disabled until a version is pinned.

## Verification boundary

`verify-workspace.ps1` checks the local harness and tests. It does not prove live GitHub publication, a hosted product, or the new project's behavior. Configure `verification.commands` as the product is implemented.

See `AGENTS.md`, `WORKSPACE_SPEC.md`, and `WORKFLOW.md` for the full professional workflow.

For final-stage requests such as "prepare technical defense" or "prepare judge Q&A", use the repository's [technical-defense skill](skills/technical-defense/SKILL.md). It prepares evidence-based answers with [a compact response template](response-contracts/technical-defense.md) and, when requested, checks [submission readiness](docs/qa/submission-readiness.md). These reusable scaffolds contain no product answers or event-specific requirements and are not loaded for normal coding work.

For "prepare demo video", "generate product demo", "create submission video" or "update demo video", Member 4 can use the [Demo Video Producer charter](agents/demo-video-producer/CHARTER.md) and [demo-video skill](skills/demo-video/SKILL.md). The isolated [executable pipeline and activation prompt](demo/README.md) cover a generic rehearsal, Playwright footage, local speech/manual audio, Remotion composition, FFmpeg fallback and MP4 validation. Final footage requires the verified integrated product; its evidence feeds the existing Submission Readiness checklist. Demo dependencies and outputs stay outside product/Core state, and no video is uploaded or submitted automatically.
