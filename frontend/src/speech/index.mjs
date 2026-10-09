// Browser-owned speech. No backend calls, remote voices, or automatic fallback.
const errors = {
  not_initialized: 'Speech has not been initialized.',
  invalid_text: 'Enter a nonempty message to speak.',
  invalid_cards: 'Select between 1 and 12 known cards.',
  full_text_unavailable: 'Full sentence voice is unavailable. Choose Speak selected cards if available.',
  cards_unavailable: 'Selected card audio is unavailable.',
  playback_failed: 'Audio could not be played. Check the device audio and try explicitly again.',
  playback_timeout: 'Audio did not finish. Check the device audio and try explicitly again.',
};

/** verifiedVoiceURI must come from this laptop/browser's disconnected voice check.
 * availableClipIds must include only bundled, licensed, audited recordings.
 * Pass the shared vocabulary object; do not maintain a second card catalogue here.
 */
export function createSpeechController({
  vocabulary = null, verifiedVoiceURI = null, availableClipIds = [],
} = {}, env = globalThis) {
  if (vocabulary && (vocabulary.version !== 'tanaw-v1' || !Array.isArray(vocabulary.cards))) {
    throw new TypeError('Expected the canonical tanaw-v1 vocabulary.');
  }
  const cards = new Map();
  for (const card of vocabulary?.cards ?? []) {
    if (!/^[a-z_]+$/.test(card.id) || typeof card.label !== 'string' || !card.label.trim()
      || card.audio_path !== `audio/en/${card.id}.wav` || cards.has(card.id)) {
      throw new TypeError('Invalid canonical card or local audio path.');
    }
    cards.set(card.id, { ...card });
  }
  if (!Array.isArray(availableClipIds) || availableClipIds.some(id => !cards.has(id))) {
    throw new TypeError('Available clips must reference canonical card IDs.');
  }
  const available = new Set(availableClipIds);
  const synthesis = env.speechSynthesis;
  let playback = 'idle';
  let error = null;
  let active = null;
  let synthesisFailed = false;
  let disposed = false;
  const listeners = new Set();

  function localVoice() {
    if (synthesisFailed || !verifiedVoiceURI || !synthesis
      || typeof env.SpeechSynthesisUtterance !== 'function') return null;
    try {
      return synthesis.getVoices().find(voice => voice.voiceURI === verifiedVoiceURI
        && voice.localService === true && /^en(?:-|$)/i.test(voice.lang)) ?? null;
    } catch { return null; }
  }

  function getState() {
    const voice = localVoice();
    const missingClipIds = [...cards.keys()].filter(id => !available.has(id));
    const cardsReady = cards.size > 0 && missingClipIds.length === 0 && typeof env.Audio === 'function';
    return {
      capability: voice ? 'full_text' : cardsReady ? 'cards_only' : 'unavailable',
      playback, error: error ? { ...error } : null,
      voice: voice ? { name: voice.name, lang: voice.lang, voiceURI: voice.voiceURI, localService: true } : null,
      cardsReady, missingClipIds,
    };
  }

  function publish() {
    for (const listener of listeners) {
      // An observer must never interrupt cleanup or another observer.
      try { listener(getState()); } catch { /* observer-owned error */ }
    }
  }

  function fail(code) {
    if (active) stopSpeech();
    const failure = { code, message: errors[code] };
    error = failure;
    playback = 'error';
    publish();
    return { ok: false, error: { ...failure } };
  }

  function cancelPlayback() {
    const previous = active;
    active = null; // Invalidate events before cancel() can dispatch them.
    previous?.cancel?.();
    previous?.resolve({ ok: false, stopped: true });
  }

  function stopSpeech() {
    const alreadyStopped = !active && playback === 'stopped' && !error;
    cancelPlayback();
    playback = 'stopped';
    error = null;
    if (!alreadyStopped) publish();
  }

  function start(run, onFailure) {
    if (disposed) return Promise.resolve({ ok: false, stopped: true });
    cancelPlayback();
    return new Promise(resolve => {
      const operation = { resolve, cancel: null };
      active = operation;
      error = null;
      playback = 'stopped';
      publish();
      if (active !== operation) return;
      playback = 'speaking';
      publish();
      if (active !== operation) return;
      const finish = code => {
        if (active !== operation) return;
        active = null;
        operation.cancel?.();
        if (code) {
          onFailure?.();
          resolve(fail(code));
        }
        else {
          playback = 'idle';
          publish();
          resolve({ ok: true });
        }
      };
      try { run(operation, finish); } catch { finish('playback_failed'); }
    });
  }

  function speakText(text) {
    if (typeof text !== 'string' || !text.trim() || text.length > 2000) {
      return Promise.resolve(fail('invalid_text'));
    }
    const voice = localVoice();
    if (!voice) return Promise.resolve(fail('full_text_unavailable'));
    return start((operation, finish) => {
      const utterance = new env.SpeechSynthesisUtterance(text);
      utterance.voice = voice;
      utterance.lang = voice.lang;
      utterance.rate = 1;
      const timer = env.setTimeout(() => finish('playback_timeout'), 120000);
      operation.cancel = () => {
        env.clearTimeout(timer);
        utterance.onend = null;
        utterance.onerror = null;
        synthesis.cancel();
      };
      // Keep utterance alive until completion; some browsers lose unreferenced ones.
      operation.utterance = utterance;
      utterance.onend = () => finish();
      utterance.onerror = () => finish('playback_failed');
      synthesis.cancel();
      synthesis.speak(utterance);
    }, () => { synthesisFailed = true; });
  }

  function speakCards(cardIds) {
    if (!Array.isArray(cardIds) || cardIds.length < 1 || cardIds.length > 12
      || cardIds.some(id => !cards.has(id))) return Promise.resolve(fail('invalid_cards'));
    const selection = [...cardIds];
    if (localVoice()) return speakText(selection.map(id => cards.get(id).label).join(' '));
    // Partial libraries are not advertised as ready. Never substitute text or other clips.
    if (!getState().cardsReady) return Promise.resolve(fail('cards_unavailable'));
    return start((operation, finish) => {
      let audio = null;
      let timer = null;
      let position = 0;
      function release() {
        env.clearTimeout(timer);
        if (!audio) return;
        audio.onended = null;
        audio.onerror = null;
        audio.pause();
        audio.removeAttribute('src');
        audio.load();
        audio = null;
      }
      operation.cancel = release;
      function next() {
        if (active !== operation) return;
        release();
        if (position === selection.length) return finish();
        audio = new env.Audio(`/${cards.get(selection[position++]).audio_path}`);
        audio.onended = next;
        audio.onerror = () => finish('playback_failed');
        timer = env.setTimeout(() => finish('playback_timeout'), 15000);
        Promise.resolve(audio.play()).catch(() => finish('playback_failed'));
      }
      next();
    });
  }

  const voicesChanged = () => {
    // Never allow the browser to replace a disappearing tested voice with its default.
    if (active?.utterance && !localVoice()) {
      stopSpeech();
      fail('full_text_unavailable');
    } else publish();
  };
  synthesis?.addEventListener?.('voiceschanged', voicesChanged);

  return {
    speakText, speakCards, stopSpeech, getState,
    subscribe(listener) {
      if (typeof listener !== 'function') throw new TypeError('Expected a speech state listener.');
      listeners.add(listener);
      try { listener(getState()); } catch { /* observer-owned error */ }
      return () => listeners.delete(listener);
    },
    dispose() {
      disposed = true;
      stopSpeech();
      synthesis?.removeEventListener?.('voiceschanged', voicesChanged);
      listeners.clear();
    },
  };
}

let controller = null;
export function initializeSpeech(options) {
  controller?.dispose();
  controller = createSpeechController(options);
  return controller.getState();
}
export function getSpeechState() {
  return controller?.getState() ?? { capability: 'unavailable', playback: 'idle',
    error: { code: 'not_initialized', message: errors.not_initialized }, voice: null,
    cardsReady: false, missingClipIds: [] };
}
export function subscribeSpeech(listener) {
  if (!controller) throw new Error(errors.not_initialized);
  return controller.subscribe(listener);
}
export function speakText(text) {
  return controller?.speakText(text) ?? Promise.resolve({ ok: false, error: getSpeechState().error });
}
export function speakCards(cardIds) {
  return controller?.speakCards(cardIds) ?? Promise.resolve({ ok: false, error: getSpeechState().error });
}
export function stopSpeech() { controller?.stopSpeech(); }
