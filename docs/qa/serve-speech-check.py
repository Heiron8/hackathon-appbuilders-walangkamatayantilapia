"""Temporary loopback-only QA server; exposes only speech-check resources."""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESOURCES = {
    '/': (ROOT / 'docs/qa/speech-check.html', 'text/html; charset=utf-8'),
    '/speech-probe.mjs': (ROOT / 'docs/qa/speech-probe.mjs', 'text/javascript; charset=utf-8'),
    '/speech/index.mjs': (ROOT / 'frontend/src/speech/index.mjs', 'text/javascript; charset=utf-8'),
    '/vocabulary.json': (ROOT / 'shared/vocabulary.json', 'application/json'),
}


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
    print('Speech QA only: http://127.0.0.1:8765 (Ctrl+C stops server)', flush=True)
    HTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
