import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { initialMessage, updateMessage } from '../src/message-state.mjs';
import { createSpeechController } from '../src/speech/index.mjs';
const vocabulary = JSON.parse(await readFile(new URL('../../shared/vocabulary.json', import.meta.url)));
const ids = new Set(vocabulary.cards.map(card => card.id));
const apply = (state, action) => updateMessage(state, action, ids);
const compose = (...sequence) => sequence.reduce((state, id) => apply(state, { type: 'append', id }), initialMessage);

test('starts empty, preserves intentional repeats and selection order', () => {
  assert.deepEqual(initialMessage.selectedIds, []);
  assert.deepEqual(compose('want', 'eat', 'apple', 'apple').selectedIds, ['want', 'eat', 'apple', 'apple']);
  assert.deepEqual(vocabulary.cards.map(card => card.id).slice(0, 8), ['no', 'stop', 'help', 'repeat', 'something_else', 'yes', 'i', 'want']);
});
test('maximum twelve rejects a thirteenth without losing the message', () => {
  const full = compose(...Array(12).fill('apple'));
  const result = apply(full, { type: 'append', id: 'water' });
  assert.deepEqual(result.selectedIds, full.selectedIds);
  assert.equal(result.revision, full.revision);
  assert.match(result.notice, /12 pictures.*Remove a word/);
});
test('Undo, intentional indexed removal, reordering and clear preserve other words', () => {
  const original = compose('want', 'eat', 'apple', 'apple');
  assert.deepEqual(apply(original, { type: 'undo' }).selectedIds, ['want', 'eat', 'apple']);
  assert.deepEqual(apply(original, { type: 'remove', index: 2 }).selectedIds, ['want', 'eat', 'apple']);
  assert.deepEqual(apply(original, { type: 'move', index: 2, direction: -1 }).selectedIds, ['want', 'apple', 'eat', 'apple']);
  assert.deepEqual(apply(original, { type: 'clear' }).selectedIds, []);
});
test('every accepted word correction invalidates optional wording, approval and pending responses', () => {
  const original = { ...compose('want', 'eat', 'apple'), candidate: { text: 'example' }, approvedText: 'example', requestId: 'pending' };
  for (const action of [{ type: 'append', id: 'water' }, { type: 'undo' }, { type: 'remove', index: 1 },
    { type: 'move', index: 2, direction: -1 }, { type: 'clear' }]) {
    const result = apply(original, action);
    assert.equal(result.revision, original.revision + 1);
    assert.equal(result.candidate, null); assert.equal(result.approvedText, null); assert.equal(result.requestId, null);
  }
});
test('invalid IDs/indices and boundary moves leave revision and message untouched', () => {
  const message = compose('want', 'apple');
  for (const action of [{ type: 'append', id: 'invented' }, { type: 'remove', index: -1 }, { type: 'remove', index: 2 },
    { type: 'move', index: 0, direction: -1 }, { type: 'move', index: 1, direction: 1 }, { type: 'move', index: 0, direction: 3 }]) {
    assert.equal(apply(message, action), message);
  }
});
test('existing speech helper speaks only an explicit retained snapshot; Stop word is not Stop audio', async () => {
  const utterances = []; let cancels = 0;
  const voice = { voiceURI: 'offline-tested-fixture', name: 'fixture', lang: 'en-US', localService: true };
  const env = { setTimeout, clearTimeout, SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
    speechSynthesis: { getVoices: () => [voice], cancel: () => { cancels++; }, speak: utterance => utterances.push(utterance),
      addEventListener() {}, removeEventListener() {} } };
  const speech = createSpeechController({ vocabulary, verifiedVoiceURI: voice.voiceURI }, env);
  const message = compose('want', 'eat', 'apple', 'apple', 'stop');
  assert.equal(utterances.length, 0);
  const playback = speech.speakCards(message.selectedIds);
  assert.equal(utterances[0].text, 'Want Eat Apple Apple Stop');
  assert.equal(speech.getState().playback, 'speaking');
  assert.deepEqual(message.selectedIds, ['want', 'eat', 'apple', 'apple', 'stop']);
  speech.stopSpeech(); assert.equal(speech.getState().playback, 'stopped');
  assert.deepEqual(await playback, { ok: false, stopped: true }); assert.ok(cancels > 0);
  speech.dispose();
});
test('unverified browser voice is unavailable and cannot imply successful audio', async () => {
  let calls = 0;
  const env = { speechSynthesis: { getVoices: () => [{ voiceURI: 'present', lang: 'en-US', localService: true }],
    speak: () => calls++, addEventListener() {}, removeEventListener() {} } };
  const speech = createSpeechController({ vocabulary }, env);
  assert.equal(speech.getState().capability, 'unavailable');
  const result = await speech.speakCards(['want', 'eat', 'apple']);
  assert.equal(result.ok, false); assert.equal(result.error.code, 'cards_unavailable'); assert.equal(calls, 0);
  speech.dispose();
});
