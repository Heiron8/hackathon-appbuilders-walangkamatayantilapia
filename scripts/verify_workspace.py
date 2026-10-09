"""Single offline-safe acceptance check for the workspace harness."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from _common import HACKATHON_MODE, ROOT, operating_mode, read_json_object
from onboard_member import IdentityError, validate_team

REQUIRED=("AGENTS.md","WORKSPACE_SPEC.md","WORKSPACE_REQUIREMENTS.md","README.md",".env.example",
          ".orchestrator/project-state.json",".orchestrator/architecture-state.json",".orchestrator/team.json",
          ".githooks/pre-commit",".githooks/pre-push","scripts/guardrails.py","scripts/install_hooks.py")
CONTRACTS=("project-sync","architecture-sync","task-claim","checkpoint","verification","pr-review","delivery","blocked-task","closeout")
AGENTS=("lead","architect","frontend","backend","database","qa","security","pr-reviewer","ui-designer","design-qa","deployment")
ADAPTERS=("vscode","codex","orca","kiro","claude","gemini","generic")
def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'} | {name}" + (f" | {detail}" if detail else "")); return ok
def main():
    p=argparse.ArgumentParser(); p.add_argument("--quick",action="store_true"); a=p.parse_args(); all_ok=True
    all_ok &= check("Workspace structure", all((ROOT/x).exists() for x in REQUIRED))
    all_ok &= check("Response contracts", all((ROOT/"response-contracts"/f"{x}.md").exists() for x in CONTRACTS))
    standard=ROOT/"agents"/"CHARTER_STANDARD.md"
    all_ok &= check("Professional charters", standard.exists() and len(standard.read_text(encoding="utf-8"))>1800 and all((ROOT/"agents"/x/"CHARTER.md").exists() and len((ROOT/"agents"/x/"CHARTER.md").read_text(encoding="utf-8"))>300 for x in AGENTS))
    all_ok &= check("Runtime adapters", all((ROOT/"adapters"/x/"README.md").exists() for x in ADAPTERS))
    try:
        cfg=read_json_object(ROOT/"workspace.config.json",{},"workspace.config.json")
        state=read_json_object(ROOT/".orchestrator/project-state.json",{},"project-state.json")
        arch=read_json_object(ROOT/".orchestrator/architecture-state.json",{},"architecture-state.json")
        policies=read_json_object(ROOT/".orchestrator/policies.json",{},"policies.json")
        all_ok &= check("State models", True)
        mode=operating_mode(cfg)
        all_ok &= check("Operating mode", mode != HACKATHON_MODE or (ROOT/"docs/workspace/hackathon-mode.md").exists(), mode)
        all_ok &= check("Mandatory delivery gates", policies.get("task_publication_requires_architecture_approval") is True and policies.get("verification_required") is True and policies.get("independent_review_required") is True)
    except (json.JSONDecodeError, OSError, ValueError) as e: all_ok &= check("State models",False,str(e))
    try:
        team=read_json_object(ROOT/".orchestrator/team.json",{},"team.json")
        validate_team(team)
        all_ok &= check("Team registry", True)
    except (json.JSONDecodeError, OSError, ValueError, IdentityError) as e:
        all_ok &= check("Team registry",False,str(e))
    if not a.quick:
        tests=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-p","test_*.py"],cwd=ROOT,text=True,capture_output=True)
        all_ok &= check("Workspace tests",tests.returncode==0,(tests.stdout+tests.stderr).strip().splitlines()[-1] if (tests.stdout+tests.stderr).strip() else "")
        r=subprocess.run([sys.executable,"scripts/guardrails.py","secrets"],cwd=ROOT,text=True,capture_output=True)
        all_ok &= check("Secret scanning",r.returncode==0,r.stdout.strip() or r.stderr.strip())
        print("PASS | Local verification report | Offline-safe checks completed")
        print("NOT TESTED | Live GitHub integration | Verify the configured repository and Project separately")
    return 0 if all_ok else 1
if __name__ == "__main__": raise SystemExit(main())
