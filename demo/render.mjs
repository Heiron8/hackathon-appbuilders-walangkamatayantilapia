import {copyFile, mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
import {browserPath} from './capture.mjs';
import {exec, ffmpeg} from './media.mjs';
import {captionCues} from './editorial.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
export async function renderRemotion(board, directory, output) {
  // Public assets must be a separate leaf, never an ancestor of bundle output.
  const assets = path.join(directory, 'assets');
  await mkdir(assets);
  for (const scene of board.scenes) {
    for (const filename of [scene.media, scene.audio].filter(Boolean)) {
      await copyFile(path.join(directory, filename), path.join(assets, filename));
    }
  }
  const serveUrl = await bundle({entryPoint: path.join(here, 'composition.jsx'), publicDir: assets,
    outDir: path.join(directory, 'bundle')});
  const options = {serveUrl, inputProps: board, browserExecutable: browserPath(), logLevel: 'warn'};
  const composition = await selectComposition({...options, id: 'Demo'});
  await renderMedia({...options, composition, codec: 'h264', audioCodec: 'aac', pixelFormat: 'yuv420p',
    crf: 18, concurrency: 2, outputLocation: output});
}
function assText(value) {
  // Braces/backslashes cannot become ASS commands; text remains literal.
  return value.replaceAll('\\', '/').replaceAll('{', '(').replaceAll('}', ')').replace(/\r?\n/g, '\\N');
}
function assTime(seconds) {
  const ticks = Math.round(seconds * 100);
  return `${Math.floor(ticks / 360000)}:${String(Math.floor(ticks / 6000) % 60).padStart(2, '0')}:${String(Math.floor(ticks / 100) % 60).padStart(2, '0')}.${String(ticks % 100).padStart(2, '0')}`;
}
export async function renderFFmpeg(board, directory, output) {
  const segments = [];
  for (const scene of board.scenes) {
    const subtitles = `[Script Info]\nScriptType: v4.00+\nPlayResX: 1280\nPlayResY: 720\n[V4+ Styles]\n` +
      `Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n` +
      `Style: Caption,Arial,32,&H00FFFFFF,&H00FFFFFF,&H002A1B10,&H002A1B10,0,0,0,0,100,100,0,0,1,2,0,2,70,70,18,1\n` +
      `Style: Title,Arial,60,&H00FFFFFF,&H00FFFFFF,&H002A1B10,&H002A1B10,-1,0,0,0,100,100,0,0,1,2,0,5,90,90,90,1\n` +
      `Style: Eyebrow,Arial,22,&H00C4DB42,&H00C4DB42,&H002A1B10,&H002A1B10,0,0,0,0,100,100,2,0,1,0,0,8,90,90,235,1\n` +
      `Style: Warning,Arial,20,&H00FFFFFF,&H00FFFFFF,&H00003D6B,&H00003D6B,0,0,0,0,100,100,0,0,3,4,0,8,20,20,8,1\n` +
      `[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n` +
      captionCues(scene).map(cue => `Dialogue: 0,${assTime(cue.start)},${assTime(cue.end)},Caption,,0,0,0,,${assText(cue.text)}\n`).join('') +
      (!scene.media ? `Dialogue: 0,0:00:00.00,0:00:30.00,Title,,0,0,0,,${assText(scene.heading ?? board.title)}\n` +
        `Dialogue: 0,0:00:00.00,0:00:30.00,Eyebrow,,0,0,0,,${assText(scene.eyebrow ?? (scene.card === 'outro' ? 'THE RESULT' : 'PRODUCT DEMO'))}\n` : '') +
      (scene.warning ? `Dialogue: 1,0:00:00.00,0:00:30.00,Warning,,0,0,0,,${assText(scene.warning)}\n` : '');
    await writeFile(path.join(directory, `${scene.id}.ass`), subtitles);
    const inputs = scene.media ? ['-i', scene.media] : ['-f', 'lavfi', '-i', 'color=c=0x101b2a:s=1280x720:r=30'];
    inputs.push(...(scene.audio ? ['-i', scene.audio] : ['-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo']));
    const filter = (scene.media ? 'scale=1152:576,pad=1280:720:64:30:color=0x101b2a,' : '') + `ass=${scene.id}.ass`;
    const filename = `${scene.id}-segment.mp4`;
    const audioFilter = `adelay=${Math.round((scene.narrationStart ?? 0) * 1000)}:all=1,apad`;
    await exec(ffmpeg, ['-y', '-v', 'error', ...inputs, '-vf', filter, '-af', audioFilter, '-t', String(scene.duration),
      '-map', '0:v:0', '-map', '1:a:0', '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
      '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-ar', '48000', '-ac', '2', filename], {cwd: directory, timeout: 180000});
    segments.push(`file '${filename}'`);
  }
  await writeFile(path.join(directory, 'segments.txt'), segments.join('\n'));
  await exec(ffmpeg, ['-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', 'segments.txt',
    '-c', 'copy', '-movflags', '+faststart', output], {cwd: directory, timeout: 180000});
}
