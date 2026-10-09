// QA only: this entry is not part of the production build. No real audio or
// offline/asset certification occurs. Drive the real App and existing helper
// with controllable synthetic browser completion/failure events.
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from '../src/App.jsx';
import { vocabulary } from '../src/vocabulary.js';
import { createSpeechController } from '../src/speech/index.mjs';

let utterance = null;
let requests = 0;
let controller = null;
function recordRequest() {
  requests++;
  document.getElementById('qa-requests').textContent = `Synthetic playback requests: ${requests}`;
}
const env = {
  setTimeout: (...args) => window.setTimeout(...args),
  clearTimeout: (...args) => window.clearTimeout(...args),
  SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
  speechSynthesis: {
    getVoices: () => [{ voiceURI: 'qa-fixture', name: 'Synthetic QA voice', lang: 'en-US', localService: true }],
    speak(next) { utterance = next; recordRequest(); }, cancel() {},
    addEventListener() {}, removeEventListener() {},
  },
  Audio: class {
    play() { recordRequest(); return Promise.resolve(); }
    pause() {} removeAttribute() {} load() {}
  },
};
const speech = {
  getSpeechState: () => controller?.getState() ?? { capability: 'unavailable', playback: 'idle', error: null },
  initializeSpeech() {
    controller?.dispose();
    controller = createSpeechController({ vocabulary, verifiedVoiceURI: 'qa-fixture',
      availableClipIds: vocabulary.cards.map(card => card.id) }, env);
    return controller.getState();
  },
  subscribeSpeech: callback => controller.subscribe(callback),
  speakCards: ids => controller.speakCards(ids),
  stopSpeech: () => controller.stopSpeech(),
};

createRoot(document.getElementById('root')).render(<StrictMode>
  <section aria-label="Synthetic speech QA controls">
    <p>QA fixture — synthetic events only; no real audio or offline PASS.</p>
    <p id="qa-requests" role="status">Synthetic playback requests: 0</p>
    <button onClick={() => utterance?.onend?.()}>Simulate speech completion</button>
    <button onClick={() => utterance?.onerror?.()}>Simulate recoverable speech failure</button>
  </section>
  <App speech={speech} />
</StrictMode>);
