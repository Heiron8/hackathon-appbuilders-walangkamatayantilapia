import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { validateVocabulary } from '../../../shared/vocabulary.mjs';
import { validateHumanAssetAudit, createHumanAssetResults } from '../../../docs/qa/speech-audit.mjs';

const publicRoot = new URL('../../public/', import.meta.url);
const vocabulary = validateVocabulary(JSON.parse(readFileSync(
  new URL('../../../shared/vocabulary.json', import.meta.url), 'utf8',
)));
const manifest = JSON.parse(readFileSync(new URL('speech-assets.json', publicRoot), 'utf8'));
const read = path => readFileSync(new URL(path, publicRoot));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');

test('all 32 actual WAVs contain bounded non-silent mono PCM, not missing/dummy clips', () => {
  assert.deepEqual(readdirSync(new URL('audio/en/', publicRoot)).sort(),
    vocabulary.cards.map(card => `${card.id}.wav`).sort());
  for (const card of vocabulary.cards) {
    const bytes = read(card.audio_path);
    assert.equal(bytes.toString('ascii', 0, 4), 'RIFF', card.id);
    assert.equal(bytes.toString('ascii', 8, 12), 'WAVE', card.id);
    assert.equal(bytes.toString('ascii', 12, 16), 'fmt ', card.id);
    assert.equal(bytes.readUInt16LE(20), 1, 'PCM required');
    assert.equal(bytes.readUInt16LE(22), 1, 'mono required');
    assert.equal(bytes.readUInt32LE(24), 22050);
    assert.equal(bytes.readUInt16LE(34), 16);
    assert.equal(bytes.toString('ascii', 36, 40), 'data');
    assert.equal(bytes.readUInt32LE(40), bytes.length - 44);
    const duration = (bytes.length - 44) / (22050 * 2);
    assert.ok(duration >= 0.1 && duration < 15, `${card.id}: duration ${duration}`);
    let peak = 0;
    for (let offset = 44; offset < bytes.length; offset += 2) peak = Math.max(peak, Math.abs(bytes.readInt16LE(offset)));
    assert.ok(peak >= 100, `${card.id}: silent recording`);
  }
});

test('all 32 symbols are bounded original vectors without scripts, remote resources or font dependencies', () => {
  assert.deepEqual(readdirSync(new URL('symbols/', publicRoot)).sort(),
    vocabulary.cards.map(card => `${card.id}.svg`).sort());
  for (const card of vocabulary.cards) {
    const svg = read(card.symbol_path).toString('utf8');
    assert.ok(!svg.includes('\r'), `${card.id}: stable LF bytes required for cross-platform hashes`);
    assert.match(svg, /viewBox="0 0 96 96"/);
    assert.ok(svg.includes(`<title id="title">${card.label}</title>`));
    assert.doesNotMatch(svg, /<script|<image|<foreignObject|\bon\w+\s*=|\b(?:href|src)\s*=|@import|url\s*\(|<text\b/i);
    assert.match(svg, /GPL-3.0-or-later/);
  }
});

test('per-asset provenance/hashes match canonical paths; human PASS/FAIL requires witness evidence', () => {
  assert.equal(manifest.vocabulary_version, vocabulary.version);
  assert.equal(manifest.engine.version, '1.52.0');
  assert.equal(manifest.engine.voice, 'en-us (default formant)');
  assert.equal(manifest.asset_license, 'GPL-3.0-or-later');
  assert.match(read(manifest.license_file).toString('utf8'), /GNU GENERAL PUBLIC LICENSE/);
  assert.equal(manifest.assets.length, 32);
  for (const [index, card] of vocabulary.cards.entries()) {
    const record = manifest.assets[index];
    for (const key of ['id', 'label', 'order', 'audio_path', 'symbol_path']) assert.equal(record[key], card[key]);
    assert.equal(record.audio_sha256, hash(read(card.audio_path)));
    assert.equal(record.symbol_sha256, hash(read(card.symbol_path)));
    assert.equal(record.license, 'GPL-3.0-or-later');
    validateHumanAssetAudit(record);
    for (const [kind, audit] of [['audio', 'audible_label'], ['symbol', 'picture_recognition']]) {
      if (record[`${audit}_audit`] === 'PENDING') continue;
      const reported = record.audit_evidence[audit];
      assert.match(reported.evidence_ref, /^docs\/qa\/evidence\/[a-z0-9._-]+\.json$/);
      const evidence = JSON.parse(readFileSync(new URL(`../../../${reported.evidence_ref}`, import.meta.url), 'utf8'));
      const row = evidence.humanAssetResults.find(item => item.id === card.id);
      assert.equal(row[`${kind}_sha256`], reported.asset_sha256);
      assert.equal(row[kind].status, record[`${audit}_audit`]);
      assert.equal(row[kind].checkedAt, reported.checked_at);
      for (const key of ['tester', 'witness', 'device', 'os', 'browser']) assert.equal(row[kind].context[key], reported[key]);
      assert.equal(row[kind].context.testedCommit, reported.tested_commit);
    }
  }
});

const witness = { tester: 'fixture tester', witness: 'self-witnessed', device: 'fixture laptop',
  os: 'fixture OS', browser: 'fixture browser', tested_commit: 'fixture revision',
  evidence_ref: 'fixture evidence only', checked_at: '2026-10-10T03:00:00+08:00', notes: '' };
test('human audit validation supports PENDING, witnessed PASS and explained FAIL without changing provenance', () => {
  const original = manifest.assets[0];
  const recorded = { ...original, audible_label_audit: 'PASS', picture_recognition_audit: 'FAIL',
    audit_evidence: { audible_label: { ...witness, asset_sha256: original.audio_sha256 },
      picture_recognition: { ...witness, asset_sha256: original.symbol_sha256, notes: 'Ambiguous meaning' } } };
  assert.equal(validateHumanAssetAudit(recorded), recorded);
  assert.equal(recorded.audio_sha256, original.audio_sha256);
  assert.equal(recorded.license, original.license);
  assert.equal(validateHumanAssetAudit({ ...original, audible_label_audit: 'PENDING', picture_recognition_audit: 'PENDING' }).id, original.id);
});
test('human audit validation rejects invented bare PASS, undocumented FAIL and invalid statuses', () => {
  const original = manifest.assets[0];
  assert.throws(() => validateHumanAssetAudit({ ...original, audible_label_audit: 'PASS', audit_evidence: {} }), /needs tester/);
  assert.throws(() => validateHumanAssetAudit({ ...original, audible_label_audit: 'FAIL',
    audit_evidence: { audible_label: witness } }), /explanation/);
  assert.throws(() => validateHumanAssetAudit({ ...original, audible_label_audit: 'verified' }), /Invalid/);
  assert.throws(() => validateHumanAssetAudit({ ...original, audible_label_audit: 'PASS',
    audit_evidence: { audible_label: { ...witness, checked_at: 'not a date' } } }), /check time/);
  assert.throws(() => validateHumanAssetAudit({ ...original, audible_label_audit: 'PASS',
    audit_evidence: { audible_label: { ...witness, asset_sha256: '0'.repeat(64) } } }), /asset bytes/);
});
test('new laptop audit starts pending even if another device has recorded PASS, and binds exact asset hashes', () => {
  const audited = { ...manifest, assets: manifest.assets.map(asset => ({ ...asset, audible_label_audit: 'PASS' })) };
  const results = createHumanAssetResults(vocabulary, audited);
  assert.equal(results.length, 32);
  assert.ok(results.every(result => result.audio.status === 'PENDING' && result.symbol.status === 'PENDING'));
  assert.equal(results[0].audio_sha256, manifest.assets[0].audio_sha256);
  assert.throws(() => createHumanAssetResults(vocabulary, { assets: [] }), /provenance/);
});
