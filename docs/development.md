# Tanaw local foundation — Issue #1

Work in the existing repository on one task branch per human. This checkpoint
adds startup and integration boundaries; it has no communication UI, speech,
Ollama adapter or AI routes. Human Figma approval still gates the AAC UI.

## Locked setup

Use Node 22.18.0 (the tested laptop/CI version) and Python 3.12 or 3.13.
The laptop runs Python 3.13.5; CI selects 3.12. Setup needs internet once.
From the repository root in PowerShell:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
Set-Location frontend
npm.cmd ci
Set-Location ..
```

On Linux/macOS use `backend/.venv/bin/python` and `npm` in place of the Windows
executables. All direct versions are exact in `frontend/package.json` and
`backend/requirements.in`; npm's lock and the fully pinned Python lock include
transitive dependencies. Manifest/lock changes belong to Heiron8 and need review.
No Ollama installation or model download is required for this checkpoint.

## Development

Run backend from the repository root, so both Python packages and shared data
resolve without machine-specific paths:

```powershell
backend/.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

In a second terminal:

```powershell
Set-Location frontend
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. Vite proxies `/api` to loopback port 8000 and permits
only the frontend and shared directories for file access. Keep both servers
bound to loopback; LAN/public exposure is outside the approved architecture.
No CORS is needed because the browser uses one origin. Backend mutation requests
reject foreign browser origins. Do not enable request/message access logging.

## Final local serving and verification

```powershell
Set-Location frontend
npm.cmd run build
Set-Location ..
backend/.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Open `http://127.0.0.1:8000`. Restart backend after building so the static mount
is assembled. Without a build it still starts for Vite development. No service
worker, database, account, remote asset or cloud inference is added.

Stop the development servers, then run the canonical command:

```powershell
python scripts/verify.py
```

This retains all existing harness tests/secret checks, runs frontend contracts
and build, backend contracts/app tests and dependency compatibility, and launches
real loopback servers to verify health, proxy, final assets/reload, filesystem
access scope, and frontend shell/vocabulary after backend shutdown. Ports
8000/5173 must be free; verification never stops someone else's server.
`python scripts/verify.py --ci` runs the same configured checks in CI.

HTTP shell/asset checks are not rendered AAC or offline speech evidence. Physical
internet-disconnected cold restart/reload, installed local voice, recordings and
fresh-device setup remain GabDeGuz's integrated QA gates. UI behavior and actual
speech during backend failure cannot pass until their implementations land.

## Owner handoff

- **RobinKielll:** `frontend/src/App.jsx` is the neutral replacement point after
  Figma approval. Import `vocabulary`, `cardsById`, `contracts` from
  `frontend/src/vocabulary.js`. Data is bundled at build time; baseline must not
  await health/API requests. UI/state/styles remain Robin's lane.
- **LadlopezGit:** `shared.vocabulary.load_vocabulary()` validates the canonical
  file; assembly exposes it as `app.state.vocabulary` and shared constants as
  `app.state.contracts`. Own new route/validation/adapter modules under
  `backend/app/`; provide an `APIRouter` handoff. Heiron8 includes the reviewed
  router **before** the `/api/{path:path}` fallback in `create_app()` and hands
  health behavior to the backend lane. Current health does not probe Ollama:
  HTTP 200, `tanaw-v1`, AI `unknown`, suggestions false. `/api/expand` and
  `/api/suggest` are deliberately absent (404 envelope), not simulated AI.
- **GabDeGuz:** implement the three speech functions and capability/playback/error
  state defined in `shared/contracts.d.ts`; no speech implementation exists yet.
  Approved paths resolve from `frontend/public/`: `symbols/<id>.svg` and
  `audio/en/<id>.wav`. References are contracts, not a claim that licensed assets
  are supplied. Add licensed symbols/recordings in your own task.

`docs/architecture/contracts.md` remains the approved behavioral authority.
`shared/contracts.json` exports the frozen version/limits/disabled flag;
`shared/contracts.d.ts` describes request/response/speech shapes for integration,
not runtime validation. UUID/revision/locale/body/version/selection enforcement,
meaning validation, inference timeouts and readiness probing remain the backend
owner's work. A type declaration does not establish those runtime guarantees.
Vocabulary labels/categories/order are checked against the approved table by
tests; both consumers also reject malformed vocabulary, extra fields, duplicate
IDs, reordered positions and noncanonical asset paths. Repeated selections and
selection-order speech remain the UI/speech lanes' responsibilities.

No teammate message was sent or remote issue state changed. LadlopezGit reviews
the shared/backend foundation; GabDeGuz reviews setup/verification before commit,
push or PR creation. Coordinate router/speech handoffs through that review.
