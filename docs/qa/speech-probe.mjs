import { initializeSpeech, speakText, speakCards, stopSpeech, subscribeSpeech } from '/speech/index.mjs';

const sample = () => el('sample').value;
const el = id => document.getElementById(id);
let voices = [];
let audition = null;
let vocabulary = null;
let unsubscribe = null;
let clipAudition = null;
let verifiedVoiceURI = null;
let voiceChosenByTester = false;
let lastCardIds = ['want', 'eat', 'apple'];
const auditedAudio = new Set();
const recognizedSymbols = new Set();
const failedPictures = new Set();
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
};

function renderEvidence() { el('evidence').textContent = JSON.stringify(evidence, null, 2); }
function configureHelper() {
  unsubscribe?.();
  initializeSpeech({ vocabulary, verifiedVoiceURI,
    availableClipIds: [...auditedAudio] });
  unsubscribe = subscribeSpeech(state => { el('capability').textContent = JSON.stringify(state); });
  el('helper-test').disabled = false; // Unavailable/error mode must also be testable.
  const canSpeakCards = Boolean(verifiedVoiceURI) || auditedAudio.size === 32;
  for (const id of ['helper-cards', 'helper-repeat', 'helper-replay']) el(id).disabled = !canSpeakCards;
  el('fallback').disabled = auditedAudio.size !== 32;
}
function recordHelper(action, result) {
  evidence.helperEvents.push({ action, result, at: new Date().toISOString() });
  el('result').textContent = JSON.stringify(result);
  renderEvidence();
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
  recordHelper('speakText', await speakText(sample()));
};
async function playCards(ids) {
  stopAudition();
  lastCardIds = [...ids];
  recordHelper(`speakCards:${ids.join(',')}`, await speakCards(ids));
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
  recordHelper('unavailable speakText', await speakText(sample()));
  recordHelper('unavailable speakCards', await speakCards(['apple']));
};
el('invalid').onclick = async () => {
  stopAudition();
  recordHelper('empty text', await speakText(''));
  recordHelper('unknown card', await speakCards(['unknown']));
  recordHelper('13 cards', await speakCards(Array(13).fill('apple')));
};

function renderAuditEvidence() {
  evidence.humanAuditedAudioIds = vocabulary.cards.filter(c => auditedAudio.has(c.id)).map(c => c.id);
  evidence.humanRecognizedSymbolIds = vocabulary.cards.filter(c => recognizedSymbols.has(c.id)).map(c => c.id);
  evidence.pictureLoadFailures = vocabulary.cards.filter(c => failedPictures.has(c.id)).map(c => c.id);
  evidence.clips = `${auditedAudio.size}/32 human-checked candidate labels; offline sequence checks separate`;
  el('asset-status').textContent = `${auditedAudio.size}/32 audio; ${recognizedSymbols.size}/32 pictures checked by tester. ${failedPictures.size}/32 pictures failed to load.`;
  renderEvidence();
}
function renderAssetAudit() {
  if (!vocabulary) return;
  for (const card of vocabulary.cards) {
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
    const loadPicture = () => {
      const img = document.createElement('img');
      img.width = img.height = 96;
      img.alt = card.label;
      pictureStatus.textContent = `Loading ${card.label} picture...`;
      if (pictureCheck) pictureCheck.disabled = true;
      img.onload = () => {
        if (picture.firstChild !== img) return;
        failedPictures.delete(card.id);
        pictureStatus.textContent = '';
        pictureCheck.disabled = false;
        renderAuditEvidence();
      };
      img.onerror = () => {
        if (picture.firstChild !== img) return;
        failedPictures.add(card.id);
        recognizedSymbols.delete(card.id);
        pictureCheck.checked = false;
        pictureCheck.disabled = true;
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
      const audio = new Audio(`/${card.audio_path}`);
      clipAudition = audio;
      audio.onended = () => {
        if (clipAudition !== audio) return;
        stopAudition();
        recordHelper(`candidate WAV:${card.id}`, { browserEnded: true, humanAudibility: 'not inferred' });
      };
      const failed = () => {
        if (clipAudition !== audio) return;
        stopAudition();
        recordHelper(`candidate WAV:${card.id}`, { error: 'playback_failed' });
      };
      audio.onerror = failed;
      audio.play().catch(failed);
    };
    box.append(picture, pictureStatus, retry, open, button);
    for (const [set, text] of [[auditedAudio, 'I heard the exact label clearly'],
      [recognizedSymbols, 'I recognize this picture meaning']]) {
      const label = document.createElement('label');
      const input = document.createElement('input');
      input.type = 'checkbox';
      if (set === recognizedSymbols) { pictureCheck = input; input.disabled = true; }
      input.onchange = () => {
        if (input.checked) set.add(card.id); else set.delete(card.id);
        stopAudition();
        configureHelper();
        renderAuditEvidence();
      };
      label.append(input, document.createTextNode(` ${card.label}: ${text}`));
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
} catch { /* Standalone sentence testing does not require the board. */ }
invalidateWitness();
refreshVoices();
renderAssetAudit();
