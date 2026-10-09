import test from 'node:test';
import assert from 'node:assert/strict';
import { createSpeechController, getSpeechState, speakText, speakCards } from './index.mjs';

// Small test fixture, not a replacement for shared/vocabulary.json.
const vocabulary = { version: 'tanaw-v1', cards: ['want', 'eat', 'apple'].map(id => ({
  id, label: id === 'want' ? 'Want' : id === 'eat' ? 'Eat' : 'Apple', audio_path: `audio/en/${id}.wav`,
})) };
const local = { voiceURI: 'local-english', name: 'Local test voice', lang: 'en-US', localService: true };

function device(voices = [local]) {
  const utterances = [], audios = [], timers = new Map(), events = new Map();
  let timerId = 0, cancels = 0;
  const env = {
    speechSynthesis: {
      getVoices: () => voices,
      cancel: () => { cancels++; },
      speak: utterance => { utterances.push(utterance); },
      addEventListener: (name, fn) => events.set(name, fn),
      removeEventListener: name => events.delete(name),
    },
    SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
    Audio: class {
      constructor(src) { this.src = src; this.paused = false; audios.push(this); }
      play() { return Promise.resolve(); }
      pause() { this.paused = true; }
      removeAttribute() { this.src = ''; }
      load() {}
    },
    setTimeout: fn => { timers.set(++timerId, fn); return timerId; },
    clearTimeout: id => timers.delete(id),
  };
  return { env, utterances, audios, timers, events, get cancels() { return cancels; } };
}
function setup(options = {}, voices) {
  const d = device(voices);
  return { ...d, speech: createSpeechController({ vocabulary, ...options }, d.env) };
}

test('uninitialized exports truthfully refuse playback', async () => {
  assert.equal(getSpeechState().capability, 'unavailable');
  assert.equal((await speakText('Hello')).error.code, 'not_initialized');
  assert.equal((await speakCards(['apple'])).error.code, 'not_initialized');
});

test('unverified, remote and non-English voices cannot speak text', async () => {
  for (const [options, voices] of [
    [{}, [local]],
    [{ verifiedVoiceURI: local.voiceURI }, [{ ...local, localService: false }]],
    [{ verifiedVoiceURI: local.voiceURI }, [{ ...local, lang: 'fr-FR' }]],
    [{ verifiedVoiceURI: 'absent' }, [local]],
  ]) {
    const { speech, utterances } = setup(options, voices);
    assert.equal(speech.getState().capability, 'unavailable');
    assert.equal((await speech.speakText('I want to eat an apple.')).error.code, 'full_text_unavailable');
    assert.equal(utterances.length, 0);
    speech.dispose();
  }
});

test('explicit text uses the exact verified voice and reports completion', async () => {
  const { speech, utterances, timers } = setup({ verifiedVoiceURI: local.voiceURI });
  const pending = speech.speakText('I do not want water.');
  assert.equal(speech.getState().capability, 'full_text');
  assert.equal(speech.getState().playback, 'speaking');
  assert.equal(utterances[0].text, 'I do not want water.');
  assert.equal(utterances[0].voice, local);
  utterances[0].onend();
  assert.deepEqual(await pending, { ok: true });
  assert.equal(speech.getState().playback, 'idle');
  assert.equal(timers.size, 0);
  speech.dispose();
});

test('card speech preserves selection order and intentional duplicates', async () => {
  const { speech, utterances } = setup({ verifiedVoiceURI: local.voiceURI });
  const pending = speech.speakCards(['apple', 'want', 'apple']);
  assert.equal(utterances[0].text, 'Apple Want Apple');
  utterances[0].onend();
  assert.equal((await pending).ok, true);
  speech.dispose();
});

test('stop settles pending playback; stale events cannot replace new playback', async () => {
  const { speech, utterances } = setup({ verifiedVoiceURI: local.voiceURI });
  const first = speech.speakText('First');
  const staleEnd = utterances[0].onend;
  const second = speech.speakText('Second');
  assert.deepEqual(await first, { ok: false, stopped: true });
  staleEnd();
  assert.equal(speech.getState().playback, 'speaking');
  speech.stopSpeech();
  assert.deepEqual(await second, { ok: false, stopped: true });
  assert.equal(speech.getState().playback, 'stopped');
  const replay = speech.speakText('Second');
  utterances[2].onend();
  assert.equal((await replay).ok, true);
  speech.dispose();
});

test('full-text failure never switches to card clips', async () => {
  const { speech, utterances, audios } = setup({ verifiedVoiceURI: local.voiceURI,
    availableClipIds: ['want', 'eat', 'apple'] });
  const pending = speech.speakText('I want to eat an apple.');
  utterances[0].onerror({ error: 'synthesis-failed' });
  assert.equal((await pending).error.code, 'playback_failed');
  assert.equal(audios.length, 0);
  assert.equal(speech.getState().playback, 'error');
  speech.dispose();
});

test('clip fallback requires the complete vocabulary library', async () => {
  const { speech, audios } = setup({ availableClipIds: ['apple'] }, []);
  assert.equal(speech.getState().capability, 'unavailable');
  assert.deepEqual(speech.getState().missingClipIds, ['want', 'eat']);
  assert.equal((await speech.speakCards(['apple'])).error.code, 'cards_unavailable');
  assert.equal(audios.length, 0);
  speech.dispose();
});

test('complete fallback plays root-local clips in selection order, including repeats', async () => {
  const { speech, audios } = setup({ availableClipIds: ['want', 'eat', 'apple'] }, []);
  assert.equal(speech.getState().capability, 'cards_only');
  const pending = speech.speakCards(['apple', 'want', 'apple']);
  assert.equal(audios[0].src, '/audio/en/apple.wav');
  audios[0].onended();
  assert.equal(audios[1].src, '/audio/en/want.wav');
  audios[1].onended();
  assert.equal(audios[2].src, '/audio/en/apple.wav');
  audios[2].onended();
  assert.equal((await pending).ok, true);
  assert.ok(audios.every(audio => audio.paused));
  speech.dispose();
});

test('stopping clips does not play the next card and allows explicit replay', async () => {
  const { speech, audios } = setup({ availableClipIds: ['want', 'eat', 'apple'] }, []);
  const first = speech.speakCards(['want', 'eat']);
  const staleEnded = audios[0].onended;
  speech.stopSpeech();
  staleEnded();
  assert.deepEqual(await first, { ok: false, stopped: true });
  assert.equal(audios.length, 1);
  assert.equal(audios[0].paused, true);
  const replay = speech.speakCards(['want']);
  audios[1].onended();
  assert.equal((await replay).ok, true);
  speech.dispose();
});

test('autoplay rejection, missing clip, and stalled playback are errors, not success', async () => {
  for (const mode of ['reject', 'missing', 'timeout']) {
    const d = device([]);
    if (mode === 'reject') d.env.Audio.prototype.play = () => Promise.reject(new Error('NotAllowedError'));
    const speech = createSpeechController({ vocabulary, availableClipIds: ['want', 'eat', 'apple'] }, d.env);
    const pending = speech.speakCards(['want', 'eat']);
    if (mode === 'missing') d.audios[0].onerror();
    if (mode === 'timeout') [...d.timers.values()][0]();
    assert.equal((await pending).error.code, mode === 'timeout' ? 'playback_timeout' : 'playback_failed');
    assert.equal(d.audios.length, 1);
    assert.equal(d.timers.size, 0);
    speech.dispose();
  }
});

test('input boundaries reject unknown IDs, empty input and too many cards', async () => {
  const { speech, utterances } = setup({ verifiedVoiceURI: local.voiceURI });
  for (const input of [[], ['unknown'], Array(13).fill('apple'), null]) {
    assert.equal((await speech.speakCards(input)).error.code, 'invalid_cards');
  }
  for (const input of ['', '   ', null, 'a'.repeat(2001)]) {
    assert.equal((await speech.speakText(input)).error.code, 'invalid_text');
  }
  assert.equal(utterances.length, 0);
  speech.dispose();
});

test('invalid explicit playback cancels old audio rather than displaying a false state', async () => {
  const { speech, utterances } = setup({ verifiedVoiceURI: local.voiceURI });
  const pending = speech.speakText('Long message');
  await speech.speakCards(['unknown']);
  assert.deepEqual(await pending, { ok: false, stopped: true });
  assert.equal(utterances[0].onend, null);
  assert.equal(speech.getState().playback, 'error');
  speech.dispose();
});

test('a disappearing local voice stops active speech and cannot use a remote replacement', async () => {
  const voices = [local];
  const { speech, utterances, events } = setup({ verifiedVoiceURI: local.voiceURI }, voices);
  const pending = speech.speakText('Hello');
  voices.splice(0, 1, { ...local, localService: false });
  events.get('voiceschanged')();
  assert.deepEqual(await pending, { ok: false, stopped: true });
  assert.equal(speech.getState().capability, 'unavailable');
  assert.equal(speech.getState().error.code, 'full_text_unavailable');
  assert.equal(utterances[0].onerror, null);
  speech.dispose();
  assert.equal(events.size, 0);
});

test('observer errors do not prevent completion and returned state is isolated', async () => {
  const { speech, utterances } = setup({ verifiedVoiceURI: local.voiceURI });
  const states = [];
  const unsubscribe = speech.subscribe(state => states.push(state.playback));
  speech.subscribe(() => { throw new Error('Observer failure'); });
  const pending = speech.speakText('Hello');
  utterances[0].onend();
  await pending;
  const state = speech.getState();
  state.missingClipIds.push('tampered');
  assert.ok(!speech.getState().missingClipIds.includes('tampered'));
  assert.ok(states.includes('speaking') && states.includes('idle'));
  unsubscribe();
  speech.dispose();
});

test('speech API absence and synchronous browser failures are truthful errors', async () => {
  const empty = createSpeechController({ vocabulary }, { setTimeout, clearTimeout });
  assert.equal(empty.getState().capability, 'unavailable');
  assert.equal((await empty.speakText('Hello')).error.code, 'full_text_unavailable');
  assert.equal((await empty.speakCards(['apple'])).error.code, 'cards_unavailable');
  empty.dispose();
  const d = device();
  d.env.speechSynthesis.speak = () => { throw new Error('Device failed'); };
  const speech = createSpeechController({ vocabulary, verifiedVoiceURI: local.voiceURI }, d.env);
  assert.equal((await speech.speakText('Hello')).error.code, 'playback_failed');
  assert.equal(d.timers.size, 0);
  speech.dispose();
});

test('stalled full-text playback settles with an error and clears the utterance', async () => {
  const { speech, utterances, timers } = setup({ verifiedVoiceURI: local.voiceURI });
  const pending = speech.speakText('Hello');
  [...timers.values()][0]();
  assert.equal((await pending).error.code, 'playback_timeout');
  assert.equal(utterances[0].onend, null);
  assert.equal(timers.size, 0);
  speech.dispose();
});

test('a late rejection from cancelled clip playback cannot fail a new operation', async () => {
  const d = device([]);
  let rejectFirst;
  let attempts = 0;
  d.env.Audio.prototype.play = () => ++attempts === 1
    ? new Promise((resolve, reject) => { rejectFirst = reject; }) : Promise.resolve();
  const speech = createSpeechController({ vocabulary, availableClipIds: ['want', 'eat', 'apple'] }, d.env);
  const first = speech.speakCards(['want']);
  const second = speech.speakCards(['apple']);
  rejectFirst(new Error('Cancelled old audio'));
  await Promise.resolve();
  assert.deepEqual(await first, { ok: false, stopped: true });
  assert.equal(speech.getState().playback, 'speaking');
  d.audios[1].onended();
  assert.equal((await second).ok, true);
  speech.dispose();
});

test('rejects foreign vocabulary, remote/path traversal clips and duplicate IDs', () => {
  for (const bad of [
    { ...vocabulary, version: 'different' },
    { ...vocabulary, cards: [{ ...vocabulary.cards[0], audio_path: 'https://example.com/want.wav' }] },
    { ...vocabulary, cards: [{ ...vocabulary.cards[0], audio_path: 'audio/en/../../want.wav' }] },
    { ...vocabulary, cards: [vocabulary.cards[0], vocabulary.cards[0]] },
  ]) assert.throws(() => createSpeechController({ vocabulary: bad }), TypeError);
  assert.throws(() => createSpeechController({ vocabulary, availableClipIds: ['unknown'] }), TypeError);
});
