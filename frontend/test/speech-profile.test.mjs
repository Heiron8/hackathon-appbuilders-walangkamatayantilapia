import test from 'node:test';
import assert from 'node:assert/strict';
import { selectSpeechProfile, verifiedSpeechProfile } from '../src/speech-profile.mjs';

test('default, absent and unknown profile never certify a voice or card recordings', () => {
  for (const profile of [undefined, null, '', 'unknown', 'zira', 'LOQ-ZIRA']) {
    assert.deepEqual(selectSpeechProfile(profile), { verifiedVoiceURI: null, availableClipIds: [] });
  }
  assert.deepEqual(verifiedSpeechProfile, { verifiedVoiceURI: null, availableClipIds: [] });
});
test('explicit loq-zira profile supplies only the exact device-evidenced voice URI', () => {
  const profile = selectSpeechProfile('loq-zira');
  assert.equal(profile.verifiedVoiceURI, 'Microsoft Zira - English (United States)');
  assert.deepEqual(profile.availableClipIds, []);
  assert.ok(Object.isFrozen(profile)); assert.ok(Object.isFrozen(profile.availableClipIds));
});
