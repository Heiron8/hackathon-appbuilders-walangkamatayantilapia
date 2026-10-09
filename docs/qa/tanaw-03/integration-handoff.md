# Issue #4: integration and backup handoff

Implementation checkpoint: PR #16 at `7244f1638938889717a33bbd1f6f8b767bf55ce6`; technical PASS is reported by the owner, with review handled centrally. That checkpoint's GitHub Verify passed, including 51 backend tests. The owner reports the Lead reviewed this readiness package and authorized publishing these five QA/handoff files after inspection. This records publication authorization, not a GitHub merge approval. **Ready for Lead integration; integrated offline acceptance remains open on Issue #4.** No implementation changes accompany this handoff.

## Heiron8: five assembly steps

1. Retain the canonical `shared.vocabulary.load_vocabulary()` load. Construct `Vocabulary.from_document(app.state.vocabulary)` from `backend.app.validation.vocabulary`; missing/malformed data must fail, with no test-fixture fallback.
2. Create one `OllamaRuntime()` from `backend.app.ai.ollama` per app; include `create_router(vocabulary, runtime)` from `backend.app.api.communication` **before** the API fallback/static mount. Close with `await runtime.aclose()` in lifespan shutdown using `try/finally`. Preserve existing lifecycle work and run one Uvicorn worker.
3. **Replace** the placeholder health route. Appending another leaves the earlier route first. Reviewed health returns HTTP 200, AI ready/unavailable and suggestions disabled. Installed-model readiness does not prove warm inference.
4. Register `backend.app.api.errors.install_error_handlers(app)` after existing handlers, or preserve status/headers when delegating. Fix the all-method catch-all that can swallow 405: `GET /api/expand` must be 405 with Allow POST; `POST /api/health` must be 405 with Allow GET; unknown API paths must return JSON 404 rather than the SPA. Retain host/origin restrictions.
5. Wire frontend candidate/unsupported/error handling with request ID, revision and source order. Verify baseline AAC/speech with Ollama stopped. Router wiring alone is not integrated offline acceptance.

Production `main.py`, lifecycle, health and app-wide routing/error edits remain Lead-owned.

## Test commands

From repository root, using the existing backup environment:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$pythonExe = Join-Path $env:TEMP 'tanaw-issue4-venv/Scripts/python.exe'
& $pythonExe -B -m unittest discover -s backend/tests -v
Push-Location -LiteralPath 'backend'
try { & $pythonExe -B -m unittest discover -s tests -v } finally { Pop-Location }
# On the merged foundation checkout, using its pinned environment:
& $pythonExe -B scripts/verify.py --ci
```

With the target server at 127.0.0.1:8000, run `python -B -m tests.smoke_checkpoint --expect-ai ready --output <new-report.json>` from `backend`. It checks six HTTP cases using fixture requests; record the actual target app/build separately, because the runner does not establish production assembly or offline network condition. Also verify the 404/405/Allow cases above.

Required production integration checks also cover client shutdown, a single active inference, unavailable/busy/timeout/invalid-output envelopes, malformed/unknown selections and version mismatch, stale revision protection, and working board/speech with AI stopped. Existing backend unit tests cover the module boundaries; repeat applicable behavior against the assembled app rather than treating unit PASS as production acceptance.

Final local publication checks: repository-root backend **35 passed**, backend-directory **35 passed** (5.254 seconds each; zero failures/errors/skips); workspace **139 run, 138 passed, one optional demo-dependency skip** (20.096 seconds; zero failures/errors). Dependency check, quick workspace gates, report consistency, secret/whitespace/link checks and `scripts/verify.py --ci` passed. The latter is structural only in this older checkout; the configured merged-foundation GitHub CI is a separate check. No additional benchmark or offline test was run for publication.

## Operational backup: LADLAPTOP

At the recorded approximately 04:30 PHT check, Ollama **0.40.2** and the verification backend were running on loopback ports 11434/8000. Model **qwen3:1.7b Q4_K_M**, digest `8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`. The model was loaded; a setup-only keep_alive=-1 request reported expiry in year 2319. Later app calls use the existing 10-minute keep-alive and may change that residency; warm again before a demo after extended idle. These dated observations do not guarantee future process availability or model residency.

Fresh **connected-session** evidence:

- [backup-warmup-20261010-042800.json](backup-warmup-20261010-042800.json): **30/30** calls, 12 fixtures, p95 **267.02 ms**. Setup **2994.41 ms** started with the model unloaded; existing runtime/OS caches mean this is not offline/process-cold timing.
- [backup-http-20261010-042943.json](backup-http-20261010-042943.json): **6/6 HTTP PASS**.
- [backup-ready-20261010-042945.json](backup-ready-20261010-042945.json): actual positive/negative expansion, preserved order/revisions, and 404/405/Allow PASS. This is the synthetic-vocabulary verification app, not the production UI.
- [backup-environment-20261010-043019.json](backup-environment-20261010-043019.json): process creation at 02:10:32 (Ollama) and 02:12:35 (backend) PHT corroborates the saved 02:07 free ports followed by 02:14 disconnected inference. Observed binds are loopback; Wi-Fi was Up during this backup check. Personal profile path prefixes are redacted explicitly; process arguments/timestamps are preserved. Physical witnessing still requires independent confirmation.

## Outstanding evidence

GabDeGuz's [independent decision](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/pull/16#issuecomment-6088189276), historical/current cloud-disabled startup capture, offline cold-start timing and session-specific source/probe/GPU capture remain pending or **UNVERIFIED**. Original source hashes and offline artifacts are preserved.

For missing startup capture, a human may use Ctrl+C in this checkpoint's original Ollama terminal, then follow [the approved manual startup procedure](manual-offline-verification.md#restart-local-services-while-disconnected): OLLAMA_NO_CLOUD=1, OLLAMA_HOST=127.0.0.1:11434, OLLAMA_NUM_PARALLEL=1, OLLAMA_MAX_LOADED_MODELS=1, OLLAMA_DEBUG=0. Capture actual cloud-disabled startup output. For offline/cold evidence, restart while physically disconnected and time the first complete inference **before** warming/examples, distinguishing runtime/model restart from an OS/fresh-install cold start.

Automatic approval review rejected a controlled runtime-restart command as **blocked by policy**; it did not execute. Existing services were left operational. No merge, new feature, final offline PASS or product-completion claim is made. Lead assembly/frontend wiring and integrated AAC/speech QA are the remaining integration dependencies.

## Merge decision versus integrated/device acceptance

No new implementation defect is identified by this QA package. The Lead centrally owns the documented standalone-checkpoint merge decision and required review/CI gates. Deferral of the unverified offline items above must be explicit in that decision; publishing this package does not itself approve merge or waive Issue #4 criteria. Production router/lifecycle/health/error integration, frontend revision/approval behavior, disconnected restart/configuration/identity evidence, cold/warm timing and baseline AAC/speech failure recovery remain integrated/device acceptance work. Keep Issue #4 open.
