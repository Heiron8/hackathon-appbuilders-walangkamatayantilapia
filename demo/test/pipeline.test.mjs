import {test} from 'node:test';
import assert from 'node:assert/strict';
import {validateStoryboard, safeURL} from '../storyboard.mjs';
import {checkMetadata, exec, ffmpeg, validateVideo} from '../media.mjs';
import {narrateScene} from '../narration.mjs';
import {mkdtemp, rm, writeFile} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {produce} from '../cli.mjs';
import {captionCues, cameraState} from '../editorial.mjs';
import {renderFFmpeg} from '../render.mjs';

function board() {
  return {mode: 'rehearsal', title: 'Generic sample', build: {id: 'fixture'},
    scenes: [{id: 'sample', kind: 'title', duration: 25, caption: 'A real sample.', narration: '',
      status: 'VERIFIED', evidence: ['fixture assertions']}]};
}
test('valid rehearsal and final build evidence; unsafe/unreviewed footage fails closed', () => {
  assert.equal(validateStoryboard(board()), 25);
  const final = board(); final.mode = 'final';
  assert.throws(() => validateStoryboard(final), /integrated build/);
  final.build.integrated = true; final.build.verification = ['dated runtime results'];
  assert.throws(() => validateStoryboard(final), /review references/);
  final.build.review = ['independent review']; final.privacyReviewed = true;
  final.scenes = Array.from({length: 3}, (_, i) => ({...final.scenes[0], id: `scene-${i}`, duration: 20}));
  assert.equal(validateStoryboard(final), 60);
  final.scenes[0].status = 'NOT SAFE TO DEMONSTRATE';
  assert.throws(() => validateStoryboard(final), /unsafe/);
});
test('warnings cannot be hidden and IDs cannot overwrite scene files', () => {
  const value = board(); value.scenes[0].status = 'DEMONSTRABLE WITH WARNING';
  assert.throws(() => validateStoryboard(value), /visible warning/);
  value.scenes[0].warning = 'Local demo data only';
  assert.equal(validateStoryboard(value), 25);
  value.scenes[0].id = '../escape';
  assert.throws(() => validateStoryboard(value), /safe filenames/);
  delete value.scenes[0].id;
  assert.throws(() => validateStoryboard(value), /safe filenames/);
});
test('capture requires stable readiness and observable outcome assertions', () => {
  const value = board(); const scene = value.scenes[0];
  Object.assign(scene, {kind: 'capture', url: 'http://127.0.0.1:3000', ready: 'h1',
    actions: [{type: 'click', selector: 'button'}]});
  assert.throws(() => validateStoryboard(value), /result assertion/);
  scene.actions.push({type: 'assertText', selector: '#result', value: 'Done'});
  assert.equal(validateStoryboard(value), 25);
  scene.actions.push({type: 'eval', selector: 'body'});
  assert.throws(() => validateStoryboard(value), /unsupported action/);
  assert.throws(() => safeURL('https://user:example@localhost/'), /credentials/);
  assert.throws(() => safeURL('https://localhost/?token=example'), /credentials/);
  assert.throws(() => safeURL('file:///tmp/index.html'), /HTTP/);
});
test('metadata rejects wrong codec, duration and absent narration stream', () => {
  const metadata = {format: {duration: '25'}, streams: [{codec_type: 'video', codec_name: 'h264', width: 1280, height: 720}]};
  checkMetadata(metadata, 25, false);
  assert.throws(() => checkMetadata(metadata, 25, true), /audio stream/);
  assert.throws(() => checkMetadata(metadata, 30, false), /duration/);
  metadata.streams[0].codec_name = 'vp8';
  assert.throws(() => checkMetadata(metadata, 25, false), /H.264/);
});
test('captions-only and manual missing-audio behavior is explicit', async () => {
  assert.equal((await narrateScene({narration: 'Hello'}, '.', '.', 'none')).provider, 'captions-only');
  await assert.rejects(narrateScene({id: 'sample', narration: 'Hello'}, '.', '.', 'manual'), /requires a scene.audio path/);
});
test('real supplied audio is probed and overlong narration is rejected', async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'demo-audio-test-'));
  try {
    await exec(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3', path.join(directory, 'manual.wav')]);
    const scene = {id: 'sample', narration: 'Manual voice test', audio: 'manual.wav', duration: 4};
    const result = await narrateScene(scene, directory, directory, 'manual');
    assert.equal(result.provider, 'manual/local replacement');
    assert.ok(result.duration > 2.9 && result.duration < 3.1);
    scene.narrationStart = 0.4;
    assert.equal((await narrateScene(scene, directory, directory, 'manual')).start, 0.4);
    scene.narrationStart = 1;
    await assert.rejects(narrateScene(scene, directory, directory, 'manual'), /exceeds scene/);
    delete scene.narrationStart;
    scene.duration = 3;
    await assert.rejects(narrateScene(scene, directory, directory, 'manual'), /exceeds scene/);
  } finally {await rm(directory, {recursive: true, force: true});}
});
test('editorial options preserve legacy stories and reject unsafe crops or overlapping captions', () => {
  const value = board(), scene = value.scenes[0];
  assert.equal(captionCues(scene)[0].text, scene.caption);
  Object.assign(scene, {card: 'outro', heading: 'The result', narrationStart: 0.4,
    captions: [{text: 'One clear result.', start: 0.4, end: 4}]});
  assert.equal(validateStoryboard(value), 25);
  scene.captions.push({text: 'Too much at once.', start: 3, end: 5});
  assert.throws(() => validateStoryboard(value), /non-overlapping/);
  delete scene.captions; delete scene.card;
  Object.assign(scene, {kind: 'manual', media: 'sample.mp4', camera: {scale: 1.09, x: 0.5, y: 0.5, start: 2, end: 5}});
  assert.throws(() => validateStoryboard(value), /camera/);
  scene.camera.scale = 1.06;
  assert.equal(validateStoryboard(value), 25);
  scene.actions = [{pauseAfter: 3}];
  assert.throws(() => validateStoryboard(value), /pauseAfter/);
});
test('camera is stationary during early actions and only eases to the bounded focus', () => {
  const camera = {scale: 1.06, x: 0.3, y: 0.6, start: 3, end: 5};
  assert.equal(cameraState(camera, 2).scale, 1);
  assert.equal(cameraState(camera, 3).scale, 1);
  assert.ok(cameraState(camera, 4).scale > 1 && cameraState(camera, 4).scale < 1.06);
  assert.equal(cameraState(camera, 6).scale, 1.06);
  assert.equal(cameraState(null, 10).scale, 1);
});
test('FFmpeg preserves the configured narration delay in actual rendered audio', async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'demo-offset-test-'));
  try {
    await exec(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1', path.join(directory, 'tone.wav')]);
    const output = path.join(directory, 'probe.mp4');
    await renderFFmpeg({title: 'Timing check', scenes: [{id: 'timing', duration: 3, caption: 'Audio follows the pause.',
      audio: 'tone.wav', narrationStart: 0.4}]}, directory, output);
    await validateVideo(output, 3, true);
    const {stdout} = await exec(ffmpeg, ['-v', 'error', '-i', output, '-ac', '1', '-ar', '8000', '-f', 's16le', '-'], {encoding: 'buffer'});
    const average = (start, end) => {
      let total = 0;
      for (let index = start; index < end; index++) total += Math.abs(stdout.readInt16LE(index * 2));
      return total / (end - start);
    };
    assert.ok(average(0, 2400) < 2, 'The first 0.3 seconds should be silent');
    assert.ok(average(4000, 8000) > 100, 'Narration should be audible after its offset');
  } finally {await rm(directory, {recursive: true, force: true});}
});
test('existing run evidence cannot be overwritten', async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'demo-test-'));
  try {
    const storyboard = path.join(directory, 'storyboard.json');
    await writeFile(storyboard, JSON.stringify(board()));
    await assert.rejects(produce(storyboard, {out: directory}), /EEXIST/);
  } finally {await rm(directory, {recursive: true, force: true});}
});
