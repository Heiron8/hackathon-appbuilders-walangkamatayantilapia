from _common import ORCH, read_json, write_json, now_iso
import argparse
p=argparse.ArgumentParser(); p.add_argument('task_key'); p.add_argument('--status', default='in-progress'); p.add_argument('--comment', default=''); p.add_argument('--agent', default=''); p.add_argument('--human-member-id', default=''); a=p.parse_args()
path=ORCH/'task-state'/f'{a.task_key}.json'
data=read_json(path,{}) or {}
data.update({'task_key':a.task_key,'status':a.status,'comment':a.comment,'agent':a.agent or data.get('agent'),'human_member_id':a.human_member_id or data.get('human_member_id'),'updated_at':now_iso()})
write_json(path,data); print(f'Checkpoint saved: {path.relative_to(ORCH.parent)}')
