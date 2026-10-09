# Issue #5: final integration and device acceptance

Owner: GabDeGuz. Prepared October 10, 2026, UTC+08. Issue #5 remains OPEN.
This is the remaining-work handoff, not a claim of final product acceptance.
Use the existing repository; no additional clone, worktree or PR is needed.

## Current evidence and integration boundary

Only Issue #5 is assigned to GabDeGuz in the live open-issue list.
Standalone speech was merged in [PR #12](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/pull/12).
The reviewed asset/evidence checkpoint is [PR #15](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/pull/15),
commit `9d3778b9fd517c9f68fd650555241994e4eb2d7b`; CI and independent review PASS.
Its canonical verification passed 47 frontend and seven backend tests, build,
dependency compatibility, loopback smoke and workspace/secret checks (one skip).
Those results identify this speech checkpoint, not a combined frontend build.

All 32 WAVs and 32 original SVGs are prepared, licensed and individually reported
PASS by Gab with Robin as reported asset witness. See the
[asset acceptance matrix](asset-acceptance.md) and immutable hash-bound manifest.
All seven fallback checks are manually reported PASS. The supplied fallback
rows have null check times/context; a valid fresh export, effective bundled mode,
explicit disconnection details and specific combined restart details remain open.
The [manual report](evidence/2026-10-10-loq-fallback-self-report.json) preserves these limits.
Other three laptops remain PENDING; current laptop success cannot approve them.

Design approval is now evidenced by [Heiron8's approval](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2#issuecomment-6087693386)
and [independent Design QA PASS](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/issues/2#issuecomment-6087806342).
The older issue/design text saying approval is pending is stale. Robin's
[PR #17](https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/pull/17),
inspected at `d7dfd5c3ed3f9d9077b1a52a9608f28a546ab828`, is the separate direct-AAC
frontend checkpoint. It is not merged into this branch or main at this check.
It calls the existing helper and offers the explicit `loq-zira` build profile,
but its `availableClipIds` are empty: it does not yet configure the 32 WAVs.
Its Figma-export pictures are different files from PR #15's original SVGs.
Their recognition/redistribution review remains pending in PR #17's manifest;
neither the GPL pack notice nor its human recognition results certify those exports.

## Robin / Lead handoff

1. Review the existing PRs and select the actual combined build through the normal
   integration process. Codex must not merge PR #15. Record its resulting exact
   commit before testing; none of the member-branch test counts certify that build.
2. Use the [speech interface](../../frontend/src/speech/README.md) and
   `shared/contracts.d.ts`. Configure canonical vocabulary, the exact device-tested
   local voice URI and only the complete licensed/audited clip IDs. All 32 clip
   paths must exist in the final build. Do not derive readiness from voice discovery.
3. On LOQ / Windows 11 / the tested Chrome, the reported voice URI is
   `Microsoft Zira - English (United States)`. PR #17 requires explicit
   `VITE_TANAW_SPEECH_PROFILE=loq-zira`; it does not certify any other device or
   configure card recordings. Robin owns adding the approved clip configuration
   and explicit cards-only choice. This handoff does not edit Robin's UI/profile.
4. Keep Speak separate from review/approval. Preserve card order and duplicates,
   stop/replay/error states and selection after failure. Full-text failure must
   never automatically substitute card recordings. Conversation remains disabled.
5. Confirm which picture files the final board uses, then obtain recognition and
   source/redistribution evidence for those actual bytes. Preserve PR #15's GPL
   notices, manifest and editable/generation source when bundling its pack.

## Setup for all four team laptops

Prepare the same speech checkpoint on each member's ONE existing repository.
Preserve unfinished work and use Project Sync; do not overwrite a member's task
branch or copy Gab's environment files. The team must integrate the approved
changes before testing the complete product. The standalone QA page can be tested
now from the reviewed Issue #5 files without React, Ollama or npm dependencies:

```powershell
python docs/qa/serve-speech-check.py --port 8770
```

Keep that terminal open and open `http://127.0.0.1:8770` on the same laptop.
If the port is already used by another task, choose a free port and use that URL;
do not terminate someone else's server. Python must already be installed before
disconnecting. All pictures, WAVs and QA modules are local files.

On each laptop enter its actual tester, witness, device, Windows build, browser
and tested commit. Do not reuse Gab/Robin/LOQ identity or audit context on a
different device. Select an installed local English candidate voice; Microsoft
Zira is the preference, but discovery alone does not verify it. Disconnect
Wi-Fi/Ethernet and other internet connections, attest that fact, then reload the
local page and re-enter the session details. While physically disconnected,
audibly test the candidate sentence, Stop, Replay and reload. Only after the
human confirmation should you select **Use verified voice for this browser
session** and **Test exported speakText**. Save evidence, restart the browser/local
server while disconnected and retest; a new browser session needs fresh voice
confirmation. Report a missing or silent local voice immediately.

Also audition the 32 WAVs and inspect the 32 pictures while disconnected, marking
their individual outcomes. After all 32 audio checks PASS, select **Use audited
clips only (no text voice)** for the seven fallback checks. A device lacking a
usable local voice can still test these explicit bundled clips. Save Evidence
JSON before reload/restart and after retesting. If PASS is rejected, follow that
row's inline prerequisite message; retain any manual report separately instead
of altering the exported timestamps or context.

| Team member | Laptop setup / test status | Evidence required |
| --- | --- | --- |
| GabDeGuz / Gab | LOQ: 32 audio + 32 picture PASS reported; fallback PASS self-report | Fresh validated fallback export and final integrated retest |
| Heiron8 | PENDING; device/browser/voice not supplied | Own setup, human audits, physical offline and integrated results |
| RobinKielll | PENDING; device/browser/voice not supplied | Own setup, human audits, physical offline and integrated results |
| LadlopezGit | PENDING; device/browser/voice not supplied | Own setup, human audits, physical offline and integrated results |

The user requests readiness for all team laptops and names **Ahron** as presenter.
Do not infer Ahron's GitHub identity from that name. Choose the presentation laptop
from devices that actually pass the combined-build rehearsal; all four receive
the same preparation checklist, not a shared PASS.

## Reproducible final-device test

First install the existing locked dependencies while connected,
using [development instructions](../development.md). Do not delete the existing
environment or create another repository to simulate a fresh setup. A genuine
first-time setup needs separately recorded clean-environment evidence.

After Lead integration, safely sync clean main using Project Sync in the same
folder. Set the device profile only on the verified LOQ before building:

```powershell
$env:VITE_TANAW_SPEECH_PROFILE = 'loq-zira'
python scripts/verify.py --ci
python scripts/dev.py
```

The launcher is provided by merged PR #14; it is not present on the older speech
branch. Follow its integrated instructions. For final static serving, set the
profile before the frontend build, then use the documented loopback server.
Run verification before launching persistent servers because its smoke check
requires ports 8000 and 5173 to be free. Keep the local asset server running for
reload and WAV requests. Stopping Ollama is different from stopping that server.

1. Record exact integrated commit, build profile, URL, laptop, Windows build,
   browser version, voice URI, tester, actual witness and check time.
2. Stop Ollama through its normal control; record that it is stopped. Disable
   Wi-Fi, unplug Ethernet and disable any other internet connection. Attest this
   personally; browser connectivity hints are not proof.
3. Start/reopen the app while disconnected. Select Want -> Eat -> Apple, open
   Review, then explicitly Speak. Confirm selected words audibly occur in order.
   Review or selection alone must produce no speech. This direct checkpoint does
   not produce an AI-expanded sentence; do not claim AI success with Ollama stopped.
4. Test Apple -> Want -> Apple, Stop during playback, Replay from the beginning,
   Undo/remove/reorder, confirmed Clear and the 12-card limit. Original selection
   must survive voice/model errors; distinguish Stop AAC from Stop audio.
5. Using Robin's explicit cards-only configuration after integration, repeat the
   order/repeat/Stop/Replay checks with full-text synthesis unavailable. Confirm
   full-text Speak reports `full_text_unavailable` without substituting clips.
   Test a deliberately missing clip only through the scoped QA fault; do not
   delete product assets. Expect `playback_failed`, no false success.
6. Save results before reload, then reload and restart the browser/local server
   while still disconnected. Restart requires both components and an actual
   subsequent audible test. Save the second session with its time/build context.
7. Test AI unavailable/timeout/error while the asset server remains up. For a
   complete backend shutdown check, keep Vite serving the frontend/assets; a
   stopped final static server cannot serve a new reload or uncached WAV.
8. Keyboard-test tab/focus, Enter/Space, edit/clear dialog focus, all essential
   actions and error announcements. Inspect the approved phone/tablet/laptop
   layouts, 200% text zoom, overflow and reduced motion. Record actual outcomes.

## Final acceptance record

| Check | Current result | Required evidence / owner |
| --- | --- | --- |
| Speech helper/contracts and 32 WAV/32 original SVG delivery | VERIFIED for PR #15 checkpoint | CI/review and asset records above; Gab |
| Current laptop voice and seven standalone fallback checks | Human-reported PASS; validated fallback detail pending | Fresh QA export with effective mode/time/context; Gab |
| Selected combined build and clip configuration | NOT READY | Lead integration; Robin clip profile/UI wiring |
| Integrated Want -> Eat -> Apple -> Review -> Speak, Ollama stopped/disconnected | PENDING | Audible human result on exact combined commit; Gab + actual witness |
| Integrated repeats/Stop/Replay/errors/reload/cold restart | PENDING | Separate local-voice and clips-only results, timestamps and errors |
| Integrated keyboard/responsive/accessibility review | PENDING | Actual rendered build, viewport/zoom/focus results; Gab |
| Recognition/rights for PR #17 Figma pictures | PENDING | Actual file hashes, recognition and source/rights review; Robin/Lead/Gab |
| Fresh setup on unprepared environment | PENDING | Existing team repo, locked setup logs/build identity; setup tester |
| Other three laptops | PENDING | Independent Heiron8 / RobinKielll / LadlopezGit device records |
| Final demo/video/rehearsal and submission requirements | NOT READY; Ahron is presenter | [Demo handoff](issue5-demo-runbook.md); actual footage, device, rules and human review |

For every human row provide PASS/FAIL/PENDING, actual outcome, check time, exact
commit, device/browser, witness, mode and error/Stop delay where applicable.
Do not backfill missing dates or copy a different build's results. Issue #5 stays
open until the remaining integrated/device/demo evidence is completed.
