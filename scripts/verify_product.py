"""Product checks and real loopback startup smoke; invoked by scripts/verify.py."""
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
VENV_PYTHON = ROOT / "backend/.venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.is_file() else sys.executable
HTTP = build_opener(ProxyHandler({}))  # Loopback requests never use an external proxy.


def run(command, cwd=ROOT):
    print(">", " ".join(str(arg) for arg in command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def get(path, port):
    with HTTP.open(f"http://127.0.0.1:{port}{path}", timeout=2) as response:
        return response.read().decode("utf-8")


def wait_ready(process, path, port):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Server on {port} exited with {process.returncode}")
        try:
            return get(path, port)
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError(f"Server on {port} did not become ready")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def smoke():
    # Refuse occupied ports. Never terminate or reuse another developer's server.
    for port in [8000, 5173]:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
    commands = [
        ([PYTHON, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1",
          "--port", "8000", "--no-access-log"], ROOT),
        ([shutil.which("node"), str(FRONTEND / "node_modules/vite/bin/vite.js")], FRONTEND),
    ]
    processes = []
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log:
        try:
            for command, cwd in commands:
                processes.append(subprocess.Popen(command, cwd=cwd, stdout=log, stderr=log))
            health = json.loads(wait_ready(processes[0], "/api/health", 8000))
            require(health["vocabulary_version"] == "tanaw-v1", "Backend vocabulary mismatch")
            require(health["ai"] == {"state": "unknown", "suggestions_enabled": False}, "AI readiness drift")
            wait_ready(processes[1], "/", 5173)
            require(json.loads(get("/api/health", 5173)) == health, "Vite API proxy mismatch")
            require("Application foundation ready" in get("/src/App.jsx", 5173), "React entry unavailable")
            shared_path = "/@fs/" + quote((ROOT / "shared/vocabulary.json").as_posix(), safe="/:")
            require('tanaw-v1' in get(shared_path, 5173), "Shared vocabulary not available to Vite")
            forbidden_path = "/@fs/" + quote((ROOT / "AGENTS.md").as_posix(), safe="/:")
            try:
                get(forbidden_path, 5173)
            except HTTPError as exc:
                require(exc.code == 403, "Unexpected Vite filesystem denial")
            else:
                raise RuntimeError("Vite exposed files outside frontend/shared")
            html = get("/", 8000)
            assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', html)
            require(assets, "Final frontend assets missing")
            for asset in assets:
                require(bool(get(asset, 8000)), "Bundled asset unavailable")
            # Exercise another local reload. Physical network disconnection is a separate QA gate.
            require(get("/", 8000) == html, "Static reload changed unexpectedly")
            processes[0].terminate()
            processes[0].wait(timeout=5)
            require('id="root"' in get("/", 5173), "Frontend requires backend to serve its shell")
            require('tanaw-v1' in get(shared_path, 5173), "Frontend vocabulary requires backend")
            print("PASS | Loopback backend, final static assets/reload, Vite proxy, scoped shared access, backend-stop shell/vocabulary")
        except Exception:
            log.seek(0)
            print(log.read(), file=sys.stderr)
            raise
        finally:
            for process in reversed(processes):
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


def main():
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm or not shutil.which("node"):
        raise SystemExit("Node/npm missing; see docs/development.md")
    run([npm, "test"], FRONTEND)
    run([npm, "run", "build"], FRONTEND)
    run([PYTHON, "-m", "pip", "check"])
    run([PYTHON, "-m", "unittest", "discover", "-s", "backend/tests", "-v"])
    smoke()


if __name__ == "__main__":
    main()
