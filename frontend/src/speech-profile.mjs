// Explicit device-specific build opt-in; default and unknown profiles stay unavailable.
// loq-zira applies only to the audited LOQ / Windows 11 / Chrome 154 setup:
// https://github.com/Heiron8/hackathon-appbuilders-walangkamatayantilapia/blob/3fd47c076aad4c5ec4abeb2ef04bdc857eda8ca7/docs/qa/evidence/2026-10-10-loq-assets.json
// That evidence confirms the local voice's disconnected audible stop/replay/reload
// check. Integrated Tanaw playback still needs its own physical-device check.
// Discovery or this profile name does not certify a different device/browser.
export function selectSpeechProfile(profile) {
  return Object.freeze({
    verifiedVoiceURI: profile === 'loq-zira' ? 'Microsoft Zira - English (United States)' : null,
    // Bundled fallback recordings have not merged or passed their readiness gate.
    availableClipIds: Object.freeze([]),
  });
}

export const verifiedSpeechProfile = selectSpeechProfile(import.meta.env?.VITE_TANAW_SPEECH_PROFILE);
