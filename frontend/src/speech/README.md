# Issue #5 speech checkpoint

Owner: GabDeGuz. Independent speech reviewer: RobinKielll. Evidence reviewer: Heiron8.
This module is independent of React, FastAPI, Ollama and network requests. No UI, state,
style, dependency manifest or shared vocabulary file is owned or changed here.

## Integrating the approved boundary

Import `initializeSpeech`, `speakText`, `speakCards`, `stopSpeech`, `getSpeechState` and
`subscribeSpeech` from `./speech/index.mjs`. Initialize once during setup with the
actual canonical `shared/vocabulary.json` object:

```js
initializeSpeech({
  vocabulary,
  verifiedVoiceURI, // exact local English URI proven offline on this laptop/browser
  availableClipIds, // only licensed recordings audited against the canonical file
});
const unsubscribe = subscribeSpeech(state => {
  // Map state to the already-approved UI. Never speak from this observer.
});
// Explicit user actions only:
await speakText(approvedText); // UI owns approval and stale-candidate invalidation
await speakCards(selectedCardIds);
stopSpeech();
// Cleanup the observer when its component unmounts:
unsubscribe();
```

`verifiedVoiceURI` defaults to null. Merely discovering a local voice does not verify
it. `availableClipIds` defaults to an empty array. Missing vocabulary does not prevent
standalone sentence testing, but cards are unavailable. Do not create another
vocabulary catalogue to fill this gap. Setup stays in memory and resets on reload;
the consuming app must supply the device-tested configuration again.

State includes `capability` (`full_text`, `cards_only`, `unavailable`), `playback`
(`idle`, `speaking`, `stopped`, `error`), `error`, chosen `voice`, `cardsReady` and
`missingClipIds`. The complete vocabulary recording library is needed to advertise
card fallback readiness. `full_text` and `cardsReady` are separate so UI can describe
missing fallback recordings even when a tested local voice works. Runtime failures
still return an error; an advertised capability is not evidence of audible playback.

Playback promises return `{ok: true}` only on the browser's completion event,
`{ok: false, stopped: true}` after explicit stop/replacement, or
`{ok: false, error: {code, message}}`. Native completion is not proof of audible
speech. Invalid playback requests stop previous audio and report an error. Only one
operation runs; stale callbacks cannot continue a stopped sequence or change the
new operation's state. Replay is another explicit call with the UI's retained text
or selected IDs; this module stores no conversation history.

Full text uses the exact verified local English voice, never the browser's default
or remote voice. Failed full text never silently switches to card audio. A disappearing
verified voice cancels active synthesis. Explicit card speech uses local synthesis
when available, otherwise complete bundled clips at `/audio/en/<canonical-id>.wav`
in selection order, preserving repeats. A synthesis error, timeout or synchronous
browser failure disables that voice for this controller; a subsequent explicit
card request uses the complete bundled library. Full text is never substituted
automatically. Reinitialize only after checking the device voice again.
Stop/dispose from a state observer cancels a pending start before any audio is
created. Disposed controllers cannot start another playback.
New playback, Stop, error and completion
release media/timers. No backend health or AI availability can disable this helper.

Bounds: 1–12 known cards, 1–2,000 nonblank text characters, a 120-second full-text
watchdog, and a 15-second watchdog per clip. The text limit is a helper validation
bound; the UI should explain it if editable text can reach it. Watchdog failures
stop audio and require a new explicit user action. There are no automatic retries.

## Verification

```powershell
node --test frontend/src/speech/speech.test.mjs
python scripts/verify.py
python docs/qa/serve-speech-check.py
```

Open `http://127.0.0.1:8765` in the actual laptop browser. Follow the per-laptop
[checklist](../../../docs/qa/offline-speech-checkpoint.md). The QA page's raw candidate
audition deliberately does not configure a production voice; only the human witness
checkbox can attest disconnected audible behavior for that browser session.

Current product verification runs 47 frontend tests: 31 speech-controller,
six asset/provenance/human-record checks, seven speech-QA state regressions and
three foundation tests. Structural WAV/SVG/hash checks use actual bundled files;
browser control tests use fixtures. Neither establishes installed-voice audibility,
human recognition or disconnected operation. The first checkpoint contained no
recordings or symbols. Issue #1's
canonical vocabulary/manifests are now merged. The continuation supplies 32 WAVs
and 32 original SVGs. Gab's individual human record reports all 32 recordings and
32 pictures PASS with Robin as witness. All seven standalone fallback rows were
later manually reported PASS; valid exported fallback detail, other-device and
integrated checks remain pending. Human design approval is now recorded; Robin's
separate PR #17 integrates the helper with a LOQ-only Zira opt-in and empty clip
configuration. See the [final integration handoff](../../../docs/qa/issue5-final-acceptance.md)
for exact build/device/clip/asset gates. PR #15's symbol recognition and license
do not certify PR #17's different Figma-export pictures.

## Asset continuation handoff

The files in `frontend/public/` match the unchanged canonical `audio_path` and
`symbol_path`: `/audio/en/<id>.wav`, `/symbols/<id>.svg`. Vite bundles these files
into the final static build. No inference, voice engine or network request is
needed to play these already bundled recordings. Runtime consumers can use the
canonical paths directly; `speech-assets.json` records source/license/checksums,
not permission to silently enable an unaudited library.

Before setting `availableClipIds`, a person must audition every actual label and
confirm intelligibility and asset rights; supply only audited IDs. The controller
advertises `cardsReady` only for the complete canonical library. Never derive
`verifiedVoiceURI` from the recording-generation engine: full-text speech requires
the laptop/browser's separately witnessed local English voice.

The candidate WAVs use eSpeak NG 1.52.0's default en-us formant voice and are
distributed under GPL-3.0-or-later with their source/recipe/license notices. SVGs
are original vectors, also supplied under GPL-3.0-or-later. Keep
`frontend/public/asset-licenses/` and the per-asset manifest when redistributing.
Read [source and rights](../../public/asset-licenses/SOURCE.md) and the
[current-laptop checklist](../../../docs/qa/current-laptop-speech-checklist.md).
Independent asset review and real-device checks are still required before a
demo-readiness claim. This handoff does not implement Robin's UI or approve design.
