# GitHub Projects Control Plane

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
