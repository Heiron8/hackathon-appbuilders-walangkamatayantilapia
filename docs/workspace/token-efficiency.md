# Token Efficiency Policy

1. Load the minimum context needed for the current task.
2. Prefer targeted retrieval over whole-repository scans.
3. Give workers task-scoped context only.
4. Do not resend unchanged architecture/docs unnecessarily.
5. Run deterministic tooling before AI analysis.
6. Persist summaries/state rather than replaying full chat history.
7. Invoke specialists only when their expertise is relevant.
8. Avoid duplicate agents inspecting the same material without purpose.
9. Stop/release workers after their task is complete.
10. For large systems, optional repository-intelligence integrations may improve context retrieval.
