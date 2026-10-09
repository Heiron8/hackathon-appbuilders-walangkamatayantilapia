"""Temporary loopback-only QA server; exposes only speech-check resources."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared.vocabulary import load_vocabulary

PUBLIC = ROOT / 'frontend/public'
RESOURCES = {
    '/': (ROOT / 'docs/qa/speech-check.html', 'text/html; charset=utf-8'),
    '/speech-probe.mjs': (ROOT / 'docs/qa/speech-probe.mjs', 'text/javascript; charset=utf-8'),
    '/speech/index.mjs': (ROOT / 'frontend/src/speech/index.mjs', 'text/javascript; charset=utf-8'),
    '/vocabulary.json': (ROOT / 'shared/vocabulary.json', 'application/json'),
    '/speech-assets.json': (PUBLIC / 'speech-assets.json', 'application/json'),
    '/asset-licenses/GPL-3.0.txt': (PUBLIC / 'asset-licenses/GPL-3.0.txt', 'text/plain; charset=utf-8'),
    '/asset-licenses/SOURCE.md': (PUBLIC / 'asset-licenses/SOURCE.md', 'text/plain; charset=utf-8'),
}
for card in load_vocabulary()['cards']:
    for field, mime in [('audio_path', 'audio/wav'), ('symbol_path', 'image/svg+xml')]:
        path = (PUBLIC / card[field]).resolve()
        if not path.is_relative_to(PUBLIC.resolve()):
            raise ValueError('Asset must stay inside frontend/public')
        RESOURCES['/' + card[field]] = (path, mime)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        resource = RESOURCES.get(self.path)
        if resource is None or not resource[0].is_file():
            self.send_error(404)
            return
        payload = resource[0].read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', resource[1])
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('port must be 1-65535')
    server = HTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Speech QA only: http://127.0.0.1:{args.port} (Ctrl+C stops server)', flush=True)
    server.serve_forever()
