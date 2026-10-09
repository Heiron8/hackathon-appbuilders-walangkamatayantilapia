from _common import ROOT, read_json_object, cmd_exists, run
from github_project import status as set_status
import json

try:
    cfg=read_json_object(ROOT/'workspace.config.json',{},'workspace.config.json')
except (OSError, ValueError) as exc:
    raise SystemExit(f'Project reconciliation stopped: {exc}')
gh=cfg.get('github',{}); owner=gh.get('owner'); project=gh.get('project_number')
if not owner or project is None: raise SystemExit('Configure github.owner and github.project_number first.')
if not cmd_exists('gh') or run(['gh','auth','status']).returncode!=0: raise SystemExit('Authenticated gh CLI required.')
r=run(['gh','project','item-list',str(project),'--owner',str(owner),'--limit','200','--field',gh.get('status_field','Status'),'--format','json'])
if r.returncode!=0: raise SystemExit(r.stderr)
data=json.loads(r.stdout or '{}')
items=data.get('items', data if isinstance(data,list) else [])
changed=0
for item in items:
    content=item.get('content') or {}
    url=content.get('url') or item.get('url')
    state=(content.get('state') or '').upper()
    typ=(content.get('type') or '').lower()
    if url and state=='CLOSED' and ('issue' in typ or '/issues/' in url):
        try:
            set_status(url,'done'); changed+=1
        except SystemExit:
            pass
print(f'Reconciliation complete. Closed issue items moved/confirmed Done: {changed}')
