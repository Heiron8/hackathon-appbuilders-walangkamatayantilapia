from _common import (
    ROOT,
    LOCAL,
    ORCH,
    architecture_release,
    cmd_exists,
    operating_mode,
    read_json,
    read_json_object,
    run,
    run_network,
    sync_main,
)

git_sync = sync_main()
team = read_json(ORCH/'team.json', {'members': []})
state = read_json(ORCH/'project-state.json', {})
arch = read_json(ORCH/'architecture-state.json', {})
try:
    config = read_json_object(ROOT/'workspace.config.json', {}, 'workspace.config.json')
except (OSError, ValueError) as exc:
    raise SystemExit(f'Project Sync stopped: {exc}')
release = architecture_release(arch, config)
display_arch = arch if release.outcome != 'invalid' else {}
local = read_json(LOCAL/'member.json', {}) or {}
member = next((m for m in team.get('members', []) if m.get('id') == local.get('member_id')), None)

print('PROJECT SYNC')
print(f'\nGit synchronization\n- {git_sync.status} - {git_sync.message}')
print('\nMember')
print(f"- Name: {member.get('name') if member else 'UNCONFIGURED'}")
print(f"- Role: {member.get('role') if member else 'run onboard_member.py'}")
print('\nProject')
print(f"- Operating mode: {operating_mode(config)}")
print(f"- Phase: {state.get('project',{}).get('phase','unknown')}")
print(f"- Architecture status: {display_arch.get('status','unknown')}")
print(f"- Architecture release: {release.outcome}")
print(f"- Current architecture section: {display_arch.get('current_section') or 'none'}")
if display_arch.get('open_questions'):
    print('- Open architecture questions:')
    for q in display_arch['open_questions'][:5]: print(f'  - {q}')

if cmd_exists('git'):
    b = run(['git','branch','--show-current'])
    s = run(['git','status','--short'])
    print('\nGit')
    print(f"- Branch: {'unknown (inspection failed)' if b.returncode != 0 else b.stdout.strip() or '(detached/none)'}")
    print(f"- Working tree: {'unknown (inspection failed)' if s.returncode != 0 else 'clean' if not s.stdout.strip() else 'changes present'}")

github = config.get('github', {})
repo = f"{github.get('owner')}/{github.get('repo')}" if github.get('owner') and github.get('repo') else None
if not repo:
    print('\nGitHub\n- Repository and Project are not configured for this new workspace.')
elif not cmd_exists('gh') or run_network(['gh','auth','status']).returncode != 0:
    print('\nGitHub\n- gh is unavailable or not authenticated.')
else:
    issues = run_network(['gh','issue','list','--repo',repo,'--limit','10','--json','number,title,assignees,labels,state'])
    prs = run_network(['gh','pr','list','--repo',repo,'--limit','10','--json','number,title,state,isDraft,headRefName'])
    print('\nGitHub')
    if issues.returncode == 0 and prs.returncode == 0:
        print(f'- Repository: {repo}')
        print(f"- Issues snapshot: {issues.stdout.strip()[:1000] or '[]'}")
        print(f"- PR snapshot: {prs.stdout.strip()[:1000] or '[]'}")
    else:
        print('- Repository issue/PR state could not be read; status is unknown.')

print('\nRecommended Next Action')
phase = state.get('project',{}).get('phase','new')
if release.outcome == 'invalid':
    print(f'- BLOCKED: {release.message}')
    print('- Repair architecture state before planning or implementation routing continues.')
elif not release.released or phase == 'new':
    print(f'- {release.message}')
    print('- Continue Architecture Kickoff / planning; implementation tasks are not generally released yet.')
else:
    print('- Inspect your active GitHub task / available Ready work.')
