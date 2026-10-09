import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {access, writeFile} from 'node:fs/promises';
import path from 'node:path';
import ffmpegStatic from 'ffmpeg-static';
import ffprobeStatic from 'ffprobe-static';

export const exec = promisify(execFile);
export const ffmpeg = process.env.DEMO_FFMPEG || ffmpegStatic;
export const ffprobe = process.env.DEMO_FFPROBE || ffprobeStatic.path;
export async function probe(filename) {
  const {stdout} = await exec(ffprobe, ['-v', 'error', '-show_format', '-show_streams', '-of', 'json', filename]);
  return JSON.parse(stdout);
}
export async function convertClip(source, target, duration, offset = 0) {
  await exec(ffmpeg, ['-y', '-v', 'error', '-ss', String(offset), '-i', source, '-an',
    '-vf', 'scale=1280:640:force_original_aspect_ratio=decrease,pad=1280:640:(ow-iw)/2:(oh-ih)/2,fps=30,tpad=stop_mode=clone:stop_duration=1',
    '-t', String(duration), '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p', target],
  {timeout: 180000});
}
export function checkMetadata(metadata, expectedDuration, expectAudio) {
  const video = metadata.streams.find(s => s.codec_type === 'video');
  if (!video || video.codec_name !== 'h264' || video.width !== 1280 || video.height !== 720) {
    throw new Error('Output must be a 1280x720 H.264 video');
  }
  if (Math.abs(Number(metadata.format.duration) - expectedDuration) > 0.2) throw new Error('Output duration differs from storyboard');
  if (expectAudio && !metadata.streams.some(s => s.codec_type === 'audio')) throw new Error('Narration audio stream is missing');
}
export async function validateVideo(filename, duration, expectAudio) {
  await access(filename);
  const metadata = await probe(filename);
  checkMetadata(metadata, duration, expectAudio);
  await exec(ffmpeg, ['-v', 'error', '-xerror', '-i', filename, '-f', 'null', '-'], {timeout: 180000});
  return {exists: true, fullDecode: 'PASS', duration: Number(metadata.format.duration),
    video: 'H.264 1280x720', audio: metadata.streams.some(s => s.codec_type === 'audio')};
}
export async function contactSheet(filename, directory, scenes) {
  let start = 0;
  const images = [];
  for (const scene of scenes) {
    const target = path.join(directory, `${scene.id}-frame.png`);
    await exec(ffmpeg, ['-y', '-v', 'error', '-ss', String(start + scene.duration / 2), '-i', filename, '-frames:v', '1', target]);
    images.push(target);
    start += scene.duration;
  }
  await writeFile(path.join(directory, 'review-frames.json'), JSON.stringify(images, null, 2));
  return images;
}
