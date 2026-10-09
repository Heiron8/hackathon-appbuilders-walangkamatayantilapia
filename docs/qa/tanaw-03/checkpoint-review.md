# TANAW-03 / Issue #4: first checkpoint and read-only review handoff

Owner: Jerald Lopez (`LadlopezGit`), authenticated and exclusive live Issue owner.
Branch: `task/issue-4` in the original repository; base `d26c95987f8e48bac83abaf88626c84b9059eaf4`.
No additional worktrees/clones or edits to teammate-owned files. Scoped Conventional Commits and Draft PR publication are authorized after final checks; merge and Issue closure remain unauthorized.
Status: the requesting user reports **PASS for the corrected code checkpoint** on October 10, 2026. The subsequent five-file test-import compatibility correction has an authenticated **PASS from Ahron / Heiron8** in [Issue #4's review comment](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/4#issuecomment-6087656421), posted October 10 at 03:18:50 PHT. GabDeGuz's final offline decision is not inferred. Earlier sections below retain historical checkpoint observations; the final publication record supersedes their pending correction-review status.
Overall task acceptance: **NOT COMPLETE**. Saved transcripts document disconnected adapters and correct expansion; final offline evidence approval and production/AAC integration remain open.

## What changed

- `backend/app/validation/contracts.py`: strict UUID/revision/locale/card-selection and model-output schemas; unknown fields rejected.
- `backend/app/validation/vocabulary.py`: loader for Lead-owned canonical 32-card `tanaw-v1` vocabulary; no production fixture fallback.
- `backend/app/validation/grammar.py`: finite approved Want/Not-Want renderings and exact source-order/output validation. Unsupported selections never generate an invented sentence.
- `backend/app/ai/ollama.py`: fixed loopback HTTP adapter, schema output, non-thinking/non-streaming, context/output caps, bounded responses, one active request, five-second total deadline, no retries/downloads/tools/text logging.
- `backend/app/api/communication.py`: `/api/health` and `/api/expand` router; request/body/version/ID/host/origin checks; approved error envelopes and metadata-only inference logs. Suggestions are absent and health reports them disabled.
- `backend/app/ai/evaluate.py`: explicit setup warm-up and real model benchmark; immutable report paths and no generated text in evidence.
- `backend/tests/`: contract/meaning/failure tests, clearly synthetic vocabulary, verification-only loopback app and HTTP smoke runner.
- `docs/qa/tanaw-03/`: measured results, environment snapshots and this handoff.

No edits to shared vocabulary, app main, manifests, frontend, speech assets, governance or verification configuration.

## Verification evidence (October 9, 2026, Philippine time)

- Backend unittest suite: 24 tests PASS, including every approved grammar combination, 12 supported and 12 unsupported fixture sequences, invented content/dropped negation/reordered source rejection, bad schema/body/origin/host/version, unavailable/busy paths, cancellation recovery and an actual five-second timeout.
- `http-ready.json`: six checks PASS over actual Uvicorn/loopback HTTP with real Ollama: health, positive/negative expansion, unsupported selection, unknown ID and vocabulary mismatch. Vocabulary is explicitly test-only; this is not integrated production proof.
- `http-unavailable.json`: six checks PASS with the owned Ollama process stopped. Health returns HTTP 200/unavailable; supported expansion returns 503; unsupported selection still returns 200.
- `online-benchmark.json`: original load-only warm-up FAILED: 26/30 accepted, four timeouts, p50 230.33 ms, p95 5008.83 ms. Initial weight-load request took 19942.42 ms. First-generation initialization continued after loading; failures are retained, not relabeled PASS.
- `online-warmed-benchmark.json`: after runtime restart and explicit complete-fixture warm-up, 30/30 accepted over all 12 fixtures, p50 216.91 ms, p95 256.24 ms. Setup inference (load + generation) 1985.09 ms; this restart benefited from previously initialized system caches and is not a fresh-install cold-start guarantee.
- Workspace verifier: structure/contracts/charters/state/team/harness tests/secret checks PASS; live GitHub integration is separately verified via authenticated identity and Issue reads. Existing configured verifier is structural only; it is not product acceptance.
- `test-environment.txt`: exact temporary test environment. `pip check` PASS; Python 3.14.6. Direct tested packages: FastAPI 0.143.0, Pydantic 2.14.0, httpx 0.28.1, Uvicorn 0.54.0. Lead still owns dependency compatibility review/pinning in production manifests.
- `hardware.json` / `hardware-warmed.json`: identified `LADLAPTOP`, Windows 11, Core Ultra 7 255HX, ~15.4 GiB RAM, RTX 5070 Laptop GPU 8151 MiB, driver 617.14; Wi-Fi **Up**. Warm runner working set 833490944 bytes, private committed memory 2664366080 bytes; Ollama working set 75526144 bytes. These metrics are not interchangeable with model allocation. Ollama `/api/ps` reports model/VRAM allocation 1465615645 bytes; total device use includes other programs.

Historical October 9 checkpoint: the user chose to keep the network connected, so offline inference/restart was NOT VERIFIED at that time. Later manual-session observations are described below without rewriting the original evidence. Baseline board/speech and fresh production setup remain separate integration/QA evidence.

## Tested runtime/model and licensing

- Official standalone Ollama **0.40.2**, installed outside Git at `%LOCALAPPDATA%/Tanaw/ollama/v0.40.2`; archive SHA-256 `e29ad1d5063dd4b54b2492d9b00adab2cff9621bfa654b6c92aa8d6f1fdfe7fc` verified against the official release asset digest.
- Runtime process has `OLLAMA_NO_CLOUD=1`, loopback binding, one parallel generation and one loaded model. The application adapter disables environment proxy use and redirect following. Runtime logs report cloud disabled; an internet-connected run does not prove absence of all external runtime traffic.
- Model **qwen3:1.7b**, Q4_K_M, installed in the ordinary Ollama model directory outside Git. Tested manifest digest: `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`. Weight blob digest: `3d0b790534fe4b79525fc3692950408dca41171676ed7e21db57af5c65ef6ab6`. Tag/digest must be checked before the demo; a mutable tag alone is not a pin. Runtime metadata displays `2.0B`, while the model's internal name/tag is Qwen3 1.7B; both observations are preserved.
- [Ollama 0.40.2 license](https://github.com/ollama/ollama/blob/v0.40.2/LICENSE): MIT. [Qwen3-1.7B license](https://huggingface.co/Qwen/Qwen3-1.7B/blob/main/LICENSE): Apache 2.0; installed model's `ollama show` also reports Apache 2.0. No binaries/weights are redistributed by this change. Retain applicable bundled component/model notices if packaging them for delivery; these links are not a complete redistribution audit.
- Request compatibility checked against official [structured-output](https://docs.ollama.com/capabilities/structured-outputs), [chat](https://docs.ollama.com/api/chat) and [local-only configuration](https://docs.ollama.com/faq) documentation.

## Integration handoff to Heiron8 (Issue #1)

Import `Vocabulary` from `app.validation.vocabulary`, `OllamaRuntime` from `app.ai.ollama`, and `create_router` from `app.api.communication` in the Lead-owned `backend/app/main.py`.

1. Load `shared/vocabulary.json` from a resolved repository-root path. Missing/invalid canonical data fails startup; do not substitute `backend/tests/fixtures.py`.
2. Create one `OllamaRuntime()` and include `create_router(vocabulary, runtime)`. Close it with `await runtime.aclose()` in the app lifespan. Run a single backend worker so the one-active-call limit applies to the app.
3. Pin compatible production dependencies and verify the runtime/model version and digest above on the demonstration laptop. Never install or pull from an API request. Complete-fixture model warm-up is an explicit setup command, not an automatic UI retry.
4. Preserve loopback/static serving, exact allowed origins/no wildcard CORS, and top-level JSON error envelopes for app-wide 404/405/validation/internal errors in app assembly. This router owns its input/inference errors; it does not override unrelated app handlers or implement static serving.
5. Configure `verification.commands` to run product checks. From `backend`, the suite is `python -m unittest discover -s tests -v`. Production startup is still blocked on the Lead-owned foundation.

Verification-only server: from `backend`, `python -m uvicorn tests.checkpoint_app:app --host 127.0.0.1 --port 8000 --no-access-log`. It uses synthetic vocabulary; never present it as the integrated application.

Benchmark from `backend`: `python -m app.ai.evaluate --output ../docs/qa/tanaw-03/<new-report-name>.json`. No report is overwritten. Default is 30 calls after explicit full-fixture warm-up. Its setup may take up to 120 seconds; product inference always retains its five-second deadline.

## Original checkpoint review handoff (historical)

- **Heiron8**: compare code, task and frozen contracts; review intent/negation validation, boundaries/error envelopes/dependencies, deadline/busy behavior, data/logging and simple layer responsibilities. Run tests without modifying the implementation. Confirm app-registration/shared-vocabulary requirements separately.
- **GabDeGuz**: independently witness the positive and negative examples and rejected additions, then actual Wi-Fi/Ethernet-disconnected runtime restart/inference. Record laptop/runtime/model digest/time/network condition. Follow with integrated baseline speech/fallback proof under Issue #5.
- Return `PASS` or `CHANGES REQUIRED` using `response-contracts/pr-review.md`, with specific evidence. No self-review is counted as independent approval. Do not commit or push before the required independent review passes.
- Suggestions stay disabled. No claim of offline acceptance, integrated AAC, fresh setup, or full Issue completion is authorized by these online checkpoint results.

## Scoped harness lesson proposal (deferred)

Two reusable observations: a model weight-load response is insufficient evidence that first-generation initialization is warm; and current `git diff`-based guardrail/whitespace commands omit new untracked files. This checkpoint explicitly scans its untracked files as well. Propose later regression coverage through the Harness Improvement Loop; no harness/governance edits are part of Issue #4.

## October 10 correction checkpoint: pending independent re-review

The user requested corrections for canonical vocabulary validation and API error envelopes. Live Issue #4 is still OPEN, exclusively assigned to LadlopezGit, with `status:in-progress`. No formal review text is currently stored in its comments; the user-supplied findings are the authorized correction scope. No commits, pushes, merges, closure, claims on other tasks or teammate file edits are performed.

### Resolved within Issue #4 ownership

- `validation/vocabulary.py` now checks the exact frozen `tanaw-v1` ID sequence, required root/card fields, English labels, per-ID categories, integer board positions and exact local symbol/audio paths. Unknown IDs replacing missing IDs cannot pass by preserving a count of 32. Direct construction rejects altered IDs/version or a mutable ID set. Missing/corrupt files are not repaired or replaced with fixtures.
- Frozen IDs/metadata rules are validation constraints taken from the approved contract, not another production vocabulary source. `Vocabulary.from_document()` consumes the actual document loaded by `shared.vocabulary.load_vocabulary()`, allowing Heiron8's canonical loader to remain the sole production source. Test documents derive independently from the approved table, not from the implementation's constants.
- `api/errors.py` exposes `install_error_handlers(app)` for the Lead to register. Framework HTTP errors use the approved envelope while preserving status and exception headers, including 405 `Allow`. Framework validation errors use a safe 422 envelope without returning request contents. Existing inference/selection errors retain their previous codes/status/messages.
- The installer is wired only in the Issue #4 verification app/tests. No production `main.py`, shared validator/data, manifests, CI, frontend or speech files are changed.
- Relative internal imports support both existing `app...` test/startup commands and the foundation's repository-root `backend.app...` namespace. AI grammar/order/negation logic and five-second/busy/unavailable behavior remain unchanged.
- Benchmark/HTTP report scope now states that networking is not checked by those commands. A manual witness must supply real network/restart evidence; connected results cannot become an offline PASS by naming a report “offline.” Previous evidence files are preserved.

### Verification

- Backend: **35 tests PASS, zero failed/skipped**, including the previous behavior checks and new vocabulary/404/405/header/privacy regressions.
- Workspace: **139 tests run, 138 PASS, zero failed, one skipped** optional demo dependency test; quick structure/state/team/delivery-gate checks and configured structural verifier PASS. Product verification configuration still belongs to Issue #1.
- Existing temporary environment: `pip check` PASS. No dependency installations or manifest edits.
- Repository-root `backend.app` imports PASS.
- Actual canonical data from [Heiron8's PR #13](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/pull/13), reviewed read-only at commit `f1159c11ff7411faac96e118b6a26a1c7cd60023`, passes `Vocabulary.from_document()` for all 32 cards. The remote JSON was evaluated in memory and was not copied into the production tree.
- `correction-http.json`: fresh Uvicorn verification app with real local Ollama passes positive/negative expansion and 404/405 envelope/status/Allow checks. This is online, synthetic-vocabulary checkpoint evidence, not production/AAC/offline acceptance.
- [Manual offline procedure](manual-offline-verification.md): seven PowerShell code blocks parsed successfully without execution. No automatic adapter disconnect is attempted. **Offline proof remains NOT VERIFIED.**

Run backend tests from `backend`: `$env:PYTHONDONTWRITEBYTECODE='1'; & "$env:TEMP/tanaw-issue4-venv/Scripts/python.exe" -B -m unittest discover -s tests -v`.
Run workspace tests from the repo root: `$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m unittest discover -s tests -p 'test_*.py'`.

### Proposed handoff to Heiron8, based on PR #13 (not sent)

1. Keep the canonical `shared/vocabulary.json` and `shared.vocabulary.load_vocabulary()` ownership. Construct the inference boundary with `Vocabulary.from_document(app.state.vocabulary)` after that shared load; do not use test fixtures. Consider centralizing the frozen identity/metadata guard in your shared validator under Issue #1, with the same regression cases, to prevent validator drift. Its current structural checks alone accept a shaped unknown replacement ID.
2. Use repository-root imports `backend.app.api.communication.create_router`, `backend.app.api.errors.install_error_handlers`, `backend.app.ai.ollama.OllamaRuntime`, and `backend.app.validation.vocabulary.Vocabulary`.
3. Replace the placeholder foundation health route with the reviewed communication router; merely appending another health route leaves the earlier `unknown` handler first. Register the router before the missing-API fallback/static mount, and manage one runtime/client in app lifespan with shutdown closure and one backend worker.
4. Register `install_error_handlers(app)` before serving the app and after any existing handler decorators, or delegate your handlers to the shared response helper while passing `exc.headers`. The current PR #13 HTTP exception handler drops `Allow`.
5. Fix your all-method `/api/{path:path}` fallback so unsupported methods on an existing route still produce **405 with Allow**, rather than being consumed as **404**. Handler installation alone cannot fix fallback route matching. Preserve unknown API/static separation. Confirm the integrated behavior with the new regressions before merging.
6. The handlers supplied here cover HTTP and request-validation exceptions. Any remaining app-wide unexpected-error policy/static serving is your assembly responsibility. No new undocumented internal-error code is introduced by this correction.

### Remaining owners and acceptance blockers

| Dependency | Owner | Remaining evidence/action |
| --- | --- | --- |
| Canonical vocabulary/shared validator | Heiron8 / Issue #1 | Review/integrate PR #13, load its actual document through the guarded boundary; resolve shared-validator drift |
| Production app/manifests/startup | Heiron8 / Issue #1 | Register router/lifespan, replace placeholder health, integrate locked setup and product checks |
| App-wide errors and API fallback | Heiron8 / Issue #1 | Register reviewed handlers, preserve headers/status, prevent catch-all from swallowing 405 |
| Approved frontend integration | RobinKielll / Issues #2–3 | Human design approval, endpoint/selection/revision/approval wiring and rendered QA |
| Baseline AAC/offline speech | RobinKielll + GabDeGuz / Issues #3 and #5 | Real integrated board/speech stays usable with Ollama stopped; complete speech/fallback evidence |
| Offline model/restart/memory proof | LadlopezGit, independently witnessed by GabDeGuz | Execute the manual procedure while genuinely disconnected; record real model/digest/latency/network evidence |
| Independent re-review | Heiron8 (contract/security), GabDeGuz (meaning/offline) | Read-only PASS or further corrections on this exact revised source; no self-approval |

Readiness: **READY for independent re-review of the correction checkpoint; NOT COMPLETE for Issue #4 acceptance or delivery.** Do not commit/push/merge/close until the requested review and acceptance gates are satisfied. Suggestions remain disabled.

## Test-import compatibility follow-up (October 10)

The user authorized a correction for the four `ModuleNotFoundError: app` failures in the repository-root command used by current main's verifier. Previous corrected-code PASS is user-reported; this new five-file test/support diff still requires its own scoped independent read-only review before commit under Issue #4's workflow.

### Minimal change and verification

`backend/tests/fixtures.py` now conditionally inserts its resolved parent backend directory into the current test process's module search path. `test_api.py`, `test_evaluation.py`, `test_validation.py` and `test_vocabulary.py` import that existing helper before importing `app`. This supports root discovery without an external PYTHONPATH, duplicate bootstrap code, a new helper/dependency or a production namespace/architecture change. Backend-directory discovery continues to work. Test assertions and test counts are unchanged.

After reproducing the four loader errors, verification returned:

- Repository root: `python -B -m unittest discover -s backend/tests -v` — **35 PASS, zero failures/errors/skips**, 5.240 seconds.
- From `backend`: `python -B -m unittest discover -s tests -v` — **35 PASS, zero failures/errors/skips**, 5.256 seconds.
- Workspace: `python -B -m unittest discover -s tests -p 'test_*.py'` — **139 run, 138 PASS, zero failures/errors, one optional demo-dependency skip**, 20.974 seconds.
- `pip check`, quick workspace checks and the configured structural verifier PASS. Commands used the existing temporary Python environment with bytecode writes disabled. Full current-main product/merged-base CI was not run in this older checkout.
- Seven production source files are byte-for-byte unchanged. Existing meaning/order/schema/negation/invalid-output/unavailable/busy/cancellation/404/405/five-second tests remain passing. No new model run or offline test is claimed for this import-only correction.

The exact diff and before/after evidence are in [import-compatibility-review.md](import-compatibility-review.md) and [import-compatibility-snapshot.json](import-compatibility-snapshot.json). Historical source snapshots and all saved offline/online result artifacts remain unchanged.

### Saved manual offline observations and approval boundaries

- `manual-offline-benchmark-20261010-012931.json`: 30/30 supported calls across 12 fixtures, p50 217.43 ms, p95 259.65 ms; runtime 0.40.2 and reviewed qwen3:1.7b Q4_K_M digest.
- `manual-offline-http-20261010-013144.json`: 6/6 PASS.
- `manual-offline-session-20261010-010929.txt` and `witnessed-offline-session-20261010-014621.txt`: physical Wi-Fi/Ethernet disconnected and correct positive/negative candidates retaining source IDs/revisions. The later transcript records free ports followed by successful inference, supporting the reported restart.
- The owner reports GabDeGuz was present. The saved artifacts do not themselves contain his explicit PASS/CHANGES REQUIRED approval. Startup/cloud-disable commands, native public-probe/nvidia-smi output, session-specific source identification and cold-load timing are not fully captured. Benchmark setup after earlier calls is not a cold-load measurement.

These observations support the numerical/meaning gates but do not establish full production integration or final offline acceptance. Raw reports and transcripts must not be relabeled or overwritten.

### Readiness and next action

The root-discovery verification blocker is resolved locally. The scoped Draft PR proposal is technically prepared, with **14 code/test files and 19 evidence/documentation files**. Its creation remains gated on independent review of this import-only correction and explicit approval to commit/push/create it. Keep Issue #4 open and use Related to #4 rather than a closing keyword.

Heiron8 reviews the import diff and owns current-main app/shared/CI integration. GabDeGuz supplies the explicit offline evidence decision. RobinKielll/GabDeGuz retain frontend and integrated AAC/speech responsibilities. No teammate-owned files, branch history, Git index or issue status are changed in this follow-up.

## Final scoped publication record (October 10)

Heiron8's authenticated Issue #4 comment explicitly records PASS for the latest five-file import correction and confirms its SHA-256 snapshot match. GitHub supplies the posting timestamp; the inline date/findings placeholders are not treated as extra evidence. The current 14 source files and four original offline artifacts match `import-compatibility-snapshot.json`. The historical snapshot is retained without rewriting its earlier PENDING status.

Final verification: repository-root backend **35 passed** and backend-directory **35 passed**, both with zero failures/errors/skips (5.491 seconds each). Workspace **139 run, 138 passed, zero failures/errors, one optional demo-dependency skip** (41.324 seconds). `pip check`, quick workspace checks and the configured structural verifier passed. Exact commands and the review link are in [import-compatibility-review.md](import-compatibility-review.md).

The authorized scope remains 14 Python code/test files plus 19 QA documentation/evidence files. Candidate scope/secret checks passed. Current `origin/main` is `d4d7e33e5e043d2cd8f44872fe27f8ee40f29dc4`; candidate paths do not overlap its files. No merge/rebase or production app integration is performed, and merged-base product CI remains pending.

The owner authorizes the two planned Conventional Commits, branch push and scoped Draft PR with Related to #4. This is checkpoint publication only: GabDeGuz's final offline decision and missing lifecycle/network/source/cold-load evidence, Heiron8's canonical vocabulary/app-wide errors/runtime assembly, approved frontend integration, baseline AAC/speech fallback, merged-base verification and final review remain required. Issue #4 stays open; suggestions remain disabled.
