import {chromium} from 'playwright';
import {performance} from 'node:perf_hooks';
import path from 'node:path';
import {mkdir} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {safeURL, VIEWPORT} from './storyboard.mjs';
import {convertClip, probe} from './media.mjs';

export function browserPath() {
  if (process.env.DEMO_BROWSER) return process.env.DEMO_BROWSER;
  const expected = chromium.executablePath();
  if (existsSync(expected)) return expected;
  if (process.platform === 'win32') {
    for (const executable of [
      path.join(process.env.ProgramFiles || 'C:\\Program Files', 'Google/Chrome/Application/chrome.exe'),
      path.join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'Microsoft/Edge/Application/msedge.exe')
    ]) if (existsSync(executable)) return executable;
  }
  return expected; // Missing prerequisite produces Playwright's actionable error.
}
export async function captureScene(scene, board, directory) {
  const rawDirectory = path.join(directory, 'raw', scene.id);
  await mkdir(rawDirectory, {recursive: true});
  const browser = await chromium.launch({executablePath: browserPath(), headless: true});
  const context = await browser.newContext({viewport: VIEWPORT, recordVideo: {dir: rawDirectory, size: VIEWPORT},
    reducedMotion: 'reduce'});
  let page, origin, offset, result;
  try {
    page = await context.newPage();
    origin = performance.now();
    page.setDefaultTimeout(15000);
    await page.goto(safeURL(scene.url ?? board.baseURL), {waitUntil: 'domcontentloaded'});
    await page.locator(scene.ready).waitFor({state: 'visible'});
    // Browser readiness is selector/assertion driven. The dwell below is video pacing only.
    offset = (performance.now() - origin) / 1000;
    const started = performance.now();
    if (scene.leadIn) await new Promise(resolve => setTimeout(resolve, scene.leadIn * 1000));
    for (const action of scene.actions) {
      const locator = page.locator(action.selector);
      if (action.type === 'assertVisible') await locator.waitFor({state: 'visible'});
      else if (action.type === 'assertText') {
        await page.waitForFunction(({selector, value}) => document.querySelector(selector)?.textContent?.includes(value),
          {selector: action.selector, value: action.value}, {timeout: 15000});
      } else if (action.type === 'fill') await locator.fill(action.value);
      else if (action.type === 'press') await locator.press(action.value);
      else if (action.type === 'check') await locator.check();
      else await locator.click();
      // Explicit editorial pauses follow actual actions/assertions; never UI readiness waits.
      if (action.pauseAfter) await new Promise(resolve => setTimeout(resolve, action.pauseAfter * 1000));
    }
    const elapsed = (performance.now() - started) / 1000;
    if (elapsed > scene.duration - 0.5) throw new Error(`${scene.id}: actions exceed scene duration; shorten the flow or increase duration`);
    await page.screenshot({path: path.join(directory, `${scene.id}-capture.png`)});
    // Allow the screencast encoder to flush its last frame; this tail is trimmed.
    await new Promise(resolve => setTimeout(resolve, (scene.duration - elapsed + 1) * 1000));
    result = {id: scene.id, assertions: 'PASS', actionTypes: scene.actions.map(a => a.type),
      recordedAt: new Date().toISOString(), build: board.build.id, offsetSeconds: offset,
      browser: {executable: browserPath(), version: browser.version()}};
  } finally {
    await context.close(); // Playwright flushes the WebM only after context close.
    await browser.close();
  }
  const source = await page.video().path();
  const metadata = await probe(source);
  if (Number(metadata.format.duration) < offset + scene.duration - 1) {
    throw new Error(`${scene.id}: recording was truncated (${metadata.format.duration}s; offset ${offset.toFixed(2)}s; scene ${scene.duration}s)`);
  }
  const target = path.join(directory, `${scene.id}.mp4`);
  await convertClip(source, target, scene.duration, offset);
  return {media: `${scene.id}.mp4`, evidence: {...result, raw: path.relative(directory, source)}};
}
