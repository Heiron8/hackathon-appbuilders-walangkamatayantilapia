import { initializeSpeech, speakText, speakCards, stopSpeech, subscribeSpeech, createSpeechController, getSpeechState } from '/speech/index.mjs';
import { createHumanAssetResults, resumeDeviceAssetResults } from '/speech-audit.mjs';

const sample = () => el('sample').value;
const el = id => document.getElementById(id);
let voices = [];
let audition = null;
let vocabulary = null;
let assetManifest = null;
let missingMediaController = null;
let unsubscribe = null;
let clipAudition = null;
let verifiedVoiceURI = null;
let voiceChosenByTester = false;
let lastCardIds = ['want', 'eat', 'apple'];
const auditedAudio = new Set();
const recognizedSymbols = new Set();
const failedPictures = new Set();
const assetControls = new Map();
const evidence = {
  browser: navigator.userAgent,
  connectedHint: navigator.onLine,
  checkedAt: null,
  candidateVoice: null,
  preferredCandidateVoice: 'Microsoft Zira',
  candidateEvents: [],
  disconnectedAudibleStopReplayReload: 'NOT VERIFIED',
  clips: 'NOT VERIFIED',
  integratedProduct: 'NOT VERIFIED',
  helperEvents: [],
  humanAuditedAudioIds: [],
  humanRecognizedSymbolIds: [],
  pictureLoadFailures: [],
  humanAssetResults: [],
  humanSession: null,
  offlineFallbackResults: [],
};

function humanContext() {
  return { tester: el('tester').value.trim(), witness: el('audit-witness').value.trim(),
    device: el('device').value.trim(), os: el('os').value.trim(),
    testedCommit: el('tested-commit').value.trim(), browser: navigator.userAgent,
    physicallyDisconnected: el('physically-offline').checked };
}
function contextComplete(context) {
  return ['tester', 'witness', 'device', 'os', 'testedCommit'].every(key => context[key]);
}
function renderEvidence() {
  evidence.connectedHintAtRecord = navigator.onLine; // A browser hint, never physical-disconnection proof.
  el('evidence').textContent = JSON.stringify(evidence, null, 2);
}
function configureHelper() {
  unsubscribe?.();
  initializeSpeech({ vocabulary, verifiedVoiceURI,
    availableClipIds: [...auditedAudio] });
  unsubscribe = subscribeSpeech(state => { el('capability').textContent = JSON.stringify(state); });
  el('helper-test').disabled = false; // Unavailable/error mode must also be testable.
  const canSpeakCards = Boolean(verifiedVoiceURI) || auditedAudio.size === 32;
  for (const id of ['helper-cards', 'helper-repeat', 'helper-replay']) el(id).disabled = !canSpeakCards;
  el('fallback').disabled = auditedAudio.size !== 32;
  el('missing-media').disabled = auditedAudio.size !== 32;
}
function helperContext(state = getSpeechState()) {
  return { context: humanContext(), verifiedVoiceURI: state.voice?.voiceURI ?? null,
    playbackMode: state.voice ? 'local_synthesis' : state.cardsReady ? 'bundled_clips' : 'unavailable',
    auditedClipCount: auditedAudio.size };
}
function recordHelper(action, result, requestContext = helperContext()) {
  evidence.helperEvents.push({ action, result, at: new Date().toISOString(),
    ...requestContext });
  el('result').textContent = JSON.stringify(result);
  renderEvidence();
}
async function requestHelper(action, request) {
  const context = helperContext();
  recordHelper(action, await request(), context);
}
function invalidateWitness() {
  el('witness').checked = false;
  el('verify').disabled = true;
  el('helper-test').disabled = true;
  verifiedVoiceURI = null;
  configureHelper();
  evidence.disconnectedAudibleStopReplayReload = 'NOT VERIFIED';
  el('capability').textContent = 'Production helper: no verified voice.';
  renderEvidence();
}
function refreshVoices() {
  const selected = el('voice').value;
  voices = (window.speechSynthesis?.getVoices() ?? []).filter(voice => voice.localService === true && /^en(?:-|$)/i.test(voice.lang));
  el('voice').replaceChildren();
  for (const voice of voices) {
    const option = document.createElement('option');
    option.value = voice.voiceURI;
    option.textContent = `${voice.name} (${voice.lang}) — local`;
    el('voice').append(option);
  }
  const zira = voices.find(voice => /^Microsoft Zira\b/i.test(voice.name));
  const retained = voices.find(voice => voice.voiceURI === selected);
  const candidate = voiceChosenByTester || verifiedVoiceURI ? retained : zira;
  el('voice').value = candidate?.voiceURI ?? '';
  el('voice-status').textContent = candidate
    ? `${candidate.name} selected as a candidate. Offline playback still needs a new witness for this voice.`
    : voices.length
      ? 'Microsoft Zira is not available as a local English voice. Refresh voices or explicitly choose another candidate; no substitute was selected.'
      : 'BLOCKER: no local English voice reported. Wait for voice loading or install an English voice through the team setup process.';
  el('test').disabled = !candidate;
  el('replay').disabled = !candidate;
  el('verify').disabled = !candidate || !el('witness').checked;
  if (selected && selected !== el('voice').value) { stopAudition(); invalidateWitness(); }
}
function stopAudition() {
  missingMediaController?.dispose();
  missingMediaController = null;
  if (clipAudition) {
    clipAudition.onended = clipAudition.onerror = null;
    clipAudition.pause();
    clipAudition.removeAttribute('src');
    clipAudition.load();
    clipAudition = null;
  }
  if (audition) {
    audition.onstart = audition.onend = audition.onerror = null;
    audition = null;
    window.speechSynthesis.cancel();
  }
  stopSpeech();
}
function auditionCandidate() {
  stopAudition();
  const voice = voices.find(candidate => candidate.voiceURI === el('voice').value);
  if (!voice || !voice.localService) return;
  const utterance = new SpeechSynthesisUtterance(sample());
  utterance.voice = voice;
  utterance.lang = voice.lang;
  audition = utterance;
  evidence.checkedAt = new Date().toISOString();
  evidence.candidateVoice = { name: voice.name, lang: voice.lang, voiceURI: voice.voiceURI, localService: voice.localService };
  evidence.candidateEvents.push('requested');
  el('result').textContent = 'Candidate requested. Confirm sound on the physical laptop.';
  utterance.onstart = () => {
    evidence.candidateEvents.push('start');
    el('result').textContent = 'Browser reported speech start. Confirm audible output.';
    renderEvidence();
  };
  utterance.onend = () => {
    audition = null;
    evidence.candidateEvents.push('end');
    el('result').textContent = 'Browser reported completion. Audible/offline quality remains witness-dependent.';
    renderEvidence();
  };
  utterance.onerror = event => {
    audition = null;
    evidence.candidateEvents.push(`error:${event.error}`);
    el('result').textContent = `Playback error: ${event.error}. This is not a speech PASS.`;
    invalidateWitness();
  };
  renderEvidence();
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

el('environment').textContent = navigator.userAgent;
el('refresh').onclick = refreshVoices;
el('voice').onchange = () => { voiceChosenByTester = true; stopAudition(); invalidateWitness(); refreshVoices(); };
el('test').onclick = auditionCandidate;
el('replay').onclick = auditionCandidate;
el('stop').onclick = () => {
  stopAudition();
  evidence.candidateEvents.push('explicit-stop');
  el('result').textContent = 'Stop requested. Confirm the sound stopped.';
  renderEvidence();
};
el('witness').onchange = () => {
  if (!el('witness').checked) invalidateWitness();
  else el('verify').disabled = !voices.some(voice => voice.voiceURI === el('voice').value);
};
el('verify').onclick = () => {
  if (!el('witness').checked || !voices.some(voice => voice.voiceURI === el('voice').value)) return;
  stopAudition();
  verifiedVoiceURI = el('voice').value;
  configureHelper();
  evidence.disconnectedAudibleStopReplayReload = 'HUMAN CONFIRMED ON THIS LAPTOP/BROWSER; record witness and device in matrix';
  el('helper-test').disabled = false;
  renderEvidence();
};
el('helper-test').onclick = async () => {
  stopAudition();
  await requestHelper('speakText', () => speakText(sample()));
};
async function playCards(ids) {
  stopAudition();
  lastCardIds = [...ids];
  await requestHelper(`speakCards:${ids.join(',')}`, () => speakCards(ids));
}
el('helper-cards').onclick = () => playCards(['want', 'eat', 'apple']);
el('helper-repeat').onclick = () => playCards(['apple', 'want', 'apple']);
el('helper-replay').onclick = () => playCards(lastCardIds);
el('fallback').onclick = () => {
  stopAudition();
  verifiedVoiceURI = null;
  configureHelper();
  recordHelper('configured explicit clips-only mode', { auditedClipCount: auditedAudio.size });
};
el('unavailable').onclick = async () => {
  stopAudition();
  unsubscribe?.();
  initializeSpeech({ vocabulary });
  unsubscribe = subscribeSpeech(state => { el('capability').textContent = JSON.stringify(state); });
  await requestHelper('unavailable speakText', () => speakText(sample()));
  await requestHelper('unavailable speakCards', () => speakCards(['apple']));
};
el('invalid').onclick = async () => {
  stopAudition();
  await requestHelper('empty text', () => speakText(''));
  await requestHelper('unknown card', () => speakCards(['unknown']));
  await requestHelper('13 cards', () => speakCards(Array(13).fill('apple')));
};
el('missing-media').onclick = async () => {
  stopAudition();
  if (auditedAudio.size !== 32) return;
  // Real missing-media response, scoped to this explicit QA controller only.
  const missingPath = '/audio/en/__qa_missing_apple.wav';
  const controller = createSpeechController({ vocabulary, availableClipIds: [...auditedAudio] }, {
    Audio: function(path) { return new Audio(path === '/audio/en/apple.wav' ? missingPath : path); },
    setTimeout, clearTimeout,
  });
  missingMediaController = controller;
  const context = helperContext(controller.getState());
  let httpStatus = null;
  try { httpStatus = (await fetch(missingPath, { cache: 'no-store' })).status; }
  catch { /* Preserve a network failure separately from the playback result. */ }
  const result = await controller.speakCards(['apple']);
  if (missingMediaController === controller) { controller.dispose(); missingMediaController = null; }
  recordHelper(`missing-media QA:${missingPath}`, result, { ...context, httpStatus });
};
el('resume-audits').onclick = () => {
  stopAudition();
  try {
    const context = humanContext();
    if (!contextComplete(context)) throw new TypeError('Enter tester/witness and device details first.');
    const restored = resumeDeviceAssetResults(vocabulary, assetManifest, context);
    for (const previous of restored) {
      const current = evidence.humanAssetResults.find(card => card.id === previous.id);
      Object.assign(current, previous);
      const controls = assetControls.get(previous.id);
      for (const kind of ['audio', 'symbol']) {
        controls[kind].select.value = previous[kind].status;
        controls[kind].notes.value = previous[kind].notes;
      }
      if (previous.audio.status === 'PASS') auditedAudio.add(previous.id); else auditedAudio.delete(previous.id);
      if (previous.symbol.status === 'PASS' && controls.pictureLoaded()) recognizedSymbols.add(previous.id);
      else recognizedSymbols.delete(previous.id);
    }
    configureHelper(); renderAuditEvidence();
    el('result').textContent = 'Restored original human asset results for this tester/device. Voice verification and offline sequence outcomes are separate.';
  } catch (error) { el('result').textContent = error.message; }
};
for (const id of ['tester', 'audit-witness', 'device', 'os', 'tested-commit', 'physically-offline']) {
  el(id).onchange = () => { evidence.humanSession = humanContext(); renderEvidence(); };
}
el('download-evidence').onclick = () => {
  evidence.humanSession = humanContext();
  const completed = evidence.humanAssetResults.flatMap(card => [card.audio, card.symbol])
    .concat(evidence.offlineFallbackResults).filter(result => result.status !== 'PENDING');
  if (completed.some(result => !contextComplete(result.context)
    || (result.status === 'FAIL' && !result.notes.trim()))) {
    el('result').textContent = 'Complete tester/device evidence and explain every FAIL before downloading.';
    return;
  }
  renderEvidence();
  const url = URL.createObjectURL(new Blob([JSON.stringify(evidence, null, 2) + '\n'], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'tanaw-speech-evidence.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};

function renderOfflineResults() {
  for (const [id, label] of [['order', 'Want -> Eat -> Apple in order'], ['repeat', 'Apple -> Want -> Apple'],
    ['stop', 'Stop interrupts clips'], ['replay', 'Replay begins the card sequence again'],
    ['reload', 'Reload and clips-only playback while disconnected'],
    ['restart', 'Browser/server restart and clips-only playback while disconnected'],
    ['missing-media', 'Missing Apple WAV reports playback_failed; no sound/false success'],
    ['full-text-unavailable', 'Clips-only full-text request reports full_text_unavailable; no automatic clips']]) {
    const result = { id, label, status: 'PENDING', notes: '', checkedAt: null, context: null };
    evidence.offlineFallbackResults.push(result);
    const row = document.createElement('label');
    const select = document.createElement('select');
    for (const status of ['PENDING', 'PASS', 'FAIL']) {
      const option = document.createElement('option'); option.value = option.textContent = status; select.append(option);
    }
    select.value = 'PENDING';
    const notes = document.createElement('input');
    notes.type = 'text'; notes.placeholder = 'Exact result, delay or failure (required for FAIL)';
    notes.onchange = () => { result.notes = notes.value; renderEvidence(); };
    const feedback = document.createElement('span');
    feedback.setAttribute('role', 'status');
    const reject = message => {
      select.value = result.status;
      feedback.textContent = message;
      el('result').textContent = message;
    };
    select.onchange = () => {
      const context = humanContext();
      const missing = [['tester', 'Tester name'], ['witness', 'Witness'],
        ['device', 'Laptop description'], ['os', 'Windows version/build'],
        ['testedCommit', 'Exact Git commit tested']].filter(([key]) => !context[key]);
      if (select.value !== 'PENDING' && missing.length) {
        reject(`At the top of this page, fill in: ${missing.map(([, label]) => label).join(', ')}. Then select this result again.`);
        return;
      }
      if (select.value !== 'PENDING' && !context.physicallyDisconnected) {
        reject('Disconnect Wi-Fi/Ethernet, then tick "I personally disconnected" at the top of this page. Select this result again afterward.');
        return;
      }
      if (select.value === 'PASS' && getSpeechState().capability !== 'cards_only') {
        reject(auditedAudio.size !== 32
          ? `Only ${auditedAudio.size}/32 audio audits are available in this page session. Use "Restore recorded asset audits for this tester/device" for your previously audited laptop, then "Use audited clips only (no text voice)".`
          : 'Click "Use audited clips only (no text voice)" above, then select this result again. Zira sentence playback is a separate test.');
        return;
      }
      result.status = select.value; result.context = context;
      result.checkedAt = result.status === 'PENDING' ? null : new Date().toISOString();
      feedback.textContent = result.status === 'PENDING' ? '' : `Recorded ${result.status} for ${context.tester}.`;
      renderEvidence();
    };
    row.append(document.createTextNode(`${label}: `), select, notes, feedback);
    el('offline-results').append(row);
  }
}

function renderAuditEvidence() {
  evidence.humanAuditedAudioIds = vocabulary.cards.filter(c => auditedAudio.has(c.id)).map(c => c.id);
  evidence.humanRecognizedSymbolIds = vocabulary.cards.filter(c => recognizedSymbols.has(c.id)).map(c => c.id);
  evidence.pictureLoadFailures = vocabulary.cards.filter(c => failedPictures.has(c.id)).map(c => c.id);
  evidence.clips = `${auditedAudio.size}/32 human-checked candidate labels; offline sequence checks separate`;
  el('asset-status').textContent = `${auditedAudio.size}/32 audio; ${recognizedSymbols.size}/32 pictures checked by tester. ${failedPictures.size}/32 pictures failed to load.`;
  renderEvidence();
}
function renderAssetAudit() {
  if (!vocabulary || !assetManifest) {
    el('asset-status').textContent = 'BLOCKER: canonical vocabulary or asset provenance did not load.';
    return;
  }
  evidence.humanAssetResults = createHumanAssetResults(vocabulary, assetManifest);
  for (const card of vocabulary.cards) {
    const audit = evidence.humanAssetResults.find(result => result.id === card.id);
    const controls = {};
    assetControls.set(card.id, controls);
    const box = document.createElement('div');
    box.className = 'asset';
    const picture = document.createElement('div');
    const pictureStatus = document.createElement('p');
    pictureStatus.setAttribute('role', 'status');
    const retry = document.createElement('button');
    retry.textContent = `Retry picture: ${card.label}`;
    const open = document.createElement('a');
    open.href = `/${card.symbol_path}`;
    open.textContent = `Open ${card.label} picture directly`;
    let pictureCheck;
    let pictureLoaded = false;
    controls.pictureLoaded = () => pictureLoaded;
    const loadPicture = () => {
      const img = document.createElement('img');
      img.width = img.height = 96;
      img.alt = card.label;
      pictureStatus.textContent = `Loading ${card.label} picture...`;
      pictureLoaded = false;
      if (pictureCheck) pictureCheck.disabled = true;
      img.onload = () => {
        if (picture.firstChild !== img) return;
        failedPictures.delete(card.id);
        pictureLoaded = true;
        if (audit.symbol.status === 'PASS') recognizedSymbols.add(card.id);
        pictureStatus.textContent = '';
        pictureCheck.disabled = false;
        renderAuditEvidence();
      };
      img.onerror = () => {
        if (picture.firstChild !== img) return;
        pictureLoaded = false;
        failedPictures.add(card.id);
        recognizedSymbols.delete(card.id);
        if (audit.symbol.status === 'PASS') {
          audit.symbol.status = 'PENDING'; audit.symbol.checkedAt = null;
          pictureCheck.value = 'PENDING';
        }
        pictureCheck.disabled = false; // A tester can report FAIL; PASS remains guarded below.
        pictureStatus.textContent = `${card.label} picture failed to load. Retry or open the picture directly.`;
        renderAuditEvidence();
      };
      picture.replaceChildren(img);
      img.src = `/${card.symbol_path}`;
    };
    retry.onclick = loadPicture;
    const button = document.createElement('button');
    button.textContent = `Play candidate: ${card.label}`;
    button.onclick = () => {
      stopAudition();
      const context = { ...helperContext(), playbackMode: 'candidate_wav', verifiedVoiceURI: null };
      const audio = new Audio(`/${card.audio_path}`);
      clipAudition = audio;
      audio.onended = () => {
        if (clipAudition !== audio) return;
        stopAudition();
        recordHelper(`candidate WAV:${card.id}`, { browserEnded: true, humanAudibility: 'not inferred' }, context);
      };
      const failed = () => {
        if (clipAudition !== audio) return;
        stopAudition();
        recordHelper(`candidate WAV:${card.id}`, { error: 'playback_failed' }, context);
      };
      audio.onerror = failed;
      audio.play().catch(failed);
    };
    box.append(picture, pictureStatus, retry, open, button);
    for (const [set, text, kind] of [[auditedAudio, 'Audio: exact understandable label', 'audio'],
      [recognizedSymbols, 'Picture: recognizable correct meaning', 'symbol']]) {
      const label = document.createElement('label');
      const input = document.createElement('select');
      for (const status of ['PENDING', 'PASS', 'FAIL']) {
        const option = document.createElement('option'); option.value = option.textContent = status; input.append(option);
      }
      input.value = 'PENDING';
      if (set === recognizedSymbols) { pictureCheck = input; input.disabled = true; }
      const notes = document.createElement('input');
      controls[kind] = { select: input, notes };
      notes.type = 'text'; notes.placeholder = 'Unclear word or ambiguous meaning (required for FAIL)';
      notes.onchange = () => { audit[kind].notes = notes.value; renderEvidence(); };
      input.onchange = () => {
        const context = humanContext();
        if (input.value !== 'PENDING' && (!contextComplete(context)
          || (kind === 'symbol' && input.value === 'PASS' && !pictureLoaded))) {
          input.value = audit[kind].status;
          el('result').textContent = 'Enter tester/device details first. A picture must load before a human can mark it PASS.';
          return;
        }
        audit[kind].status = input.value;
        audit[kind].checkedAt = input.value === 'PENDING' ? null : new Date().toISOString();
        audit[kind].context = context;
        if (input.value === 'PASS') set.add(card.id); else set.delete(card.id);
        stopAudition();
        configureHelper();
        renderAuditEvidence();
      };
      label.append(document.createTextNode(`${card.label}: ${text} `), input, notes);
      box.append(label);
    }
    el('asset-audit').append(box);
    loadPicture();
  }
  renderAuditEvidence();
}
window.speechSynthesis?.addEventListener('voiceschanged', refreshVoices);
window.addEventListener('pagehide', stopAudition);
try {
  const response = await fetch('/vocabulary.json');
  if (response.ok) vocabulary = await response.json();
  const manifestResponse = await fetch('/speech-assets.json');
  if (manifestResponse.ok) assetManifest = await manifestResponse.json();
} catch { /* Standalone sentence testing does not require the board. */ }
invalidateWitness();
refreshVoices();
renderAssetAudit();
renderOfflineResults();
