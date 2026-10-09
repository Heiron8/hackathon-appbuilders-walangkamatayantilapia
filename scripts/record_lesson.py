from _common import ROOT, now_iso
import argparse, re
p=argparse.ArgumentParser(); p.add_argument('--title', required=True); p.add_argument('--problem', required=True); p.add_argument('--root-cause', required=True); p.add_argument('--proposal', required=True); a=p.parse_args()
lessons=ROOT/'docs/workspace/lessons'; lessons.mkdir(parents=True, exist_ok=True)
existing=sorted(lessons.glob('LESSON-*.md'))
num=len(existing)+1
slug=re.sub(r'[^a-z0-9]+','-',a.title.lower()).strip('-')[:40]
path=lessons/f'LESSON-{num:03d}-{slug}.md'
content = (
    f'# LESSON-{num:03d}: {a.title}\n\n'
    f'- Recorded: {now_iso()}\n\n'
    f'## Problem\n{a.problem}\n\n'
    f'## Root cause\n{getattr(a, "root_cause")}\n\n'
    f'## Proposed harness improvement\n{a.proposal}\n\n'
    '## Regression check\n_To be added before merge where practical._\n\n'
    '## Approval / PR\n_Pending normal workspace review._\n'
)
path.write_text(content, encoding='utf-8')
print(path)
