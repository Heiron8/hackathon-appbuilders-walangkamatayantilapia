# Tanaw: Compact Architecture Proposal

Status: APPROVED Tanaw MVP v0.1 architecture and compact task plan, by the requesting Lead Architect on October 9, 2026. Actual approver name/GitHub identity were not supplied; no identity is inferred. Approval is recorded using `scripts/architecture_state.py --approve-by` and covers the proposed conservative grammar and Issues-first coordination, subject to the conditions below. Architecture approval does not claim runtime verification or final design approval.

This kickoff session authorizes approval records and task preparation/publication only: no application code, dependencies/models, commits or pushes. Future implementation sessions need actual ownership; frontend implementation additionally needs human approval of the editable Figma design. Suggestions remain disabled until technical validation passes. Planning artifacts remain local/uncommitted until a separately authorized reviewed delivery.

Confirmed by the team: React/Vite + Python/FastAPI preference; local Ollama; no cloud inference, authentication, mandatory database, microphone, or complex deployment. Functionally complete and demo-ready by **2026-10-10 08:00 Asia/Manila (UTC+08:00)**; submission deadline **10:00**. Four developers; actual names/identities are not registered yet.

## 1. product-boundary

Offline picture-to-speech AAC for non-speaking/minimally speaking children, with caregivers supporting setup. P0: stable board, ordered message construction, offline speech independent of AI, local-AI expansion with explicit user approval. Expansion is optional to the end user but remains a P0 engineering commitment. P1: typed-question suggestions only after their separate feasibility gate passes. No child accounts, clinical claims, conversation archive, custom vocabulary editor, microphone, or remote inference.

Demo assumption: one Windows laptop, browser, local backend, and installed local model. Other platforms and independent phone/tablet operation are unverified. Responsive layouts are required; a LAN/device deployment is outside this proposal.

## 2. primary-user-journey

Open board -> select labeled pictures -> see ordered message -> Speak selected words. Optional: Improve sentence -> inspect original alongside candidate -> approve or explicitly edit -> Speak approved sentence. Any card edit invalidates approval and pending AI output. Suggestions: caregiver types a question -> request options -> child chooses existing cards -> ordinary message/review/Speak flow. Nothing is automatically selected or spoken.

No, Stop, Help, Repeat, Something else, and access to the complete vocabulary stay available. Pressing the Stop card selects the communication word; a separately labeled Stop audio control interrupts playback. Repeat is a communication card; replaying speech requires an explicit Replay audio action.

## 3. architecture-style

One local web application, one backend process, one external local runtime. React/Vite owns interaction and baseline AAC; FastAPI validates optional inference and serves the production frontend. A small runtime adapter isolates Ollama HTTP details. No orchestration framework, service mesh, ORM, agent framework, retrieval system, or extra application service.

Proposed implementation locations (not created): `frontend/`, `backend/app/`, `shared/vocabulary.json`. Use native semantic controls and small CSS tokens; UI libraries need a demonstrated benefit before addition. Backend uses FastAPI/Pydantic, Uvicorn, and one asynchronous HTTP client, with exact versions reviewed/pinned when implementation is authorized.

## 4. modules-responsibilities

| Module | Responsibility | Developer lane |
| --- | --- | --- |
| Shared vocabulary/contracts | Stable IDs, order, vocabulary version, grammar specification | Developer 1 / Lead |
| Frontend communication | Selection, review/approval, stale-result handling, approved responsive UI | Developer 2 |
| Backend communication + inference | Schema/grammar validation, bounded Ollama requests, model evaluation | Developer 3 |
| Browser speech + bundled fallback assets | Local voice selection, ordered card audio, stop/replay, truthful unavailable states | Developer 4 |
| Startup / verification / integration | Dependency manifests, local serving, configured existing verifier, frequent merges | Developer 1 |
| Figma/design preparation | Editable design foundation, design handoff and human review coordination | Developer 2, human-reviewed by Lead |
| Independent Design QA / QA / demo | Independent rendered design checks, fresh setup, video/disclosures | Developer 4; own speech changes reviewed by Developer 2 |

These are approved developer lanes, not human assignments. Six implementation issues are published; all remain unassigned until actual member identities are supplied. Split frontend speech behind a small interface so Developers 2 and 4 can work independently. Independently review every implementation; nobody reviews their own change as independent approval.

## 5. interfaces-contracts

[contracts.md](contracts.md) is the implementation reference for vocabulary v1, `/api/health`, `/api/expand`, `/api/suggest`, speech, and error/state rules. Frontend and backend consume one canonical vocabulary file. Vocabulary/order changes require both owners to review; IDs never change because a label is translated.

## 6. data-flow

Baseline: bundled vocabulary + ordered IDs -> frontend labels -> explicit Speak -> local browser synthesis or bundled card audio. This route makes no AI request and survives an unavailable inference API.

Expansion: selection snapshot + version/revision -> backend validates IDs -> bounded local model call -> schema + approved grammar validation -> candidate preview -> user approval -> explicit Speak. Backend never invokes speech. Current selections must match the response snapshot before showing/accepting it.

Suggestions: typed question + vocabulary version -> model ranks vocabulary IDs -> backend validates known unique IDs -> separate options panel. Selecting an option appends that card through the ordinary board action. The primary grid/order is unchanged.

## 7. persistence-strategy

Bundle vocabulary, symbols, card recordings, and fonts locally. Keep selected messages, question text, generated candidates, and approval in memory; reload clears them. No conversation logging, database, analytics, or child identity. Model files stay in the runtime's local model directory, outside Git. Download/build/setup need internet once; operation afterward must pass a disconnected restart/reload test.

## 8. external-integrations

Only the locally installed Ollama HTTP API at `http://127.0.0.1:11434`. Start feasibility with `qwen3:1.7b` Q4_K_M; pin the successful runtime/model digest after measurement. A 4b candidate is a bounded second attempt if small-model quality fails and memory permits, not a requirement. Keep runtime-specific configuration in the adapter; no cloud endpoint or remote fallback. Verify licenses for the exact runtime version and model weights/quantization, including permitted use/redistribution and required notices, alongside symbol/audio asset-license checks before bundling or presenting them.

Request JSON-schema output, non-streaming, non-thinking where supported, approximately 2,048 context tokens and at most 256 generated tokens. Initial temperature 0 is a test setting, not a semantic guarantee. Use `OLLAMA_NO_CLOUD=1`; verify disconnected operation. Runtime/version compatibility and hardware acceleration remain unverified.

Primary speech: planned installed browser voice reporting `localService: true`; offline playback must be verified on the demo browser with internet disconnected. Fallback: licensed/team-recorded bundled clips for every card, played in selection order; stop/replay must be verified in both modes. Clips speak selected card labels, not arbitrary edited/expanded sentences. If full-sentence synthesis is unavailable, offer an explicit Speak selected cards action instead, without claiming the expanded sentence was spoken. A working full-sentence local voice is the planned AI-expansion demo prerequisite.

References: [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs), [thinking controls](https://docs.ollama.com/capabilities/thinking), [local-only configuration](https://docs.ollama.com/faq), [browser local voice property](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesisVoice/localService).

## 9. failure-fallback

Five-second total backend inference deadline; frontend abandons the request after six seconds. One inference call active at a time; reject extra calls as busy rather than building a queue. Cold startup may exceed the limit: warm the selected model during setup, report availability, and keep AAC usable while warming. Do not automatically retry or pull models in response to user actions.

On unavailable model/backend, timeout, malformed output, unsupported grammar, or stale response: retain selections; show brief optional-assistance status; Speak selected words stays available. Only AI controls are disabled during inference. Cancel/selection edits discard stale results even if runtime generation has not stopped. Output caps bound remaining work.

Primary voice failure offers card audio explicitly. Missing card clips and missing local voice are a speech readiness blocker; text display alone is not a passing picture-to-speech demonstration.

## 10. security-boundaries

Bind FastAPI and Ollama to loopback. Accept only known localhost/127.0.0.1 hosts and the app's exact development/final origins; no wildcard CORS. Require JSON for mutation requests; validate body limits, versions, IDs, lengths, and output grammar. Runtime URL/model are server-controlled, never accepted from user requests. Render strings as text, not HTML. Questions are untrusted data, never instructions or tool calls. No model tools, shell execution, file access, remote fetches, secrets, or identifiable child demo data.

Log only request ID, outcome code, and duration; never question/message text. No child telemetry, local history, or cloud speech fallback. A locally served application is not approved for public/LAN exposure. Account/authorization infrastructure is unnecessary within this explicit boundary.

## 11. deployment-route

Proposed development: Vite `127.0.0.1:5173`, FastAPI `127.0.0.1:8000`; Vite proxies `/api` and imports the canonical shared vocabulary. Lead configures Vite to allow only the necessary shared workspace path. Final: build frontend once; FastAPI serves its static build and `/api` at `http://127.0.0.1:8000`; Ollama remains separate. No hosted deployment or service worker is required for this local-server MVP. A stopped backend does not disable direct AAC in an already loaded page, but a fresh page/reload still needs the local static server running. Internet-disconnected operation is not a claim of serverless operation.

After authorized setup, document exact locked installation commands, model download/digest, installed voice/card assets, and separate Ollama/backend launch commands. Planned backend entry point: `backend/app/main.py`; local launch from `backend/`: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. This command is a specification, not an existing executable application.

Extend existing `verification.commands` with frontend tests/build and backend contract/fallback tests. Keep existing harness checks and independent review; make CI cover actual product checks once manifests exist. Perform keyboard/contrast/responsive QA and an internet-disconnected cold restart, browser reload, model-stop test, and fresh-device setup. Do not treat harness structural PASS as product PASS.

## 12. constraint-tradeoffs

Accessibility: proposed minimum 64px communication-card targets, 48px utility targets, text contrast at least 4.5:1, non-text boundaries/focus at least 3:1, visible focus, logical keyboard order, text labels plus symbols, reduced motion, and no color-only meaning. Keep card ordering/positions stable within a viewport/profile; responsive column changes follow deterministic row order, never AI relevance. Preserve the message while navigating. No timed decisions or auto-speech.

Safety tradeoff: accepted expansion is deliberately limited to the finite grammar in contracts; unsupported sequences retain direct card speech. Actual local model-generated candidates are validated, not replaced by scripted answers presented as AI. General free-form intent preservation cannot be guaranteed. Filipino labels/voice quality and clinical usability are unverified; demonstrate only tested language/phrasing.

Speed tradeoff: fixed vocabulary, no persistence/accounts, no microphone, one demo device, short PRs, parallel lanes, early integration. Suggestions are optional and remain disabled unless their independent evaluation passes. Detailed ADRs/integrations/production infrastructure are deferred.

Feasibility proposal: 12 expansion fixtures and 12 question fixtures including negation, ambiguity, refusals, unknown content, and prompt injection. At least 30 timed warm calls for the enabled model/feature; record cold start, p50/p95, RAM/VRAM, and actual off-network evidence. Expansion must reject all unsupported additions in the fixtures and pass valid supported inputs at least 90%; suggestion relevance must reach 90% by independent human review, with all returned IDs valid and no unsafe imposed choices. Warm p95 target <=3 seconds, enforced deadline 5 seconds. Missing performance evidence is not a pass. Benchmark-derived changes to targets/model need Lead review.

Planned checkpoints: first integrated baseline within 90 minutes of implementation authorization/design approval; integrate P0 expansion next; decide suggestions within the first two hours after models/setup are available. Freeze new features **October 10 06:00**, complete fresh/offline verification **07:00**, finish demo rehearsal/video **08:00**, then reserve **08:00-10:00** for submission and corrections. Slower setup reduces optional scope, not baseline AAC/review time.

## Review and unresolved evidence

- Lead Architect: requesting user; actual name not supplied. Architecture and compact implementation plan APPROVED in the development-kickoff request; approval record contains role attribution only, not an invented member identity.
- Design: [Figma-ready brief](../design/ux-plan.md) prepared; actual editable design and human approval NOT PRESENT. Frontend implementation waits for that approval.
- Feasibility: runtime, model performance, local voice, clips, runtime/model/asset licenses, and setup unverified; no dependencies/models installed by this planning step.
- Collaboration: Issues-first coordination APPROVED; GitHub Projects remains optional/unconfigured. Use manual issue creation/assignment/status with the existing stable-key, task-body and duplicate-check conventions; Project-dependent claim/publication helpers require verified access. See [approved implementation handoff](../plans/active/tanaw-mvp-plan.draft.md) and [canonical approved task input](../plans/approved-tasks.json). All tasks remain unassigned until real identities are supplied.
