import {parseArgs} from 'node:util';
import {access, copyFile, mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {loadStoryboard} from './storyboard.mjs';
import {browserPath, captureScene} from './capture.mjs';
import {contactSheet, convertClip, exec, ffmpeg, ffprobe, probe, validateVideo} from './media.mjs';
import {narrateScene} from './narration.mjs';
import {renderFFmpeg, renderRemotion} from './render.mjs';
import {captionCues} from './editorial.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
export async function produce(filename, {out, tts = 'auto', renderer = 'auto'} = {}) {
  if (!['auto', 'windows', 'none', 'manual'].includes(tts)) throw new Error('Unknown TTS provider');
  if (!['auto', 'remotion', 'ffmpeg'].includes(renderer)) throw new Error('Unknown renderer');
  const {board, directory: sourceDirectory} = await loadStoryboard(filename);
  const directory = path.resolve(out ?? path.join(here, 'output', `run-${Date.now()}`));
  await mkdir(path.dirname(directory), {recursive: true});
  await mkdir(directory); // Fail closed on an existing run: never overwrite stale evidence.
  await copyFile(filename, path.join(directory, 'storyboard.json'));
  const capture = [], narration = [], scenes = [];
  try {
    for (const scene of board.scenes) {
      console.log(`Preparing scene ${scene.id}`);
      const composed = {...scene};
      if (scene.kind === 'capture') {
        const result = await captureScene(scene, board, directory);
        composed.media = result.media;
        capture.push(result.evidence);
      } else if (scene.kind === 'manual') {
        const source = path.resolve(sourceDirectory, scene.media);
        const metadata = await probe(source);
        if (Number(metadata.format.duration) < scene.duration) throw new Error(`${scene.id}: manual footage is too short`);
        composed.media = `${scene.id}.mp4`;
        await convertClip(source, path.join(directory, composed.media), scene.duration);
        capture.push({id: scene.id, source, assertions: 'NOT AUTOMATED; human footage review required', build: board.build.id});
      }
      const voice = await narrateScene(scene, directory, sourceDirectory, tts);
      composed.audio = voice.audio;
      narration.push({id: scene.id, ...voice});
      if (voice.warning) console.warn(`${scene.id}: ${voice.warning}`);
      scenes.push(composed);
    }
    const composedBoard = {...board, scenes};
    const output = path.join(directory, 'demo.mp4');
    let selectedRenderer = renderer;
    if (renderer === 'ffmpeg') await renderFFmpeg(composedBoard, directory, output);
    else {
      try {
        await renderRemotion(composedBoard, directory, output);
        selectedRenderer = 'remotion';
      } catch (error) {
        if (renderer !== 'auto') throw error;
        await writeFile(path.join(directory, 'remotion-error.txt'), String(error.stack ?? error));
        console.warn('Remotion failed; exercising FFmpeg fallback. See remotion-error.txt.');
        await renderFFmpeg(composedBoard, directory, output);
        selectedRenderer = 'ffmpeg-fallback';
      }
    }
    const duration = scenes.reduce((sum, scene) => sum + scene.duration, 0);
    const validation = await validateVideo(output, duration, narration.some(n => n.audio));
    const reviewFrames = await contactSheet(output, directory, scenes);
    const report = {checkedAt: new Date().toISOString(), mode: board.mode, build: board.build, output,
      renderer: selectedRenderer, capture, narration, validation, reviewFrames,
      sceneClaims: scenes.map(({id, status, evidence, warning}) => ({id, status, evidence, warning})),
      editorial: scenes.map(scene => ({id: scene.id, card: scene.card, heading: scene.heading,
        camera: scene.camera, captions: captionCues(scene), narrationStart: scene.narrationStart ?? 0})),
      humanReview: 'NOT READY: inspect full playback for readable text, audio synchronization, truthful claims and private data; record independent reviewer evidence',
      submissionReadiness: 'Supply this evidence to docs/qa/submission-readiness.md. Rehearsal is not product/submission evidence.'};
    await writeFile(path.join(directory, 'evidence.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify({output, renderer: selectedRenderer, validation, evidence: path.join(directory, 'evidence.json')}, null, 2));
    return report;
  } catch (error) {
    await writeFile(path.join(directory, 'failure.txt'), String(error.stack ?? error));
    throw error;
  }
}
async function doctor() {
  for (const [name, executable] of [['Chromium', browserPath()], ['FFmpeg', ffmpeg], ['FFprobe', ffprobe]]) {
    try {await access(executable); console.log(`${name}: available (${executable})`);}
    catch {console.log(`${name}: MISSING (${executable}); see demo/README.md`); process.exitCode = 1;}
  }
  for (const binary of [ffmpeg, ffprobe]) {
    const {stdout} = await exec(binary, ['-version']);
    console.log(stdout.split('\n')[0]);
  }
  console.log(`Node: ${process.version}; Remotion and Playwright imported successfully`);
  if (process.platform === 'win32') {
    const {stdout} = await exec('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command',
      'Add-Type -AssemblyName System.Speech; $demoVoice = New-Object System.Speech.Synthesis.SpeechSynthesizer; $demoVoice.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }; $demoVoice.Dispose()']);
    console.log(`Local SAPI voices: ${stdout.trim()}`);
  } else console.log('Local SAPI: unavailable; use manual/local generated audio or captions-only');
}
async function main() {
  const {positionals, values} = parseArgs({allowPositionals: true, options: {
    storyboard: {type: 'string'}, out: {type: 'string'}, tts: {type: 'string'}, renderer: {type: 'string'}, video: {type: 'string'}}});
  const [command] = positionals;
  if (command === 'doctor') return doctor();
  if (!values.storyboard) throw new Error('Usage: node demo/cli.mjs produce --storyboard <json> [--tts auto|windows|manual|none] [--renderer auto|remotion|ffmpeg] [--out <new-directory>]\nOr: validate --storyboard <json> --video <mp4>');
  if (command === 'produce') return produce(values.storyboard, values);
  if (command === 'validate' && values.video) {
    const {board} = await loadStoryboard(values.storyboard);
    console.log(await validateVideo(values.video, board.scenes.reduce((sum, s) => sum + s.duration, 0), false));
    return;
  }
  throw new Error('Unknown command or missing --video');
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => {console.error(error.message); process.exitCode = 1;});
}
