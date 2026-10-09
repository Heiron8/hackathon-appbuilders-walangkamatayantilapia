"""One-command loopback development startup; shared with product verification."""
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
VENV_PYTHON = ROOT / "backend/.venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
PYTHON = str(VENV_PYTHON) if VENV_PYTHON.is_file() else sys.executable
PORTS = (8000, 5173)
HTTP = build_opener(ProxyHandler({}))


def get(path, port):
    with HTTP.open(f"http://127.0.0.1:{port}{path}", timeout=2) as response:
        return response.read().decode("utf-8")


def wait_ready(process, path, port):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Server on {port} exited with {process.returncode}; check its startup output")
        try:
            return get(path, port)
        except (URLError, TimeoutError, ConnectionError):
            time.sleep(0.1)
    raise RuntimeError(f"Server on {port} did not become ready within 20 seconds")


def check_dependencies():
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is missing. Follow locked setup in docs/development.md.")
    backend = subprocess.run([PYTHON, "-c", "import fastapi, pydantic, uvicorn, httpx"],
                             cwd=ROOT, capture_output=True, text=True, timeout=15)
    if backend.returncode:
        raise RuntimeError("Backend dependencies are missing/incomplete. Install backend/requirements.lock.txt "
                           "using the Python environment in docs/development.md.")
    frontend = subprocess.run([node, "--input-type=module", "-e",
                               "await import('vite'); await import('@vitejs/plugin-react'); "
                               "await import('react'); await import('react-dom/client');"],
                              cwd=FRONTEND, capture_output=True, text=True, timeout=15)
    if frontend.returncode or not (FRONTEND / "node_modules/vite/bin/vite.js").is_file():
        raise RuntimeError("Frontend dependencies are missing/incomplete. Run npm ci in frontend/.")
    return node


def check_ports():
    for port in PORTS:
        with socket.socket() as probe:
            # Allow a just-stopped server's TIME_WAIT sockets, but never share a listener.
            if os.name != "nt":
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                raise RuntimeError(f"Port {port} is unavailable on 127.0.0.1. "
                                   "Stop its existing service before starting Tanaw.") from exc


def stop_services(processes):
    for process in reversed(processes):
        if process.poll() is None:
            try:
                if os.name == "nt":
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(process.pid, signal.SIGTERM)
            except OSError:
                process.terminate()
    for process in reversed(processes):
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                process.kill()
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass  # It exited between the timeout and termination.
            process.wait(timeout=5)


@contextmanager
def running_services(stdout=None):
    node = check_dependencies()
    check_ports()
    commands = [
        ([PYTHON, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1",
          "--port", "8000", "--no-access-log"], ROOT, "/api/health", 8000),
        ([node, str(FRONTEND / "node_modules/vite/bin/vite.js"), "--host", "127.0.0.1",
          "--port", "5173", "--strictPort"], FRONTEND, "/", 5173),
    ]
    processes = []
    try:
        for command, cwd, path, port in commands:
            process = subprocess.Popen(command, cwd=cwd, stdout=stdout, stderr=stdout,
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                                       start_new_session=os.name != "nt")
            processes.append(process)
            wait_ready(process, path, port)
        yield processes
    finally:
        stop_services(processes)


def main():
    # On POSIX, an external termination follows the same cleanup path as Ctrl+C.
    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    try:
        with running_services() as processes:
            print("Tanaw ready: http://127.0.0.1:5173 (backend: http://127.0.0.1:8000)", flush=True)
            print("Press Ctrl+C to stop both services. Ollama is not required.", flush=True)
            while True:
                for name, process in zip(("Backend", "Frontend"), processes):
                    if process.poll() is not None:
                        raise RuntimeError(f"{name} exited unexpectedly (code {process.returncode})")
                time.sleep(0.25)
    except KeyboardInterrupt:
        print("Tanaw stopped.", flush=True)
        return 0
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print(f"Tanaw startup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
