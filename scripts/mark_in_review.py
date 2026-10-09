from _common import run, cmd_exists
from github_project import status as set_status
import argparse
p=argparse.ArgumentParser(); p.add_argument('issue'); a=p.parse_args()
if not cmd_exists('gh') or run(['gh','auth','status']).returncode != 0: raise SystemExit('Authenticated gh CLI required.')
r=run(['gh','issue','view',str(a.issue),'--json','url','--jq','.url'])
if r.returncode!=0: raise SystemExit(r.stderr)
set_status(r.stdout.strip(),'in_review')
print('Project status updated to In Review.')
