# Engineering Constitution

## Professional baseline

Every agent and human contributor should:

1. Understand the task and acceptance criteria before editing.
2. Inspect existing implementation, conventions, contracts, and reusable assets.
3. Prefer the smallest correct change.
4. Preserve cohesion and avoid unnecessary coupling.
5. Reuse existing models/components/services/utilities when that improves consistency.
6. Avoid both needless duplication and premature abstraction.
7. Handle error, loading, empty, permission, and failure states appropriate to the change.
8. Add/update tests when behavior changes.
9. Run deterministic verification before semantic claims.
10. Explain unverified areas honestly.

## Anti-slop rules

Do not:
- add unrelated files/refactors to a focused task
- create placeholder logic and call it complete
- duplicate existing functionality without checking first
- add random dependencies
- create giant god components/classes/services without justification
- swallow errors silently
- hardcode secrets
- invent APIs/contracts that conflict with approved docs
- bypass failing checks
- silently change architecture
- claim a security guarantee that was not actually established

## Evidence-based completion

A completion report should state what was changed, which acceptance criteria were verified, which checks ran, and what remains unverified.
