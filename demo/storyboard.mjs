import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {validateEditorial} from './editorial.mjs';

export const FPS = 30;
export const SIZE = {width: 1280, height: 720};
export const VIEWPORT = {width: 1280, height: 640};
const statuses = ['VERIFIED', 'DEMONSTRABLE WITH WARNING'];
const actions = ['fill', 'click', 'press', 'check', 'assertVisible', 'assertText'];
function requireValue(ok, message) {if (!ok) throw new Error(message);}
function text(value) {return typeof value === 'string' && value.trim().length > 0;}
export function safeURL(value) {
  const url = new URL(value);
  requireValue(['http:', 'https:'].includes(url.protocol) && !url.username && !url.password,
    'Capture URLs must be HTTP(S) without embedded credentials');
  requireValue(![...url.searchParams.keys()].some(key => /token|secret|password|api.?key/i.test(key)),
    'Do not put credentials in capture URLs');
  return url.href;
}
export function validateStoryboard(board) {
  requireValue(['rehearsal', 'final'].includes(board.mode), 'mode must be rehearsal or final');
  requireValue(text(board.title) && board.title.length <= 80, 'title must contain 1-80 characters');
  requireValue(text(board.build?.id), 'An identified build is required');
  if (board.mode === 'final') {
    requireValue(board.build.integrated === true, 'Final footage requires an integrated build');
    for (const key of ['verification', 'review']) {
      requireValue(Array.isArray(board.build[key]) && board.build[key].length > 0 && board.build[key].every(text),
        `Final build requires ${key} references`);
    }
    requireValue(board.privacyReviewed === true, 'Review sanitized capture data before final recording');
  }
  requireValue(Array.isArray(board.scenes) && board.scenes.length > 0, 'scenes are required');
  const ids = new Set();
  for (const scene of board.scenes) {
    requireValue(text(scene.id) && /^[a-z0-9-]+$/.test(scene.id) && !ids.has(scene.id), 'Scene IDs must be unique safe filenames');
    ids.add(scene.id);
    requireValue(['title', 'capture', 'manual'].includes(scene.kind), `${scene.id}: unknown scene kind`);
    requireValue(Number.isInteger(scene.duration) && scene.duration >= 3 && scene.duration <= 30,
      `${scene.id}: duration must be an integer from 3 to 30 seconds`);
    requireValue(text(scene.caption) && scene.caption.length <= 140, `${scene.id}: caption must contain 1-140 characters`);
    requireValue(typeof scene.narration === 'string', `${scene.id}: narration must be text (empty for silence)`);
    requireValue(statuses.includes(scene.status), `${scene.id}: unsafe or missing evidence classification`);
    requireValue(Array.isArray(scene.evidence) && scene.evidence.length > 0 && scene.evidence.every(text),
      `${scene.id}: verification references are required`);
    validateEditorial(scene);
    if (scene.status === 'DEMONSTRABLE WITH WARNING') {
      requireValue(text(scene.warning) && scene.warning.length <= 100, `${scene.id}: visible warning is required`);
    }
    if (scene.highlight) {
      const {x, y, width, height} = scene.highlight;
      requireValue([x, y, width, height].every(Number.isFinite) && x >= 0 && y >= 0 && width > 0 && height > 0 &&
        x + width <= 1 && y + height <= 1, `${scene.id}: highlight must be a normalized rectangle`);
    }
    if (scene.kind === 'manual') requireValue(text(scene.media), `${scene.id}: manual recording path required`);
    if (scene.kind === 'capture') {
      safeURL(scene.url ?? board.baseURL);
      requireValue(text(scene.ready), `${scene.id}: stable ready selector required`);
      requireValue(Array.isArray(scene.actions) && scene.actions.length > 0, `${scene.id}: actions required`);
      for (const action of scene.actions) {
        requireValue(actions.includes(action.type) && text(action.selector), `${scene.id}: unsupported action or selector`);
        if (['fill', 'press', 'assertText'].includes(action.type)) {
          requireValue(typeof action.value === 'string', `${scene.id}: action value required`);
        }
      }
      requireValue(scene.actions.some(a => ['assertText', 'assertVisible'].includes(a.type)),
        `${scene.id}: a result assertion is required`);
    }
  }
  const duration = board.scenes.reduce((sum, scene) => sum + scene.duration, 0);
  const [min, max] = board.mode === 'rehearsal' ? [20, 30] : [60, 120];
  requireValue(duration >= min && duration <= max, `${board.mode}: total duration must be ${min}-${max} seconds`);
  return duration;
}
export async function loadStoryboard(filename) {
  const board = JSON.parse(await readFile(filename, 'utf8'));
  validateStoryboard(board);
  return {board, directory: path.dirname(path.resolve(filename))};
}
