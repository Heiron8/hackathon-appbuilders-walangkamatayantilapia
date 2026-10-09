import { initializeSpeech, speakText, speakCards, stopSpeech, subscribeSpeech } from '/speech/index.mjs';

const sample = () => el('sample').value;
const el = id => document.getElementById(id);
let voices = [];
let audition = null;
let vocabulary = null;
let unsubscribe = null;
let clipAudition = null;
let verifiedVoiceURI = null;
let lastCardIds = ['want', 'eat', 'apple'];
const auditedAudio = new Set();
const recognizedSymbols = new Set();
const evidence = {
  browser: navigator.userAgent,
  connectedHint: navigator.onLine,
  checkedAt: null,
  candidateVoice: null,
  candidateEvents: [],
  disconnectedAudibleStopReplayReload: 'NOT VERIFIED',
  clips: 'NOT VERIFIED',
  integratedProduct: 'NOT VERIFIED',
  helperEvents: [],
  humanAuditedAudioIds: [],
  humanRecognizedSymbolIds: [],
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
  if (voices.some(voice => voice.voiceURI === selected)) el('voice').value = selected;
  el('voice-status').textContent = voices.length ? `${voices.length} local English candidate(s). Offline playback still needs a witness.` : 'BLOCKER: no local English voice reported. Wait for voice loading or install an English voice through the team setup process.';
  el('test').disabled = voices.length === 0;
  el('replay').disabled = voices.length === 0;
  if (selected && selected !== el('voice').value) invalidateWitness();
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
el('voice').onchange = () => { stopAudition(); invalidateWitness(); };
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
  else el('verify').disabled = voices.length === 0;
};
el('verify').onclick = () => {
  if (!el('witness').checked) return;
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

function renderAssetAudit() {
  if (!vocabulary) return;
  for (const card of vocabulary.cards) {
    const box = document.createElement('div');
    box.className = 'asset';
    const img = document.createElement('img');
    img.src = `/${card.symbol_path}`;
    img.alt = card.label;
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
    box.append(img, button);
    for (const [set, text] of [[auditedAudio, 'I heard the exact label clearly'],
      [recognizedSymbols, 'I recognize this picture meaning']]) {
      const label = document.createElement('label');
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.onchange = () => {
        if (input.checked) set.add(card.id); else set.delete(card.id);
        evidence.humanAuditedAudioIds = vocabulary.cards.filter(c => auditedAudio.has(c.id)).map(c => c.id);
        evidence.humanRecognizedSymbolIds = vocabulary.cards.filter(c => recognizedSymbols.has(c.id)).map(c => c.id);
        evidence.clips = `${auditedAudio.size}/32 human-checked candidate labels; offline sequence checks separate`;
        el('asset-status').textContent = `${auditedAudio.size}/32 audio; ${recognizedSymbols.size}/32 pictures checked by tester.`;
        stopAudition();
        configureHelper();
        renderEvidence();
      };
      label.append(input, document.createTextNode(` ${card.label}: ${text}`));
      box.append(label);
    }
    el('asset-audit').append(box);
  }
  el('asset-status').textContent = '0/32 audio; 0/32 pictures human-audited. Play candidates explicitly.';
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
