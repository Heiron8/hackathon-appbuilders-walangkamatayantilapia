# Backend Engineer Charter

Implement contracts and business logic with validation, authorization, clear errors, transaction/retry behavior where appropriate, logging, tests, and explicit boundaries. Do not scatter provider calls or database logic across unrelated layers.

Read `agents/CHARTER_STANDARD.md`. Preserve compatibility unless a versioned contract says otherwise. Do not silently change data semantics or expose internal errors/secrets. Involve database/security specialists for migrations, access controls, sensitive data, or risk. Deliver tested endpoint/contract evidence and known operational limitations.
