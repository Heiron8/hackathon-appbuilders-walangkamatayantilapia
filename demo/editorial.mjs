// Small shared timing contract for Remotion, FFmpeg and storyboard validation.
export function smoothProgress(seconds, start, end) {
  const t = Math.max(0, Math.min(1, (seconds - start) / (end - start)));
  return t * t * (3 - 2 * t);
}
export function captionCues(scene) {
  return scene.captions ?? [{text: scene.caption, start: scene.narrationStart ?? 0, end: scene.duration - 0.15}];
}
export function cameraState(camera, seconds) {
  if (!camera) return {scale: 1, x: 0.5, y: 0.5};
  const progress = smoothProgress(seconds, camera.start, camera.end);
  return {scale: 1 + (camera.scale - 1) * progress, x: camera.x, y: camera.y};
}
export function validateEditorial(scene) {
  const requireValue = (ok, message) => {if (!ok) throw new Error(`${scene.id}: ${message}`);};
  for (const key of ['leadIn', 'narrationStart']) {
    if (scene[key] !== undefined) requireValue(Number.isFinite(scene[key]) && scene[key] >= 0 &&
      scene[key] <= 3 && scene[key] < scene.duration - 0.3, `${key} must fit the scene (0-3 seconds)`);
  }
  if (scene.card !== undefined) requireValue(scene.kind === 'title' && ['intro', 'outro'].includes(scene.card), 'card must be intro or outro on a title scene');
  for (const key of ['heading', 'eyebrow']) {
    if (scene[key] !== undefined) requireValue(typeof scene[key] === 'string' && scene[key].trim().length > 0 &&
      scene[key].length <= 80, `${key} must contain 1-80 characters`);
  }
  if (scene.camera) {
    const {scale, x, y, start, end} = scene.camera;
    requireValue(scene.kind !== 'title' && [scale, x, y, start, end].every(Number.isFinite) &&
      scale >= 1 && scale <= 1.08 && x >= 0 && x <= 1 && y >= 0 && y <= 1 &&
      start >= 0 && end > start && end <= scene.duration, 'camera requires scale 1-1.08, normalized focus and an in-scene interval');
  }
  if (scene.captions !== undefined) {
    requireValue(Array.isArray(scene.captions) && scene.captions.length > 0 && scene.captions.length <= 8, 'captions must contain 1-8 timed phrases');
    let previousEnd = 0;
    for (const cue of scene.captions) {
      requireValue(typeof cue.text === 'string' && cue.text.trim().length > 0 && cue.text.length <= 100 &&
        Number.isFinite(cue.start) && Number.isFinite(cue.end) && cue.start >= previousEnd &&
        cue.end - cue.start >= 0.6 && cue.end <= scene.duration, 'caption phrases must be readable, non-overlapping and inside the scene');
      previousEnd = cue.end;
    }
  }
  for (const action of scene.actions ?? []) {
    if (action.pauseAfter !== undefined) requireValue(Number.isFinite(action.pauseAfter) &&
      action.pauseAfter >= 0 && action.pauseAfter <= 2, 'pauseAfter must be 0-2 seconds of presentation pacing');
  }
}
