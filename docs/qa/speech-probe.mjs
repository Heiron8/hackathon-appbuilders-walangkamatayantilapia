import { initializeSpeech, speakText, stopSpeech, subscribeSpeech } from '/speech/index.mjs';

const sample = 'I want to eat an apple.';
const el = id => document.getElementById(id);
let voices = [];
let audition = null;
let vocabulary = null;
let unsubscribe = null;
const evidence = {
  browser: navigator.userAgent,
  connectedHint: navigator.onLine,
  checkedAt: null,
  candidateVoice: null,
  candidateEvents: [],
  disconnectedAudibleStopReplayReload: 'NOT VERIFIED',
  clips: 'NOT VERIFIED',
  integratedProduct: 'NOT VERIFIED',
};

function renderEvidence() { el('evidence').textContent = JSON.stringify(evidence, null, 2); }
function invalidateWitness() {
  el('witness').checked = false;
  el('verify').disabled = true;
  el('helper-test').disabled = true;
  unsubscribe?.();
  unsubscribe = null;
  initializeSpeech({ vocabulary });
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
  const utterance = new SpeechSynthesisUtterance(sample);
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
  unsubscribe?.();
  initializeSpeech({ vocabulary, verifiedVoiceURI: el('voice').value });
  evidence.disconnectedAudibleStopReplayReload = 'HUMAN CONFIRMED ON THIS LAPTOP/BROWSER; record witness and device in matrix';
  unsubscribe = subscribeSpeech(state => { el('capability').textContent = JSON.stringify(state); });
  el('helper-test').disabled = false;
  renderEvidence();
};
el('helper-test').onclick = async () => {
  const result = await speakText(sample);
  el('result').textContent = JSON.stringify(result);
};
window.speechSynthesis?.addEventListener('voiceschanged', refreshVoices);
window.addEventListener('pagehide', stopAudition);
try {
  const response = await fetch('/vocabulary.json');
  if (response.ok) vocabulary = await response.json();
} catch { /* Standalone sentence testing does not require the board. */ }
invalidateWitness();
refreshVoices();
