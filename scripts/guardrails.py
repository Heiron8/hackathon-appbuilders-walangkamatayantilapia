"""Portable deterministic checks used by Git hooks and verify-workspace."""
from __future__ import annotations
import argparse, re, subprocess, sys
from pathlib import Path
from _common import ROOT

CREDENTIAL_PATTERN = re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?(?!example|changeme|your[_-]|\$\{|\})([a-z0-9_./+=-]{8,})")
PROTECTED = {"main", "master", "production", "release"}

def git(*args): return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
def changed(staged=False):
    args = ["diff", "--cached", "--name-only"] if staged else ["diff", "--name-only", "HEAD"]
    r = git(*args); return [ROOT / p for p in r.stdout.splitlines() if p]
def scan(files):
    hits=[]
    for path in files:
        if path.suffix.lower() in {".png", ".jpg", ".zip", ".pdf"} or not path.is_file(): continue
        try: lines=path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError: continue
        try: label=path.relative_to(ROOT)
        except ValueError: label=path
        hits += [f"{label}:{n}" for n,line in enumerate(lines,1) if CREDENTIAL_PATTERN.search(line)]
    return hits
def protected_branch():
    r=git("branch", "--show-current")
    return r.stdout.strip() in PROTECTED
def main():
    p=argparse.ArgumentParser(); p.add_argument("check", choices=["secrets","scope","protected-branch"]); p.add_argument("--staged", action="store_true"); a=p.parse_args()
    if a.check=="secrets":
        hits=scan(changed(a.staged))
        if hits: print("Potential secret(s):\n"+"\n".join(hits)); return 1
        print("Secret scan PASS"); return 0
    if a.check=="scope":
        forbidden=[x for x in changed(a.staged) if ".workspace-local" in x.parts or x.name==".env"]
        if forbidden: print("Local identity/environment files must not be committed."); return 1
        print("Scope check PASS"); return 0
    if protected_branch(): print("Direct push from a protected branch is blocked; use a feature branch and PR."); return 1
    print("Protected-branch check PASS"); return 0
if __name__ == "__main__": raise SystemExit(main())
