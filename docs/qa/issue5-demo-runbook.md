# Issue #5: demo and disclosure handoff

Prepared October 10, 2026, UTC+08. Owner: GabDeGuz. Status: preparation only;
no integrated Tanaw video, rehearsal PASS or submission approval is claimed.
Use the existing [demo pipeline](../../demo/README.md) and
[submission readiness checklist](submission-readiness.md); no new pipeline.

Tool preparation on this laptop: existing pinned `npm.cmd --prefix demo ci
--no-fund` completed (198 packages, zero reported vulnerabilities at install time).
`node demo/cli.mjs doctor` passed executable/version/import checks: installed
Chrome, FFmpeg 6.1.1, FFprobe 4.0.2, Node 24.18.0, Remotion and Playwright. It
printed no SAPI voices in this invocation; synthetic narration availability is
not confirmed. Manual narration or captions remain available paths. No browser
capture/rehearsal was executed and these checks do not establish a product video.
All ten existing `npm.cmd --prefix demo test` checks passed, including actual
audio probing and FFmpeg narration-delay rendering. These are tool checks, not
Tanaw footage or human listening evidence. Workspace verification also passed
after setup; no tracked dependency manifest or lockfile was changed.

## Build and capture gate

The [final acceptance handoff](issue5-final-acceptance.md) identifies the speech
checkpoint and separate frontend PR #17. A combined build is not selected yet.
Final recording starts only after that exact build passes verification, independent
review and the real disconnected direct-AAC test. Keep the existing repository,
identify the running commit/profile/URL and record sanitized words only. Do not
capture private accounts, notifications, tokens or identifiable child data.

The Demo Video skill requires integrated-build verification and review references
before final capture. Do not mark a draft `integrated: true`, `VERIFIED` or
`privacyReviewed: true` to bypass the pipeline. Generic rehearsal/sample footage
does not prove the Tanaw product. A manual real recording is supported when an
authorized browser capture is unavailable; retain original footage and failures.

## Proposed 75-second story

Presenter: **Ahron**, as supplied by the user. The user reports no required video
duration. Use 75 seconds as a proposed length within the existing pipeline;
confirm the official format and submission requirements before capture. Prepare
all four team laptops using the [device checklist](issue5-final-acceptance.md),
then select a presentation laptop after its actual integrated rehearsal passes.
These are planned actions and narration, not observed results.

| Time | Actual action after the gate passes | Planned narration / claim limit |
| --- | --- | --- |
| 0-10 s | Title and empty real board | "Tanaw lets a child build a message with pictures and choose when to speak." No clinical efficacy claim. |
| 10-30 s | Tap Want, Eat, Apple; show ordered selected pictures | "Each tap adds a word. The message stays in the order selected." No AI sentence claim. |
| 30-50 s | Open Review, explicitly Speak; show Stop and Replay | "Review the message, then press Speak. Stop and replay are separate choices." Use actual captured speech; narration must not impersonate app output. |
| 50-65 s | Repeat a card; demonstrate the verified model-off path | "Direct speech remains available with Ollama stopped." Show only after that exact build passes the physical test. |
| 65-75 s | Closing / limitation caption | "Local speech and bundled recordings require device checks. Conversation assistance is not enabled." Name the actually configured mode. |

If AI expansion later passes its separate gate, revise the story from that actual
build/evidence; never replace an unavailable response with simulated output. If
voice or clip playback fails, stop that scene, retain the error and use a qualified
human explanation. Silent footage cannot be presented as audible speech proof.

## Existing production steps

1. Complete the build/device/privacy gates and confirm event rules, demo laptop,
   technical-question owner and required submissions with the Lead. Ahron is the
   named presenter; no fixed duration is reported by the user.
2. Check isolated prerequisites with `node demo/cli.mjs doctor`. Use only the
   existing pinned demo lockfile/setup from `demo/README.md`. No product manifest
   changes, global packages or additional repository are required.
3. Save a product storyboard under ignored `demo/output/`, following the existing
   schema. Fill real integrated commit, verification/review references, privacy
   review and scene assertions. Do not execute final capture while those are absent.
4. Use a supported real manual recording or authorized capture. Narration can be
   human-recorded or captions-only; any synthetic narration needs its own source/
   rights record. Microsoft's live device voice check does not establish rights
   to distribute a new narration recording. The fallback card WAV rights are
   separately documented under GPL-3.0-or-later.
5. Compose and validate with the existing pipeline; use a new output directory
   each time. Decode the final MP4, verify streams/duration and inspect frames.
   A human must watch/listen to the complete video for readable text, accurate
   app audio, synchronization, truthful claims and privacy. Obtain independent
   playback review and attach `evidence.json`, storyboard and final MP4 location.
6. Rehearse the actual integrated laptop and confirm the final package against
   event requirements. Preparing a video does not authorize upload/submission.

## Required disclosure record

| Component | Known source / use | Disclosure or remaining confirmation |
| --- | --- | --- |
| Pre-existing workspace harness | Repo skills, governance, verification and demo tools | Disclose reused tooling; generic rehearsal is not Tanaw runtime evidence. |
| Coding/design assistance | Codex speech implementation, original SVG generation and independent Codex reviews | Human asset/device results remain separately attributed to Gab/actual witness. Do not imply reviewers were named humans. |
| Canonical vocabulary | `shared/vocabulary.json`, tanaw-v1, 32 stable IDs/order | Shared Issue #1 contract; no new/reordered words. |
| WAVs and original symbols | PR #15 pack; eSpeak NG 1.52.0 default en-us formant voice / original editable SVGs | Preserve `frontend/public/asset-licenses/`, manifest, generation source and GPL-3.0-or-later notices. No Microsoft recordings are in this pack. |
| Live full-text voice | Microsoft Zira - English (United States), localService true on reported LOQ/Chrome | Device-specific human report; integrated audible verification and other laptops remain separate. |
| Figma pictures in PR #17 | Export/source manifest and file hashes on Robin's branch | Recognition and redistribution review pending; PR #15's license/audit does not cover those different files. |
| Product libraries | Existing locked React 19.3.0, Vite 8.3.4, FastAPI/Pydantic/Uvicorn/HTTPX | Preserve upstream licenses/notices; this work adds no product dependency. |
| Ollama / model | Optional backend lane and PR #16, separately reviewed/verified | Exact runtime/model digest, model license, evaluation and final-build use need the backend owner's evidence. No AI success is claimed by the direct AAC demo. Conversation stays disabled. |
| Demo libraries | Existing isolated Playwright/Remotion/FFmpeg tools and lockfile | Keep their notices; verify actual eligibility/rights before distributing produced material. Existing tool availability is not a final video result. |

## Submission evidence still needed

Official event name/rules source, required links/files, format, actual
integrated commit, final demo device and technical-question owner,
actual video artifact/full playback review and final human package approval are
not documented here. Ahron is the user-named presenter and no fixed duration is
reported; neither statement supplies an official rules source. Issue #5 records
team deadlines of October 10 at 06:00
feature freeze, 08:00 demo-ready and 10:00 submission, Philippine time (UTC+08);
confirm these against official rules instead of treating issue text as the rules.
Overall submission readiness remains NOT READY until those gates are evidenced.
