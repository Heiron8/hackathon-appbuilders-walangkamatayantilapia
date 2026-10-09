# Issue #5 - current laptop speech test

Tester: GabDeGuz. Only this laptop is available. Heiron8, RobinKielll and
LadlopezGit remain PENDING. Issue #5 stays OPEN; no PR merge is authorized here.
PR #12 is already merged; further reviewed assets/evidence use the Issue #5
continuation branch `task/issue-5-assets` in the same repository.

Current recorded result (October 10, 2026): GabDeGuz answered "it all pass" to
Zira speech, Stop, Replay and disconnected restart. Those four checks are recorded
as self-reported PASS on this laptop. Exact voice URI and Evidence JSON remain
unsupplied; other helper/asset/device/integrated checks are not inferred passed.
The steps below remain the reproducible checklist, not a request to repeat the
four already reported checks. See the [checkpoint](offline-speech-checkpoint.md)
for the evidence limits and remaining gates.

## First test: real full-sentence speech

1. From the repository root, run `python docs/qa/serve-speech-check.py --port 8770`.
   If the server is already running, leave it running. Open
   `http://127.0.0.1:8770` in Chrome on this physical laptop. This port contains
   the updated asset whitelist; the pre-existing 8765 server was preserved.
2. Record the browser version (Chrome menu > Help > About Google Chrome), Windows
   version/build and laptop description. Native inventory observed Windows build
   26200 and David/Zira Desktop en-US; browser availability is still unverified.
3. In the page, select Microsoft Zira, now the requested default local English
   candidate. If Zira is absent, report that rather than treating another voice as
   Zira. Changing from the previously reported Mark requires a new test. Copy its name, language
   and exact voice URI from Evidence after playing it. If the list is empty, click
   Refresh local voices once. Report an empty list immediately as a voice blocker.
4. Turn Wi-Fi off and unplug Ethernet; disable any other internet connection.
   Reload the loopback page with the server running. A browser Offline hint is not
   evidence that the physical connection was disconnected.
5. Click Test candidate sentence. You must actually hear the complete
   **I want to eat an apple.** clearly and with the intended words. Record PASS/FAIL
   and what you heard. A browser completion event without sound is FAIL.
6. Click the candidate button again and Stop audio while it is speaking. Record
   whether sound stops promptly (approximately how long). Click Replay candidate
   sentence; it must begin again from the first word without overlap.
7. Only after these audible checks and disconnected reload pass, tick the witness
   box and click Use verified voice for this browser session. Then click
   Test exported speakText. Hear the same whole sentence; the result should be
   `{ "ok": true }`. Stop it midway; result should be
   `{ "ok": false, "stopped": true }`. Click Test exported speakText again to replay.
8. Copy the entire Evidence JSON and the helper capability/result text. Record
   who listened; self-witnessed results may be recorded as such and are not an
   independent QA approval.
9. While still disconnected, close Chrome and stop the QA server with Ctrl+C.
   Restart the server, reopen Chrome at the same loopback address and repeat steps
   3-8. Do not reconnect to load a voice. Reload clears the witness/verification.

Stop and report the exact error if a voice cannot speak offline. Do not install a
new voice or change system settings as part of a PASS; report the setup change
and repeat the disconnected restart test afterward.

## More helper checks

After using the verified voice button, open Chrome Developer Tools (F12), select
Console and enter:

```js
var tanawSpeech = await import('/speech/index.mjs');
```

| Test | Action | Required outcome |
| --- | --- | --- |
| Ordered cards | `await tanawSpeech.speakCards(['want','eat','apple'])` | Hear Want, Eat, Apple, in that order; result ok:true |
| Repeated card | `await tanawSpeech.speakCards(['apple','want','apple'])` | Hear Apple twice, preserving selection order |
| Long text / Stop | `tanawSpeech.speakText('I want to eat an apple. I do not want milk. Please help me. I want water.');` then click Stop audio | Sound stops; helper playback is stopped, with no later restart |
| Replacement | Start the long text, then click Test exported speakText | Old message stops; only the new sentence plays |
| Explicit replay | Click Test exported speakText after Stop or completion | Starts from the beginning, once |
| No automatic speech | Reload and wait; select another voice without clicking Speak | No sound from loading, selection or verification alone |
| Empty text | `await tanawSpeech.speakText('')` | invalid_text error, no sound |
| Unknown card | `await tanawSpeech.speakCards(['unknown'])` | invalid_cards error, no sound |
| Selection limit | `await tanawSpeech.speakCards(Array(13).fill('apple'))` | invalid_cards error, no sound |
| Valid maximum | `await tanawSpeech.speakCards(Array(12).fill('apple'))` | Exactly 12 Apples in order; Stop remains usable |
| No configured voice/library | Reload; before verifying voice, try exported text/cards in Console | full_text_unavailable/cards_unavailable; no substitute voice or false success |

If the browser prevents a Console-triggered playback, record its exact error and
test with the page buttons. Do not bypass browser safety warnings. The production
app must eventually use explicit user-click actions.

## Bundled recordings and pictures

In the 32-card recording and picture audit section, click Play candidate for each
actual WAV. Check each audio/picture box only from what you actually heard/saw.
If a picture is missing, click its Retry picture button or direct picture link;
report any remaining failure. Failed/loading pictures cannot be marked recognized.
The candidate WAVs keep their documented eSpeak voice; selecting Zira affects live
speech synthesis, not the pre-recorded files.
For each card, record: intelligible exact English label, non-silent/complete audio,
recognizable corresponding picture, and PASS/FAIL with corrections. A generated
file or nonzero waveform is not an intelligibility/recognition PASS.

Only enable the audited clip library after all recordings pass. Click
Use audited clips only (no text voice), then Speak cards: Want -> Eat -> Apple;
Speak repeated cards: Apple -> Want -> Apple; Stop midway; Replay last card
sequence; and disconnected server/browser
restart. Full-text speech in clips-only mode must return full_text_unavailable;
it must not automatically speak different card audio. Click Test exported
speakText while in clips-only mode to check that error. Click
Test all-speech-unavailable errors and Test invalid inputs for the explicitly
configured unavailable/input cases; restore a verified voice or clips-only mode
afterward. These error buttons are configuration tests, not induced engine failures.
Record capability
cards_only, paths and results. Real missing/failed-media handling and synthesis
failure are separate checks; deterministic regressions are not a live-device PASS.

Integrated board, Review/approval, Stop communication card, design accessibility,
Ollama stopped and backend-failure journey tests stay PENDING until Robin's
design-approved integrated application is available.

## Paste these results back

```text
Tester / person who listened:
Independent witness (if none, write self-witnessed):
Date/time and timezone:
Git commit / branch tested:
Laptop description:
Windows version/build:
Browser/version:
Voice name / language / exact URI / localService:
Physical disconnection (Wi-Fi/Ethernet/other connections):
Candidate full sentence: PASS/FAIL; exact words heard:
Exported speakText: PASS/FAIL; returned result:
Stop: PASS/FAIL; approximate delay:
Replay from beginning: PASS/FAIL:
Card order / repeated card / 12-card limit: PASS/FAIL or pending:
Replacement / no automatic speech: PASS/FAIL or pending:
Empty text / unknown card / 13-card rejection: PASS/FAIL or pending:
Disconnected reload: PASS/FAIL:
Disconnected browser + server restart: PASS/FAIL:
32 WAV auditions: passing IDs / failing IDs / not tested:
32 symbol review: passing IDs / failing IDs / not tested:
Clips-only order/repeat/Stop/Replay/restart: PASS/FAIL or pending:
Missing/failed-media handling: PASS/FAIL or not tested:
Any exact errors or pronunciation/recognition concerns:
Evidence JSON (paste from page):
```

Use PENDING for untested cases. Results apply only to the named laptop/browser,
voice and build. The other three laptops remain pending, and Issue #5 stays open.
