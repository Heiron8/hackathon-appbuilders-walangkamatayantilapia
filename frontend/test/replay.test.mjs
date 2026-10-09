import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

test('Replay remains an explicit action after completion, Stop and recoverable failure', async t => {
  const cacheDir = await mkdtemp(join(tmpdir(), 'tanaw-replay-test-'));
  const server = await createServer({ root: fileURLToPath(new URL('..', import.meta.url)), cacheDir,
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: false, ws: false, watch: null } });
  try {
    const { ReplayButton } = await server.ssrLoadModule('/src/App.jsx');
    for (const playback of ['idle', 'stopped', 'error']) {
      await t.test(playback, () => {
        let calls = 0;
        const props = { playback, canSpeak: true, playedCurrentMessage: true, onReplay: () => calls++ };
        assert.match(renderToStaticMarkup(createElement(ReplayButton, props)), /<button>Replay audio<\/button>/);
        const button = ReplayButton(props);
        assert.equal(calls, 0, 'rendering must not start speech');
        button.props.onClick();
        assert.equal(calls, 1, 'one explicit click requests one replay');
      });
    }
    await t.test('no replay before first speech, during speech, after word edits or when unavailable', () => {
      const ready = { playback: 'idle', canSpeak: true, playedCurrentMessage: true, onReplay: () => assert.fail('automatic speech') };
      for (const override of [{ playedCurrentMessage: false }, { playback: 'speaking' }, { canSpeak: false }]) {
        assert.equal(renderToStaticMarkup(createElement(ReplayButton, { ...ready, ...override })), '');
      }
    });
  } finally { await server.close(); await rm(cacheDir, { recursive: true, force: true }); }
});
