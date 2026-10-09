# Submission Readiness

Reusable checklist for the actual event requirements and final integrated build. Leave challenge-specific fields blank until known. Fill each applicable row with a classification, evidence/check time, and an owner or next action. Blank cells and unchecked artifacts are not PASS. This checklist prepares a submission; it does not submit anything or add an architecture approval gate.

- Event/challenge:
- Submission rules source and version/date:
- Deadline and timezone:
- Required links/files, disclosure rules, and demo duration/format:
- Repository and integrated commit/build:
- Deployment URL (if required):
- Demo artifact location (if required):
- Check time:
- Demo owner:
- Technical-question owner:
- Final human reviewer and review evidence:
- Overall readiness:

## Evidence classifications

- **VERIFIED:** relevant evidence demonstrates the claim/check for the identified build and scope. Cite the result and check time; code or documentation alone does not prove runtime behavior.
- **KNOWN BUT NOT VERIFIED:** an artifact or behavior is known to exist, but the necessary check has not been performed or its evidence is stale. A deployment URL without an external smoke test belongs here.
- **NOT READY:** a required artifact, implementation, rule confirmation, or check result is missing, failing, or blocked. A claimed feature with neither evidence nor a working implementation belongs here.
- **NOT APPLICABLE:** known requirements and the actual product justify exclusion; record the reason. For example, no database is needed by the product. Unknown applicability is not NOT APPLICABLE.

Use NOT DOCUMENTED for missing records and NEEDS TEAM CONFIRMATION for unresolved facts alongside the appropriate classification. Neither label counts as VERIFIED.

Overall readiness is VERIFIED only when the requirements are known and every required item is VERIFIED (or justifiably NOT APPLICABLE). Any required NOT READY item or unknown requirement makes the overall result NOT READY. Otherwise, any required KNOWN BUT NOT VERIFIED item makes the overall result KNOWN BUT NOT VERIFIED. List open items and next actions; never convert missing evidence into PASS.

## Checklist

Combine related checks only when evidence covers each part. Repository harness verification must not stand in for product verification or a public smoke test.

| Area / check | Classification | Evidence, build and check time | Owner / next action |
| --- | --- | --- | --- |
| Repository: correct repository and latest integrated code match the submitted build | | | |
| Repository: no accidental secrets; secret scanning/relevant inspection completed | | | |
| Repository: README/use instructions sufficient; required disclosures complete | | | |
| Product: primary journey works on the final build | | | |
| Product: critical error/fallback path checked | | | |
| Product: no known demo-blocking issue; product verification passes | | | |
| Deployment: public URL works if required; fresh device/incognito access checked | | | |
| Deployment: environment/configuration valid; secrets not exposed | | | |
| Demo: final video exists if required and opens successfully | | | |
| Demo: real functionality shown; no unverified feature claims | | | |
| Demo: duration/format meet known requirements | | | |
| Technical defense: architecture explanation and important tradeoffs prepared | | | |
| Technical defense: limitations and relevant judge Q&A prepared with evidence | | | |
| Presentation: product story agreed; demo and technical-question owners known | | | |
| Presentation: fallback path known if the live demo fails | | | |
| Submission: required links/files present and accessible; team information correct | | | |
| Submission: required tool/AI disclosures complete | | | |
| Submission: final package reviewed by another human; review evidence recorded | | | |

## Open items

- Missing requirements or team confirmations:
- Missing/failing artifacts or checks:
- Known but unverified claims:
- Next actions and owners:
