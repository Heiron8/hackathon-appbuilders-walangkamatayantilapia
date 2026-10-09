# GitHub Projects Control Plane

GitHub Issues are durable task truth; GitHub Projects is an optional status view.

## Issues-first claiming

When Projects is unconfigured or its initial lookup is unavailable, the Lead Architect serializes assignment: check the open Issue's current status and assignees, mark it `status:ready`, assign exactly one registered owner without replacing another owner, and reread GitHub. Developers run `python scripts/claim_task.py ISSUE_NUMBER` from clean main or their existing task branch/worktree. The script requires matching authenticated/local identity and approved implementation, rereads ownership/status, then replaces `status:ready` with `status:in-progress`. Same-owner In Progress retries reuse the branch and do not repeat the status write.

Use exactly one workflow label: `status:backlog`, `status:ready`, `status:in-progress`, `status:in-review`, `status:blocked`, or `status:done`. Create labels deliberately before using them. Labels never substitute for acceptance criteria, dependencies, verification or independent review. Issue claiming refuses unassigned, competing, closed, missing/ambiguous or later-status tasks. GitHub provides no atomic compare-and-set for assignees/status; Lead serialization and no concurrent manual edits during a claim are required. Detected races stop and require Lead reconciliation; the script never rewrites another owner's claim.

For maintenance Issue #10, the Lead explicitly authorized the temporary manual claim: verified Ready/unassigned, assigned Heiron8, reread exclusive ownership, transitioned labels to In Progress, and reread again. The old Project-only script was not run or reported successful. This procedure permits this implementation without changing architecture or product tasks.

## Canonical statuses

`Backlog → Ready → In Progress → In Review → Done`

`Blocked` may be entered from Ready/In Progress when a real dependency prevents progress.

## Transition rules

- Architecture/task planning approved but not yet ready → Backlog
- Definition of Ready satisfied and dependencies clear → Ready
- Human/worker claims Ready task, assigns owner, and prepares isolated branch/worktree → In Progress
- Delivery creates/links PR → In Review
- Linked issue/task is completed/closed after required review/merge → Done
- Blocking dependency appears → Blocked

## Automation contract

All GitHub mutations must be idempotent where practical. Before creating an issue, search for its stable `workspace-task-key`. Before adding an item to a Project, re-adding must be safe. Status updates use the configured project number/owner and Status field.

The workspace scripts require GitHub CLI authentication. Project operations require the account/token to have GitHub Projects permission. The workspace never stores GitHub credentials in the repository.
