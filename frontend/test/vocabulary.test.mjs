import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { renderToStaticMarkup } from 'react-dom/server';
import { createElement } from 'react';
import { validateVocabulary } from '../../shared/vocabulary.mjs';

const vocabulary = JSON.parse(readFileSync(new URL('../../shared/vocabulary.json', import.meta.url)));
const contracts = JSON.parse(readFileSync(new URL('../../shared/contracts.json', import.meta.url)));
const approvedIds = 'no stop help repeat something_else yes i want not more finished eat drink play go rest water milk juice apple banana rice bread toy ball music home school outside toilet parent teacher'.split(' ');

test('bundled vocabulary has the exact stable IDs and order', () => {
  assert.equal(validateVocabulary(vocabulary), vocabulary);
  assert.deepEqual(vocabulary.cards.map(card => card.id), approvedIds);
  assert.equal(contracts.vocabulary_version, vocabulary.version);
  assert.equal(contracts.suggestions_enabled, false);
});

test('rejects version drift, count, duplicate IDs, extra fields, order and remote paths', () => {
  const mutations = [
    data => { data.version = 'tanaw-v2'; },
    data => { data.cards.pop(); },
    data => { data.cards[1].id = data.cards[0].id; },
    data => { data.cards[0].extra = 'unexpected'; },
    data => { data.cards[0].order = 4; },
    data => { data.cards[0].symbol_path = 'https://example.com/no.svg'; },
    data => { data.cards[0].audio_path = '../no.wav'; },
    data => { data.cards[0].category = 'unknown'; },
    data => { data.cards[0].label = ''; },
  ];
  for (const mutate of mutations) {
    const data = structuredClone(vocabulary);
    mutate(data);
    assert.throws(() => validateVocabulary(data));
  }
});

test('validated local labels are usable by React without any API request', () => {
  const html = renderToStaticMarkup(createElement('p', null,
    validateVocabulary(vocabulary).cards.map(card => card.label).join(' ')));
  assert.match(html, /Something else/);
  assert.match(html, /Apple/);
});
