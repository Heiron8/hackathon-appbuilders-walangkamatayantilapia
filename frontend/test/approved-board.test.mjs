import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, stat, mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { createServer } from 'vite';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
const assets = new URL('../src/assets/figma/', import.meta.url);
const manifest = JSON.parse(await readFile(new URL('source-manifest.json', assets)));
const vocabulary = JSON.parse(await readFile(new URL('../../shared/vocabulary.json', import.meta.url)));

test('every canonical picture uses a nonempty, unchanged Figma SVG with preserved root dimensions', async () => {
  assert.equal(Object.keys(manifest.vocabulary_slots).length, 32);
  for (const card of vocabulary.cards) assert.ok(manifest.vocabulary_slots[card.id]);
  for (const asset of Object.values(manifest.assets)) {
    const file = new URL(asset.path, assets); assert.ok((await stat(file)).size > 0);
    const bytes = await readFile(file);
    assert.equal(createHash('sha256').update(bytes).digest('hex'), asset.sha256);
    const root = bytes.toString().match(/<svg\b[^>]*>/)[0];
    assert.ok(root.includes(`width="${asset.width}"`)); assert.ok(root.includes(`height="${asset.height}"`));
  }
});
test('actual application renders all 32 fixed cards, essentials, empty composer and disabled inference/navigation', async () => {
  const cacheDir = await mkdtemp(join(tmpdir(), 'tanaw-render-test-'));
  const server = await createServer({ root: new URL('..', import.meta.url).pathname, cacheDir,
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: false, ws: false, watch: null } });
  try {
    const { default: App } = await server.ssrLoadModule('/src/App.jsx');
    const html = renderToStaticMarkup(createElement(App));
    assert.deepEqual([...html.matchAll(/data-card-id="([^"]+)"/g)].map(match => match[1]), vocabulary.cards.map(card => card.id));
    assert.match(html, /Quick communication pictures/); assert.match(html, /Tap a picture to start your message/);
    assert.match(html, /<button disabled=""[^>]*>Conversation<\/button>/);
    assert.match(html, /<button disabled="">Improve sentence<\/button>/);
    assert.ok(html.includes('Speech has not been initialized.') || html.includes('Speech is unavailable'));
    assert.ok(!html.includes('https://www.figma.com/api/mcp/asset'));
    assert.ok(!html.includes('data:image/svg'));
  } finally { await server.close(); await rm(cacheDir, { recursive: true, force: true }); }
});
