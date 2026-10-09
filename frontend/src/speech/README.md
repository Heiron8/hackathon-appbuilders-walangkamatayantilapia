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
in selection order, preserving repeats. New playback, Stop, error and completion
release media/timers. No backend health or AI availability can disable this helper.

Bounds: 1–12 known cards, 1–2,000 nonblank text characters, a 120-second full-text
watchdog, and a 15-second watchdog per clip. The text limit is a helper validation
bound; the UI should explain it if editable text can reach it. Watchdog failures
stop audio and require a new explicit user action. There are no automatic retries.

## Verification

```powershell
node --test frontend/src/speech/speech.test.mjs
python docs/qa/serve-speech-check.py
```

Open `http://127.0.0.1:8765` in the actual laptop browser. Follow the per-laptop
[checklist](../../../docs/qa/offline-speech-checkpoint.md). The QA page's raw candidate
audition deliberately does not configure a production voice; only the human witness
checkbox can attest disconnected audible behavior for that browser session.

Tests use small injected fixture vocabularies and fake browser events to verify
control flow. They do not validate an installed voice, real WAV files or offline
operation. The first checkpoint contains no recordings or symbols and makes no
licensed-asset readiness claim. UI integration waits for design approval and the
shared vocabulary/manifests from TANAW-01.
