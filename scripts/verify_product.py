"""Product checks and real loopback startup smoke; invoked by scripts/verify.py."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.error import HTTPError
from urllib.parse import quote
from dev import FRONTEND, PYTHON, ROOT, check_ports, get, running_services, stop_services


def run(command, cwd=ROOT):
    print(">", " ".join(str(arg) for arg in command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def smoke():
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log:
        try:
            with running_services(stdout=log) as processes:
                check_servers(processes)
            check_ports()
            print("PASS | Launcher shutdown released both approved ports")
        except Exception:
            log.seek(0)
            print(log.read(), file=sys.stderr)
            raise


def check_servers(processes):
    health = json.loads(get("/api/health", 8000))
    require(health["vocabulary_version"] == "tanaw-v1", "Backend vocabulary mismatch")
    require(health["ai"] == {"state": "unknown", "suggestions_enabled": False}, "AI readiness drift")
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
    stop_services([processes[0]])
    require('id="root"' in get("/", 5173), "Frontend requires backend to serve its shell")
    require('tanaw-v1' in get(shared_path, 5173), "Frontend vocabulary requires backend")
    print("PASS | Loopback backend, final static assets/reload, Vite proxy, scoped shared access, backend-stop shell/vocabulary")


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
