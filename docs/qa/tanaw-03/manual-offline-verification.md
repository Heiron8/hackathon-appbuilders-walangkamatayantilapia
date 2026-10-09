# Manual offline verification for TANAW-03 / Issue #4

Status: **NOT TESTED**. These instructions prepare a witnessed test; documentation or a connected run is not an offline PASS. GabDeGuz witnesses meaning, network condition and restart, then records independent evidence. No command here disconnects an adapter, installs dependencies or pulls a model.

## Before disconnecting

Use the identified demonstration laptop. Confirm the installed runtime/model and existing Python environment while internet is still available. Do not change a teammate's manifests or install a different model during the offline test.

Open PowerShell at the repository root:

```powershell
Set-Location -LiteralPath 'C:\Users\Jeral\Workspace Projects\App builders hackathon\hackathon-appbuilders-walangkamatayantilapia'
$repoRoot = (Get-Location).Path
$pythonExe = Join-Path $env:TEMP 'tanaw-issue4-venv/Scripts/python.exe'
$ollamaExe = Join-Path $env:LOCALAPPDATA 'Tanaw/ollama/v0.40.2/ollama.exe'
if (-not (Test-Path -LiteralPath $pythonExe) -or -not (Test-Path -LiteralPath $ollamaExe)) { throw 'Prepare the documented local environment before disconnecting.' }
$env:PYTHONDONTWRITEBYTECODE = '1'
& $pythonExe -B -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed.' }
```

Stop the previous verification services to prove a process restart. Prefer Ctrl+C in the terminals where you started them. If they were started in the background, the following checks restrict shutdown to this checkpoint's processes. Do not stop unrelated servers or another developer's app.

```powershell
foreach ($port in @(8000, 11434)) {
    $listeners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
    foreach ($processId in @($listeners.OwningProcess | Select-Object -Unique)) {
        $ownedProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$processId"
        $expected = if ($port -eq 8000) { 'uvicorn tests\.checkpoint_app:app' } else { 'Tanaw.*v0\.40\.2.*ollama\.exe.*serve' }
        if (-not $ownedProcess -or $ownedProcess.CommandLine -notmatch $expected) { throw "Port $port belongs to a different process; stop and coordinate with its owner." }
        if ($port -eq 11434) {
            & $ollamaExe stop qwen3:1.7b
            if ($LASTEXITCODE -ne 0) { throw 'Could not unload the model safely.' }
        }
        Stop-Process -Id $processId
    }
}
```

## Disconnect manually and check the condition

The human now turns **Wi-Fi off in Windows Settings → Network & internet** and unplugs Ethernet. Disconnect tethering or any other physical internet connection. Selecting a chat confirmation does not operate Windows network settings.

Run this guard in the repository-root PowerShell. It reads adapter state and attempts one bounded public TCP connection; it does not change networking.

```powershell
function Assert-Offline {
    $physicalAdapters = @(Get-NetAdapter -Physical)
    $physicalAdapters | Select-Object Name,Status
    if (@($physicalAdapters | Where-Object Status -eq 'Up').Count -ne 0) { throw 'A physical network adapter is still connected.' }
    @'
import socket
try:
    connection = socket.create_connection(('1.1.1.1', 443), timeout=3)
except OSError as exc:
    print('Public TCP probe failed:', type(exc).__name__)
else:
    connection.close()
    raise SystemExit('Internet access is still available; do not run or claim an offline test.')
'@ | & $pythonExe -B -
    if ($LASTEXITCODE -ne 0) { throw 'Offline network guard failed.' }
}
Get-Date -Format o
Assert-Offline
```

GabDeGuz records the physical adapter results, time and failed TCP probe. Failure of one public connection alone is insufficient; the physical interfaces must also be disconnected. Keep networking off throughout the remaining steps. Abort if it reconnects.

## Restart local services while disconnected

Terminal A, opened at the repository root:

```powershell
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_DEBUG = '0'
& "$env:LOCALAPPDATA/Tanaw/ollama/v0.40.2/ollama.exe" serve
```

Keep this terminal open; record that startup reports cloud disabled and loopback binding. No `pull`, download, retry loop, remote model or remote fallback is allowed.

Terminal B, opened at the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
Push-Location -LiteralPath 'backend'
& "$env:TEMP/tanaw-issue4-venv/Scripts/python.exe" -B -m uvicorn tests.checkpoint_app:app --host 127.0.0.1 --port 8000 --no-access-log
# After Ctrl+C, return with: Pop-Location
```

This is the **verification-only application with synthetic vocabulary**, not the integrated frontend/AAC build. After Heiron8's reviewed integration, repeat the same checks against the production app using his startup instructions; record that application's exact build/hash. Do not replace a missing canonical file with test fixtures.

## Verify model identity, meaning, performance and HTTP behavior

Back in the first PowerShell terminal (which retains `$repoRoot`, `$pythonExe` and `Assert-Offline`):

```powershell
Assert-Offline
$version = Invoke-RestMethod 'http://127.0.0.1:11434/api/version'
if ($version.version -ne '0.40.2') { throw 'Runtime version differs from the reviewed checkpoint.' }
$model = (Invoke-RestMethod 'http://127.0.0.1:11434/api/tags').models | Where-Object name -eq 'qwen3:1.7b'
if (@($model).Count -ne 1 -or $model.digest -ne '8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7') { throw 'The downloaded model is missing or its digest changed. Do not pull it while offline.' }
$version
$model | Select-Object name,digest,details
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$benchmarkReport = Join-Path $repoRoot "docs/qa/tanaw-03/manual-offline-benchmark-$stamp.json"
$httpReport = Join-Path $repoRoot "docs/qa/tanaw-03/manual-offline-http-$stamp.json"
Push-Location -LiteralPath 'backend'
try {
    & $pythonExe -B -m app.ai.evaluate --output $benchmarkReport
    if ($LASTEXITCODE -ne 0) { throw 'Model quality/latency benchmark failed. Preserve the report.' }
    & $pythonExe -B -m tests.smoke_checkpoint --expect-ai ready --output $httpReport
    if ($LASTEXITCODE -ne 0) { throw 'HTTP checkpoint failed. Preserve available evidence.' }
} finally { Pop-Location }
Assert-Offline
```

The benchmark performs explicit complete-fixture setup warm-up, followed by at least 30 actual bounded model calls over 12 supported fixtures. Setup can take up to 120 seconds; product inference retains its five-second deadline. Reports preserve existing files and never contain generated message text. They say networking is **not checked by the command**: GabDeGuz's separately observed adapter/probe/restart evidence is required to establish offline operation.

Show the witnessed positive and negative examples explicitly:

```powershell
$positive = '{"request_id":"11111111-1111-4111-8111-111111111111","revision":3,"vocabulary_version":"tanaw-v1","locale":"en","selected_card_ids":["want","eat","apple"]}'
$negative = '{"request_id":"11111111-1111-4111-8111-111111111111","revision":4,"vocabulary_version":"tanaw-v1","locale":"en","selected_card_ids":["not","want","eat","apple"]}'
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/expand' -ContentType 'application/json' -Body $positive
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/expand' -ContentType 'application/json' -Body $negative
Get-Process -Name ollama,llama-server | Select-Object ProcessName,Id,WorkingSet64,PrivateMemorySize64
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader
Get-Date -Format o
Assert-Offline
```

Expected positive text: `I want to eat an apple.` or `I would like to eat an apple.` Expected negative text: `I do not want to eat an apple.` Source order/revision must be preserved; an invented feeling/quantity/preference or dropped negation fails the test. The HTTP smoke also checks unsupported Water, unknown IDs and vocabulary mismatch. Collect memory observations without confusing process working set, committed RAM, model allocation and total GPU use.

## Evidence and acceptance for GabDeGuz

Record laptop identity, reviewer identity, time/timezone, tested source hashes/build, runtime version/model digest/quantization, network checks before and after, actual service restarts while disconnected, observed positive/negative meaning, both report paths, setup duration, 30-call outcomes and p50/p95, RAM/VRAM, and any failures. Preserve failed reports. The model gate requires at least 90% supported success and warm p95 at most 3 seconds, with no accepted unsupported additions in validation fixtures.

Run the backend tests separately to check invalid-output/negation/order, busy/unavailable and the real five-second boundary with injected delay. Do not present an injected delay as a naturally timed-out real model. On the integrated product, additionally stop Ollama while still disconnected and verify the board, selection and offline speech remain usable; then perform production restart/browser reload. **Those baseline AAC/fresh-build checks are still blocked on integration and are not proven by this verification app.**

GabDeGuz returns `PASS` or `CHANGES REQUIRED` with evidence under the independent review contract. A successful checkpoint does not close Issue #4. After all observations, the human may reconnect Wi-Fi/Ethernet manually. These instructions never do so automatically.
