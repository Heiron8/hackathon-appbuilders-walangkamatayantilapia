# Architecture Standards

Architecture is requirements-driven, not provider-driven.

Use this decision order:

`requirements → constraints → deployment/system pattern → concrete technologies/services`

Prefer clear module responsibilities, explicit data ownership, and documented contracts. Significant decisions go through ADRs. Architecture approval is not permanent freezing; later significant changes must use governance/review rather than silent drift.

The Architecture Planner must distinguish known facts, assumptions, decisions, and open questions.
