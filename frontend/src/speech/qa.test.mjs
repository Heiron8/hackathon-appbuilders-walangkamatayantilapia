// DOM/browser-event fixtures only; never evidence of real audible/offline acceptance.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { createHumanAssetResults, resumeDeviceAssetResults } from '../../../docs/qa/speech-audit.mjs';
import { createSpeechController } from './index.mjs';

const source = readFileSync(new URL('../../../docs/qa/speech-probe.mjs', import.meta.url), 'utf8').replace(/^import[^\n]+\n/gm, '');
const vocabulary = JSON.parse(readFileSync(new URL('../../../shared/vocabulary.json', import.meta.url), 'utf8'));
const manifest = JSON.parse(readFileSync(new URL('../../public/speech-assets.json', import.meta.url), 'utf8'));
const zira = { name: 'Microsoft Zira Desktop', lang: 'en-US', localService: true, voiceURI: 'zira-fixture' };
const mark = { ...zira, name: 'Microsoft Mark', voiceURI: 'mark-fixture' };
class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.value = ''; this.disabled = false; this.checked = false; }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children = [...items]; }
  setAttribute(name, value) { this[name] = value; }
  click() { this.onclick?.(); }
  get firstChild() { return this.children[0]; }
}
async function fixture(initialVoices = [zira], assetSource = manifest) {
  const ids = [...readFileSync(new URL('../../../docs/qa/speech-check.html', import.meta.url), 'utf8').matchAll(/id="([^"]+)"/g)].map(match => match[1]);
  const elements = Object.fromEntries(ids.map(id => [id, new Element('div')]));
  elements.sample.value = 'I want to eat an apple.';
  let voices = initialVoices;
  const spoken = [], initialized = [], mediaPaths = [], downloads = [];
  class Audio {
    constructor(path) { this.path = path; mediaPaths.push(path); }
    play() { queueMicrotask(() => this.path.includes('__qa_missing') ? this.onerror?.() : this.onended?.()); return Promise.resolve(); }
    pause() {} removeAttribute() {} load() {}
  }
  const context = vm.createContext({
    document: { getElementById: id => elements[id], createElement: tag => new Element(tag), createTextNode: text => ({ text }) },
    navigator: { userAgent: 'fixture browser', onLine: false },
    window: { speechSynthesis: { getVoices: () => voices, cancel() {}, speak: utterance => spoken.push(utterance), addEventListener() {} }, addEventListener() {} },
    SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
    fetch: async path => ({ ok: !path.includes('__qa_missing'), status: path.includes('__qa_missing') ? 404 : 200,
      json: async () => path === '/vocabulary.json' ? vocabulary : assetSource }),
    initializeSpeech: setup => initialized.push(setup), stopSpeech() {},
    getSpeechState: () => {
      const setup = initialized.at(-1);
      const voice = voices.find(candidate => candidate.voiceURI === setup?.verifiedVoiceURI);
      const cardsReady = setup?.availableClipIds?.length === 32;
      return { voice, cardsReady, capability: voice ? 'full_text' : cardsReady ? 'cards_only' : 'unavailable' };
    },
    subscribeSpeech: cb => { cb({ capability: 'fixture' }); return () => {}; },
    speakText: async () => ({ ok: true }), speakCards: async () => ({ ok: true }),
    createHumanAssetResults, resumeDeviceAssetResults, createSpeechController, Audio, setTimeout, clearTimeout, Blob,
    URL: { createObjectURL: blob => { downloads.push(blob); return 'blob:fixture'; }, revokeObjectURL() {} },
  });
  await vm.runInContext(`(async () => { ${source} })()`, context);
  const evidence = () => JSON.parse(elements.evidence.textContent);
  const metadata = () => {
    for (const id of ['tester','audit-witness','device','os','tested-commit']) elements[id].value = `fixture ${id}`;
  };
  const card = id => {
    const box = elements['asset-audit'].children[vocabulary.cards.findIndex(item => item.id === id)];
    const labels = box.children.filter(child => child.tag === 'label');
    return { picture: box.children[0], retry: box.children[2],
      audio: labels[0].children[1], symbol: labels[1].children[1], symbolNotes: labels[1].children[2] };
  };
  return { elements, evidence, card, metadata, spoken, initialized, mediaPaths, downloads,
    setVoices(next) { voices = next; elements.refresh.onclick(); } };
}

test('QA prefers delayed local English Zira without speaking/verifying or silently substituting Mark', async () => {
  const f = await fixture([mark, { ...zira, localService: false }, { ...zira, lang: 'fr-FR' }]);
  assert.equal(f.elements.voice.value, ''); assert.equal(f.spoken.length, 0);
  assert.ok(f.initialized.every(setup => !setup.verifiedVoiceURI));
  f.setVoices([mark, zira]); assert.equal(f.elements.voice.value, zira.voiceURI);
  f.elements.test.onclick(); assert.equal(f.spoken.at(-1).voice.voiceURI, zira.voiceURI);
  f.elements.witness.checked = true; f.elements.witness.onchange(); f.elements.verify.onclick();
  assert.equal(f.initialized.at(-1).verifiedVoiceURI, zira.voiceURI);
  f.setVoices([mark]); assert.equal(f.elements.witness.checked, false);
  assert.equal(f.initialized.at(-1).verifiedVoiceURI, null); assert.equal(f.elements.voice.value, '');
  f.elements.voice.value = mark.voiceURI; f.elements.voice.onchange(); f.setVoices([mark, zira]);
  assert.equal(f.elements.voice.value, mark.voiceURI, 'preserve explicit tester choice');
});
test('QA records separate human PASS/FAIL, rejects missing identity, and does not infer recognition from image loading', async () => {
  const f = await fixture(); const c = f.card('go');
  c.audio.value = 'PASS'; c.audio.onchange(); assert.equal(c.audio.value, 'PENDING');
  f.metadata(); c.audio.value = 'PASS'; c.audio.onchange();
  assert.equal(f.evidence().humanAssetResults.find(row => row.id === 'go').audio.status, 'PASS');
  c.picture.firstChild.onload(); assert.equal(c.symbol.value, 'PENDING');
  c.symbol.value = 'FAIL'; c.symbol.onchange();
  f.elements['download-evidence'].onclick(); assert.equal(f.downloads.length, 0, 'unexplained FAIL cannot export');
  c.symbolNotes.value = 'Arrow meaning ambiguous to fixture witness'; c.symbolNotes.onchange();
  f.elements['download-evidence'].onclick(); assert.equal(f.downloads.length, 1);
  assert.equal(f.evidence().humanAssetResults.find(row => row.id === 'go').symbol.status, 'FAIL');
  assert.deepEqual(f.evidence().humanRecognizedSymbolIds, []);
});
test('QA picture failure revokes PASS, permits human FAIL, and ignores callbacks from replaced images', async () => {
  const f = await fixture(); f.metadata(); const c = f.card('go');
  c.picture.firstChild.onload(); c.symbol.value = 'PASS'; c.symbol.onchange();
  c.picture.firstChild.onerror(); assert.equal(c.symbol.value, 'PENDING');
  c.symbol.value = 'PASS'; c.symbol.onchange(); assert.equal(c.symbol.value, 'PENDING');
  c.symbol.value = 'FAIL'; c.symbol.onchange(); assert.equal(c.symbol.value, 'FAIL');
  const previous = c.picture.firstChild; c.retry.onclick(); previous.onload(); previous.onerror();
  assert.equal(c.symbol.disabled, true); c.picture.firstChild.onload();
  assert.equal(c.symbol.value, 'FAIL', 'loading/recovery never invents human PASS');
  assert.deepEqual(f.evidence().pictureLoadFailures, []);
});
test('QA enables clips only after all audio PASS; missing-media request reaches error; offline results require human disconnection', async () => {
  const f = await fixture(); f.metadata(); assert.equal(f.elements.fallback.disabled, true);
  for (const item of vocabulary.cards) { const c = f.card(item.id); c.audio.value = 'PASS'; c.audio.onchange(); }
  assert.equal(f.elements.fallback.disabled, false); f.elements.fallback.onclick();
  assert.equal(f.initialized.at(-1).verifiedVoiceURI, null);
  await f.elements['missing-media'].onclick();
  assert.deepEqual(f.mediaPaths, ['/audio/en/__qa_missing_apple.wav']);
  assert.equal(f.evidence().helperEvents.at(-1).result.error.code, 'playback_failed');
  assert.equal(f.evidence().helperEvents.at(-1).httpStatus, 404);
  assert.equal(f.evidence().helperEvents.at(-1).playbackMode, 'bundled_clips');
  const select = f.elements['offline-results'].children[0].children[1];
  select.value = 'PASS'; select.onchange(); assert.equal(select.value, 'PENDING');
  f.elements['physically-offline'].checked = true; select.value = 'PASS'; select.onchange();
  assert.equal(f.evidence().offlineFallbackResults[0].status, 'PASS');
  assert.equal(f.spoken.length, 0);
});
test('QA exports the eighth full-text rejection outcome only after explicit human marking with offline context', async () => {
  const f = await fixture(); f.metadata();
  f.elements.tester.onchange();
  const outcomes = f.evidence().offlineFallbackResults;
  assert.equal(outcomes.length, 8);
  assert.ok(outcomes.every(row => row.status === 'PENDING' && row.checkedAt === null));
  const index = outcomes.findIndex(row => row.id === 'full-text-unavailable');
  const select = f.elements['offline-results'].children[index].children[1];
  select.value = 'PASS'; select.onchange(); assert.equal(select.value, 'PENDING');
  for (const item of vocabulary.cards) { const c = f.card(item.id); c.audio.value = 'PASS'; c.audio.onchange(); }
  f.elements.fallback.onclick();
  assert.equal(f.evidence().offlineFallbackResults[index].status, 'PENDING');
  f.elements['physically-offline'].checked = true;
  select.value = 'PASS'; select.onchange();
  f.elements['download-evidence'].onclick();
  const saved = JSON.parse(await f.downloads.at(-1).text());
  const row = saved.offlineFallbackResults[index];
  assert.equal(row.status, 'PASS'); assert.ok(Number.isFinite(Date.parse(row.checkedAt)));
  assert.equal(row.context.tester, 'fixture tester'); assert.equal(row.context.physicallyDisconnected, true);
});
test('QA explains rejected fallback results beside the affected control and retains human evidence gates', async () => {
  const f = await fixture();
  const row = f.elements['offline-results'].children[0];
  const select = row.children[1], feedback = row.children[3];
  const markPass = () => { select.value = 'PASS'; select.onchange(); };
  markPass(); assert.equal(select.value, 'PENDING');
  assert.match(feedback.textContent, /Tester name.*Witness.*Laptop description.*Windows version\/build.*Exact Git commit tested/);
  f.metadata(); markPass(); assert.equal(select.value, 'PENDING');
  assert.match(feedback.textContent, /tick "I personally disconnected"/);
  f.elements['physically-offline'].checked = true; markPass();
  assert.match(feedback.textContent, /0\/32.*Restore recorded asset audits/);
  for (const item of vocabulary.cards) { const c = f.card(item.id); c.audio.value = 'PASS'; c.audio.onchange(); }
  f.elements.witness.checked = true; f.elements.witness.onchange(); f.elements.verify.onclick();
  markPass(); assert.equal(select.value, 'PENDING');
  assert.match(feedback.textContent, /Click "Use audited clips only/);
  f.elements.fallback.onclick(); markPass(); assert.equal(select.value, 'PASS');
  assert.match(feedback.textContent, /Recorded PASS for fixture tester/);
  const result = f.evidence().offlineFallbackResults[0];
  assert.ok(result.checkedAt); assert.equal(result.context.tester, 'fixture tester');
  assert.equal(result.context.physicallyDisconnected, true);
  select.value = 'PENDING'; select.onchange(); assert.equal(feedback.textContent, '');
  assert.equal(f.evidence().offlineFallbackResults[0].checkedAt, null);
});
test('QA resumes file-bound human results only for the same named tester/witness/device; retains original times without voice verification', async () => {
  const recorded = { tester: 'fixture tester', witness: 'fixture audit-witness', device: 'fixture device',
    os: 'fixture os', browser: 'fixture browser', tested_commit: 'fixture tested-commit',
    checked_at: '2026-10-10T03:00:00+08:00', notes: '', evidence_ref: 'fixture only', physical_disconnection_attested: true };
  const audited = { ...manifest, assets: manifest.assets.map(asset => ({ ...asset,
    audible_label_audit: 'PASS', picture_recognition_audit: 'PASS', audit_evidence: {
      audible_label: { ...recorded, asset_sha256: asset.audio_sha256 },
      picture_recognition: { ...recorded, asset_sha256: asset.symbol_sha256 } } })) };
  const f = await fixture([zira], audited); f.metadata();
  f.elements.device.value = 'another device';
  f.elements['resume-audits'].onclick(); assert.match(f.elements.result.textContent, /different/);
  assert.deepEqual(f.evidence().humanAuditedAudioIds, []);
  f.elements.device.value = recorded.device;
  f.elements['resume-audits'].onclick();
  assert.equal(f.evidence().humanAuditedAudioIds.length, 32);
  const restored = resumeDeviceAssetResults(vocabulary, audited, recorded);
  assert.equal(restored[0].audio.checkedAt, recorded.checked_at);
  assert.equal(restored[0].audio.status, 'PASS');
  assert.throws(() => resumeDeviceAssetResults(vocabulary, audited, { ...recorded, device: 'another laptop' }), /different/);
  assert.throws(() => resumeDeviceAssetResults(vocabulary, audited, { ...recorded, browser: 'another browser' }), /different/);
  assert.equal(f.spoken.length, 0); assert.ok(f.initialized.every(setup => !setup.verifiedVoiceURI));
});
test('QA logs effective request mode after unavailable configuration instead of stale verified voice preference', async () => {
  const f = await fixture(); f.metadata();
  f.elements.witness.checked = true; f.elements.witness.onchange(); f.elements.verify.onclick();
  await f.elements['helper-test'].onclick();
  assert.equal(f.evidence().helperEvents.at(-1).verifiedVoiceURI, zira.voiceURI);
  assert.equal(f.evidence().helperEvents.at(-1).playbackMode, 'local_synthesis');
  await f.elements.unavailable.onclick();
  assert.equal(f.evidence().helperEvents.at(-1).verifiedVoiceURI, null);
  assert.equal(f.evidence().helperEvents.at(-1).playbackMode, 'unavailable');
});
