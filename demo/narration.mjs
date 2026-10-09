import {copyFile, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {exec, probe} from './media.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
export async function narrateScene(scene, directory, sourceDirectory, provider) {
  if (provider === 'none' || !scene.narration.trim()) return {provider: 'captions-only', audio: null};
  const target = path.join(directory, `${scene.id}.wav`);
  let choice;
  if (scene.audio) {
    await copyFile(path.resolve(sourceDirectory, scene.audio), target);
    choice = 'manual/local replacement';
  } else if (provider === 'manual') {
    throw new Error(`${scene.id}: --tts manual requires a scene.audio path`);
  } else if (process.platform !== 'win32') {
    if (provider === 'windows') throw new Error('Windows SAPI requires Windows. Use --tts none or scene.audio with --tts manual.');
    return {provider: 'captions-only', audio: null, warning: 'Local TTS unavailable; supply scene.audio or use --tts none'};
  } else {
    const textFile = path.join(directory, `${scene.id}-narration.txt`);
    await writeFile(textFile, scene.narration, 'utf8');
    try {
      const {stdout} = await exec('powershell.exe', ['-NoProfile', '-NonInteractive', '-File', path.join(here, 'tts.ps1'),
        '-TextFile', textFile, '-OutputFile', target], {timeout: 60000});
      choice = `Windows SAPI: ${stdout.trim()}`;
    } catch (error) {
      if (provider !== 'auto') throw error;
      return {provider: 'captions-only', audio: null, warning: 'Local speech synthesis failed; use manual narration. See runtime logs/prerequisites.'};
    }
  }
  const metadata = await probe(target);
  const seconds = Number(metadata.format.duration);
  if (!metadata.streams.some(s => s.codec_type === 'audio') || !(seconds > 0)) throw new Error(`${scene.id}: invalid narration audio`);
  const start = scene.narrationStart ?? 0;
  if (start + seconds > scene.duration - 0.3) throw new Error(`${scene.id}: narration (${seconds.toFixed(2)}s + ${start}s offset) exceeds scene; shorten text or increase duration`);
  return {provider: choice, audio: `${scene.id}.wav`, duration: seconds, start,
    alignment: `scene + ${start}s; fits without truncation`};
}
