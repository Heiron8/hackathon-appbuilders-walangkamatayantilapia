# Demo production

This isolated Node toolchain belongs to [Demo Video Producer](../agents/demo-video-producer/CHARTER.md) and [demo-video](../skills/demo-video/SKILL.md). No product dependencies or workspace Core scripts are changed. All generated sample HTML, recordings, audio, bundles, MP4s and evidence go under ignored `demo/output/` by default. Do not add real private data to tracked storyboards or commit generated media.

## Setup and rehearsal (PowerShell, from repository root)

```powershell
npm.cmd --prefix demo ci --no-fund
# If the expected browser is absent, install the recording prerequisites once:
$env:PLAYWRIGHT_SKIP_BROWSER_GC = '1'
npm.cmd --prefix demo exec -- playwright install chromium ffmpeg
npm.cmd --prefix demo run doctor
npm.cmd --prefix demo run rehearsal -- --renderer remotion --tts auto
```

The rehearsal serves a disposable checklist on loopback and a random port, captures add/complete/empty-input behavior with runtime assertions, creates local speech if available, renders a 29-second MP4 and shuts down the server. It is a generic tool rehearsal, not a challenge solution. Each run prints its MP4 and evidence paths and preserves failures in a new output folder.

Start rehearsal invocations separately; the existing millisecond-based run folder names can collide if two processes start at the same instant. Existing directories are refused rather than overwritten. Run a narrated rehearsal, then the fallback command for its own output.

The driver prefers Playwright's expected Chromium and, on Windows if it is missing, tries installed Chrome then Edge in their standard locations. To select another compatible Chromium/Chrome, set `$env:DEMO_BROWSER` to its absolute executable path (for example `C:\Program Files\Google\Chrome\Application\chrome.exe`). You still need `npm.cmd --prefix demo exec -- playwright install ffmpeg` for Playwright's small recording encoder. Keep `PLAYWRIGHT_SKIP_BROWSER_GC=1` during installation to preserve other tools' cached browsers. `doctor` checks executable presence, FFmpeg/FFprobe versions and installed voices; the rehearsal proves actual execution. An arbitrary Chromium override still needs this execution check. No system PATH changes are needed. Optional `DEMO_FFMPEG` / `DEMO_FFPROBE` override the isolated package binaries.

Dependencies are pinned in package.json/package-lock.json. Node 22+, npm and Python for workspace checks are prerequisites. No global Node package or paid service is required. Remotion's [license](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) permits free use by individuals and small teams; check eligibility if reusing this outside that setting. FFmpeg packages bundle locally executed binaries; Playwright can download its browser/encoder during setup. After dependencies/browser are present, local rehearsal/rendering needs no hosted service.

## Product storyboard

Prepare a task-owned JSON file using the actual project evidence. Do not reuse rehearsal claims. This example describes schema only; replace all values with verified product details. Capture scene duration must accommodate the actions and narration. Total final duration is currently 60-120 seconds; if known event rules differ, make an explicit task-scoped change to that validation and tests before rendering.

```json
{
  "mode": "final",
  "title": "Product name",
  "baseURL": "http://127.0.0.1:3000",
  "build": {
    "id": "integrated commit or immutable deployment build",
    "integrated": true,
    "verification": ["dated product check result for this build"],
    "review": ["independent integration review reference"]
  },
  "privacyReviewed": true,
  "scenes": [{
    "id": "primary-flow",
    "kind": "capture",
    "duration": 20,
    "ready": "h1",
    "actions": [
      {"type": "fill", "selector": "#input", "value": "sanitized demo input"},
      {"type": "click", "selector": "#submit"},
      {"type": "assertText", "selector": "#result", "value": "verified result text"}
    ],
    "caption": "A concise supported claim.",
    "narration": "A concise spoken explanation of this scene.",
    "status": "VERIFIED",
    "evidence": ["acceptance criterion and dated runtime evidence for this build"]
  }]
}
```

Add scenes to meet the total duration; this one-scene schema example deliberately does not satisfy the final duration gate. Each scene needs a unique lowercase filename-safe ID, integer duration 3-30 seconds, caption up to 140 characters, narration (empty allowed), status and evidence. `kind: title` creates a title/closing card. `kind: capture` needs ready selector, actions and optional URL override. Actions support CSS selectors with fill, click, press, check, assertVisible and assertText. Every capture needs a result assertion. Each capture begins in a fresh context; replay all prerequisite steps, including sanitized test-account sign-in if authorized. No storage-state secrets are persisted or loaded. Recordings contain navigation and real clicks, not screenshots pretending to be interactions.

`DEMONSTRABLE WITH WARNING` requires a visible `warning` up to 100 characters. `NOT SAFE TO DEMONSTRATE` is rejected. Optional `highlight: {"x":0.1,"y":0.2,"width":0.3,"height":0.1}` uses normalized footage coordinates; it adds an outline without modifying the product. Manual scenes use `kind: manual` and `media` pointing to real local footage relative to the storyboard. Supply at least the full scene duration; conversion preserves aspect ratio with padding. Optional `audio` accepts local narration relative to the storyboard; other local TTS engines such as Piper can produce this file without changing the pipeline.

```powershell
node demo/cli.mjs produce --storyboard demo/output/product-storyboard.json --tts auto --renderer auto
node demo/cli.mjs validate --storyboard demo/output/product-storyboard.json --video demo/output/<run>/demo.mp4
npm.cmd --prefix demo test
```

Use a new `--out <directory>` for every run; existing directories are refused to protect prior evidence. Keep custom output under demo/output so it is ignored. Inspect the complete running product first; schema flags/references are declarations, not automated proof of integrated-build identity or privacy. Freeze or identify an immutable running build for capture and confirm it matches the recorded build ID.

## Narration and rendering fallbacks

- `--tts auto`: per-scene supplied audio first, then installed English Windows SAPI voice, otherwise captions with an explicit warning. SAPI is local conventional synthetic speech, not a neural AI voice. No neural voice/model is installed by this toolchain.
- `--tts windows`: fail if local English SAPI synthesis is unavailable. `--tts manual`: require per-scene audio for nonempty narration. `--tts none`: captions-only, deliberately ignores audio.
- Audio starts at its scene boundary or optional `narrationStart` offset. The pipeline probes audio and rejects the offset plus narration exceeding scene duration minus 0.3 seconds. Rewrite text or lengthen the scene; it never silently truncates speech. Partial audio availability is recorded per scene; review it before submission.
- `--renderer remotion`: strict Remotion render. `--renderer auto`: try Remotion, preserve its error if it fails, then use FFmpeg. `--renderer ffmpeg`: explicitly exercise the fallback with the same capture/audio. The fallback includes configured titles, footage, timed burned-in captions, warnings and offset narration; camera movement, highlight outlines and fades are omitted. Captions-only fallback may include a silent AAC track.
- Non-browser product: record the verified app with an installed screen recorder, crop private desktop areas, save a real recording and use manual scenes. A human can record WAV narration with an installed audio recorder. Keep build ID and original footage; no fake product results. This manual recorder path is documented, not automated.

The default renderer uses public bundle assets locally. Do not serve these output directories publicly. Render errors and failed recordings are diagnostic evidence; inspect/sanitize before sharing.

## Optional editorial controls

Existing storyboards still work. Add only the controls needed by the actual verified story:

- Title scenes: `card: "intro"` introduces the problem/product with left-aligned text; `card: "outro"` closes on the result with centered text. `heading` and `eyebrow` override displayed card text (1-80 characters each); heading otherwise uses the board title. Remotion uses a short upward reveal, fading text and a restrained accent-line reveal. These words are product claims too and need the scene's evidence.
- Capture pacing: `leadIn: 0.5` pauses after the ready selector, before actions. Each action can use `pauseAfter: 0.8` to show an input or verified result. Pauses are explicitly for presentation, not readiness; selector/action/result checks still control readiness. Keep total action/pause time within the scene; the existing duration guard rejects overruns.
- Camera: `camera: {"scale":1.05,"x":0.3,"y":0.6,"start":3,"end":5}` eases from the original framing to the normalized focal point during that interval, then holds. Scale is bounded to 1-1.08; aspect ratio and the underlying footage are unchanged. This small zoom crops edges: choose an interior target and inspect all important UI for clipping. Put movement after important input/actions, and reuse an optional highlight to identify a verified result. Highlights track the footage's transform.
- Narration: `narrationStart: 0.4` gives a title reveal or an action a short lead-in. Remotion and FFmpeg use the same offset; fit checks include it. Offset defaults to zero and cannot exceed three seconds.
- Captions: optional `captions: [{"text":"Complete it.","start":2.4,"end":3.5},{"text":"The count updates.","start":3.5,"end":6.2}]` shows one short phrase at a time. Times are seconds relative to the scene. Cues must be ordered, non-overlapping, at least 0.6 seconds long, within the scene and at most 100 characters each. Remotion gently fades each phrase; FFmpeg honors its timing with static text. Without cues, the existing caption appears from narration start through the scene's final reading hold.

Caption timings are editor-authored, not automatic word alignment. Match them to the actual local voice/action timing and inspect full playback. The pipeline never time-stretches, truncates or regenerates product behavior to fit an animation. Footage stays visible during cuts; text fades avoid obscuring actions. In captions-only mode the same cue timing remains, without a voice. evidence.json records card text, camera, cue timing and narration offset for review.

## Validation and existing submission support

evidence.json records the identified build, capture assertions, time, provider, narration duration/alignment, actual renderer, full decode, dimensions/codec/duration and extracted review-frame paths. Media is H.264/yuv420p 1280x720 at 30 fps, with AAC when narration is present. Raw WebMs and scene PNGs support footage review. Trim offsets use capture timestamps; inspect scene beginnings/ends and audio during playback. Small recording-end gaps (at most one second) hold the last real frame; no new product action/result is created.

Full decoding is not playback review. Play the whole MP4 and inspect readability, pronunciation/synchronization, private information, product truth and actual event rules. Ask an independent teammate to review and record result/build/time. Hand these artifacts and remaining blockers to the existing [Submission Readiness](../docs/qa/submission-readiness.md) Demo rows; use [technical-defense](../skills/technical-defense/SKILL.md) for requested readiness reporting. No second checklist or submission state is created. Rehearsal evidence cannot satisfy final product or submission checks. Artifact creation never uploads, publishes or submits.

## Member 4 and a fresh session

Members 1-3 develop, independently review, integrate and verify the approved product. Member 4 owns the normal shared demo task, prepares this toolchain and a generic rehearsal early, then drafts product story/narration only from available evidence. Final capture waits for the verified integrated build and safe test data. Report defects with selectors/actions, expected/actual behavior and build ID to the developer owner; recapture after a verified integration fix. Obtain another teammate's full-playback review before submission readiness can be VERIFIED.

Activation prompt:

> Run Project Sync. Read agents/CHARTER_STANDARD.md, agents/demo-video-producer/CHARTER.md and skills/demo-video/SKILL.md. Act as Demo Video Producer for Member 4 under my owned demo task. Inspect verified features and integrated-build evidence, then prepare storyboard, real capture, local narration and a validated MP4 using demo/. Keep edits demo-owned, report product defects, and supply evidence/blockers to existing Submission Readiness. If the product is not integrated and verified yet, prepare infrastructure and generic rehearsal only. Do not upload or submit.

## Tested rehearsal, 2026-10-08

On the preparation branch, Node 22.18.0, npm 10.9.3 and Python 3.13.5 were available. Installed isolated dependencies: Playwright 1.64.0, Remotion 4.0.534, FFmpeg 6.1.1 and FFprobe 4.0.2. Package audit reported zero vulnerabilities at check time. Installed Chrome 154.0.8037.98 ran the browser capture and render. The small Playwright recording encoder was installed; its installer removed an older cached Chromium revision before the cache-preservation setting was added to these setup instructions.

- Strict Remotion + Windows SAPI rehearsal: [MP4](output/rehearsal-1791458935339/render/demo.mp4), [evidence](output/rehearsal-1791458935339/render/evidence.json). Runtime add/complete/empty-input assertions passed. Microsoft David Desktop generated five English WAV files; all fitted their scenes. H.264 1280x720 with audio, 25.003 seconds, full decode PASS. Exported scene frames were visually inspected for UI/caption readability.
- Explicit FFmpeg + captions-only fallback: [MP4](output/rehearsal-1791458979755/render/demo.mp4), [evidence](output/rehearsal-1791458979755/render/evidence.json). Same actual capture assertions passed. H.264 1280x720, 25.022 seconds, full decode PASS; its AAC track is silent.
- Both MP4s played to the end in headless Chrome at 4x, muted, without a media error; each run includes playback-evidence.json. This proves browser playback, not human listening or independent full-playback review. Narration timing has scene alignment/fit checks; pronunciation and subjective synchronization remain human review work.
- Seven Node behavioral checks and four role/skill checks passed. The complete 87-test workspace suite and canonical `python scripts/verify_workspace.py` passed, along with skill validation, changed/untracked source secret scanning and `git diff --check`. Live GitHub integration remains NOT TESTED for this unconfigured template.

These links point to ignored artifacts on the rehearsal machine and will not exist in a fresh clone; rerun the rehearsal there. Early failures were a missing recording encoder, capture-tail timing and recursive bundling. The first two were resolved by prerequisite/timing changes; the bundler now receives a separate leaf folder containing only media. Failed-run artifacts remain ignored. Neural local AI TTS is NOT YET AVAILABLE; conventional local SAPI, manual audio and captions-only are implemented. No challenge product, final integrated-build capture, event-rule confirmation or independent submission review is claimed.

## Editorial rehearsal, 2026-10-08

One focused presentation pass over checkpoint e22fae2 added distinct configurable intro/outro cards, restrained reveals, optional 5-6% result zooms in the sample, a result highlight, explicit input/result holds, timed phrase captions and narration offsets. No product or dependency changes were needed; the generic sample HTML has the same SHA-256 as the checkpoint's rehearsal.

- Narrated Remotion: [new MP4](output/rehearsal-1791466367054/render/demo.mp4), [evidence](output/rehearsal-1791466367054/render/evidence.json), 29.013 seconds, H.264 1280x720 with audio; full FFmpeg decode PASS.
- Captions-only FFmpeg fallback: [new MP4](output/rehearsal-1791466377141/render/demo.mp4), [evidence](output/rehearsal-1791466377141/render/evidence.json), 29.022 seconds; full decode PASS. It intentionally retains static cards/footage and timed text instead of camera movement or animation.
- Both final videos reached the end in headless Chrome at 4x, muted, with no playback error. Exported intro/input/result/outro frames were inspected: typed input remains visible before submission, the highlight surrounds the real completion count, and UI/captions are readable. A misplaced highlight and a short input hold were corrected during this pass.
- Decoded narrated speech onsets matched source WAVs plus configured scene offsets within 22 milliseconds for all five scenes; audio-sync-evidence.json records the comparison. Caption phrases are manually timed, not word-aligned automatically. Human listening/independent playback review of this new edit remains pending.
- Ten demo checks now include bounded camera timing, legacy storyboard compatibility, caption overlap rejection, offset-aware narration fit and an actual FFmpeg audio-delay render check. Workspace tests and canonical verification remain separate from product/submission evidence.

Concurrent rehearsal launches exposed the existing timestamp-folder collision; the final runs used separate launches. The original checkpoint and older ignored outputs remain intact. The links above are local ignored artifacts, not committed media or submission approval.
