from _common import (
    HACKATHON_MODE,
    ORCH,
    now_iso,
    operating_mode,
    read_json_object,
    require_nonempty_string,
    required_architecture_sections,
    write_json,
)
import argparse

p = argparse.ArgumentParser()
p.add_argument('--status', choices=['not_started','in_progress','review_pending','changes_requested','approved'])
p.add_argument('--current-section')
p.add_argument('--complete-section')
p.add_argument('--open-question')
p.add_argument('--approve-by', help='Record explicit human architecture approval')
args = p.parse_args()
approved_by = None
if args.approve_by is not None:
    try:
        approved_by = require_nonempty_string(args.approve_by, '--approve-by')
    except ValueError as exc:
        raise SystemExit(str(exc))
path = ORCH/'architecture-state.json'
s = read_json_object(path, {}, 'architecture-state.json')
mode = operating_mode()
if args.status == 'approved' and mode == HACKATHON_MODE:
    raise SystemExit('Hackathon Mode approval requires --approve-by HUMAN_NAME.')
required = required_architecture_sections()
completed = set(s.get('completed_sections', []))
if args.status == 'approved':
    missing = [section for section in required if section not in completed]
    if missing:
        raise SystemExit(f'{mode} architecture is incomplete: ' + ', '.join(missing))
if args.status: s['status'] = args.status
if args.current_section: s['current_section'] = args.current_section
if args.complete_section:
    s.setdefault('completed_sections', [])
    if args.complete_section not in s['completed_sections']: s['completed_sections'].append(args.complete_section)
    s['pending_sections'] = [x for x in s.get('pending_sections',[]) if x != args.complete_section]
if args.open_question: s.setdefault('open_questions', []).append(args.open_question)
if approved_by is not None:
    completed = set(s.get('completed_sections', []))
    missing = [section for section in required if section not in completed]
    if missing:
        raise SystemExit(f'{mode} architecture is incomplete: ' + ', '.join(missing))
    s['status'] = 'approved'
    s['approval'] = {'approved_by': approved_by, 'approved_at': now_iso(), 'mode': mode}
s['pending_sections'] = [section for section in required if section not in set(s.get('completed_sections', []))]
s['last_updated'] = now_iso()
write_json(path, s)
print('Architecture state updated.')
