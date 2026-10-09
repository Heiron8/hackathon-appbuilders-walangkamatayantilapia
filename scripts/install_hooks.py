from __future__ import annotations
import subprocess
from _common import ROOT
r=subprocess.run(["git","config","core.hooksPath",".githooks"], cwd=ROOT, text=True, capture_output=True)
if r.returncode: raise SystemExit(r.stderr.strip() or "Git hooks could not be installed. Is this a Git repository?")
print("Git hooks installed from .githooks")
