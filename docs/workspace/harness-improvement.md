# Harness Improvement Loop

Use when a repeated failure or newly discovered lesson is reusable beyond one task.

1. Stop blind retries after repeated materially similar failures.
2. Gather evidence: logs, commands, diffs, state, failing criteria.
3. Identify root cause and scope.
4. Decide whether lesson is task-specific or reusable.
5. If reusable, propose the smallest change to a skill/rule/script/test/doc.
6. Add a regression check where practical.
7. Validate the improvement.
8. Deliver it through normal Git/PR review.
9. High-impact governance/security/deployment changes require Lead Architect/team approval.

The harness learns through versioned repository improvements, not uncontrolled recursive self-modification.
