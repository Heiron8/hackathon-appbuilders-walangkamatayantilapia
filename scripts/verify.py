from _common import ROOT, read_json_object, run
import argparse, shlex

p=argparse.ArgumentParser(); p.add_argument('--ci', action='store_true'); args=p.parse_args()
try:
    config = read_json_object(ROOT/'workspace.config.json', {}, 'workspace.config.json')
except (OSError, ValueError) as exc:
    raise SystemExit(f'Workspace verification stopped: {exc}')
commands = config.get('verification',{}).get('commands',[])
if not commands:
    print('No project-specific verification commands configured. Workspace structural checks only.')
    required = ['AGENTS.md','WORKSPACE_SPEC.md','WORKFLOW.md','.orchestrator/project-state.json','.orchestrator/architecture-state.json']
    missing=[x for x in required if not (ROOT/x).exists()]
    if missing:
        print('Missing:', ', '.join(missing)); raise SystemExit(1)
    print('Structural verification PASS')
    raise SystemExit(0)
failed=False
for c in commands:
    print(f'> {c}')
    r=run(shlex.split(c))
    if r.stdout: print(r.stdout)
    if r.stderr: print(r.stderr)
    if r.returncode != 0: failed=True
if failed: raise SystemExit(1)
print('Verification PASS')
