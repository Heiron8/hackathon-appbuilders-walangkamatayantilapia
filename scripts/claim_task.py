"""Claim an already Ready issue on an isolated branch."""
import argparse
import json

from _common import LOCAL, ORCH, ROOT, architecture_release, read_json, cmd_exists, run, run_network
from github_project import find_item, items, status as set_status, values, project as project_number
from onboard_member import validate_team

ISSUE_STATUSES = {'backlog', 'ready', 'in-progress', 'in-review', 'blocked', 'done'}


def check_claim_context(member, team):
    validate_team(team)
    user = run_network(['gh', 'api', 'user', '--jq', '.login'])
    if user.returncode != 0 or user.stdout.strip().lower() != member['github'].lower():
        raise SystemExit('Authenticated GitHub account must match the local registered member.')
    config = read_json(ROOT/'workspace.config.json', {})
    release = architecture_release(read_json(ORCH/'architecture-state.json', {}), config)
    state = read_json(ORCH/'project-state.json', {})
    if not release.released or state.get('project', {}).get('phase') != 'implementation':
        raise SystemExit('Claim requires approved architecture and released implementation.')


def issue_status(task):
    try:
        statuses = [label['name'][7:] for label in task['labels'] if label['name'].startswith('status:')]
        if task['state'] != 'OPEN' or len(statuses) != 1 or statuses[0] not in ISSUE_STATUSES:
            raise ValueError('unsafe status')
        return statuses[0]
    except (KeyError, TypeError, ValueError):
        raise SystemExit('Issue must be open with exactly one supported status: label; ask the Lead Architect to mark it Ready.')


def claim_issue(task, member):
    """Lead preassignment avoids racing unassigned Issues (GitHub has no claim CAS)."""
    login, url = member['github'].lower(), task['url']
    github = read_json(ROOT/'workspace.config.json', {}).get('github', {})
    owner, repo = github.get('owner'), github.get('repo')
    if not owner or not repo or url != f"https://github.com/{owner}/{repo}/issues/{task['number']}":
        raise SystemExit('Issues-first claim requires an Issue in the configured repository; claim stopped.')
    if owners(task) != [login]:
        raise SystemExit('Issues-first claim requires exclusive Lead-assigned ownership; ask the Lead Architect to serialize assignment.')
    if issue_status(task) not in ('ready', 'in-progress'):
        raise SystemExit('Issue is not Ready or this owner\'s In Progress retry; status preserved.')
    workspace = prepare_branch(f"task/issue-{task['number']}")
    current = issue_state(url)
    if owners(current) != [login]:
        raise SystemExit('Competing or missing owner detected; issue status preserved.')
    status = issue_status(current)
    if status == 'ready':
        edited = run_network(['gh', 'issue', 'edit', url, '--remove-label', 'status:ready',
                              '--add-label', 'status:in-progress'])
        if edited.returncode != 0:
            raise SystemExit('Issue status update failed; reread GitHub and retry. No claim success reported.')
    elif status != 'in-progress':
        raise SystemExit('Issue status changed before mutation; status preserved.')
    final = issue_state(url)
    if owners(final) != [login] or issue_status(final) != 'in-progress':
        raise SystemExit('Issue ownership/status changed; claim not reported as successful. Ask the Lead Architect to reconcile.')
    print(f"TASK CLAIM RESULT\n- Owner: {member['name']}\n- GitHub: {member['github']}\n- Issue: {url}\n- Branch/worktree: {workspace}\n- Status: In Progress\n- Source: GitHub Issues (Lead-serialized ownership)")


def prepare_branch(branch):
    state = run(['git', 'status', '--porcelain'])
    current = run(['git', 'branch', '--show-current'])
    if state.returncode != 0 or current.returncode != 0 or state.stdout.strip():
        raise SystemExit('Claim requires a clean checkout.')
    if current.stdout.strip() == branch:
        return branch
    if current.stdout.strip() != 'main':
        raise SystemExit('Start or retry claim from main or the task branch.')

    worktrees = run(['git', 'worktree', 'list', '--porcelain'])
    if worktrees.returncode != 0:
        raise SystemExit(worktrees.stderr or 'Could not inspect existing worktrees.')
    for block in worktrees.stdout.split('\n\n'):
        if f'branch refs/heads/{branch}' in block.splitlines():
            return next(line.removeprefix('worktree ') for line in block.splitlines() if line.startswith('worktree '))

    existing = run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch}'])
    if existing.returncode not in (0, 1):
        raise SystemExit(existing.stderr or 'Could not inspect existing task branch.')
    command = ['git', 'switch', branch] if existing.returncode == 0 else ['git', 'switch', '-c', branch]
    prepared = run(command)
    if prepared.returncode != 0:
        raise SystemExit(prepared.stderr or 'Could not prepare isolated branch; claim stopped.')
    return branch


def issue_state(issue):
    viewed = run_network(['gh', 'issue', 'view', str(issue), '--json', 'number,url,assignees,state,labels'])
    if viewed.returncode != 0:
        raise SystemExit(viewed.stderr or 'Issue lookup failed; claim stopped.')
    try:
        task = json.loads(viewed.stdout)
        if (not isinstance(task['number'], int) or not isinstance(task['url'], str)
                or not isinstance(task['assignees'], list)):
            raise ValueError('incomplete issue')
        return task
    except (ValueError, KeyError, TypeError):
        raise SystemExit('Incomplete issue lookup; claim stopped.')


def owners(task):
    try:
        return [assignee['login'].lower() for assignee in task['assignees']]
    except (KeyError, TypeError, AttributeError):
        raise SystemExit('Incomplete assignee lookup; claim stopped.')


def verify_owner(url, login, added_by_us=False):
    current = owners(issue_state(url))
    login = login.lower()
    if current == [login]:
        return
    if added_by_us and login in current and any(owner != login for owner in current):
        removed = run(['gh', 'issue', 'edit', url, '--remove-assignee', login])
        remaining = owners(issue_state(url))
        if removed.returncode != 0 or login in remaining:
            raise SystemExit('Competing owner detected; removal of this claim assignment needs review.')
    raise SystemExit('Competing or missing owner detected; claim stopped.')


def claim(issue):
    team = read_json(ORCH/'team.json', {'members': []})
    local = read_json(LOCAL/'member.json', {}) or {}
    member = next((m for m in team.get('members', []) if m.get('id') == local.get('member_id')), None)
    if not member or not member.get('github'):
        raise SystemExit('Current local member needs a GitHub username in the team registry.')
    if not cmd_exists('gh') or run_network(['gh', 'auth', 'status']).returncode != 0:
        raise SystemExit('Authenticated gh CLI required.')
    check_claim_context(member, team)

    task = issue_state(issue)
    number, url = task['number'], task['url']
    if project_number is None:
        return claim_issue(task, member)
    try:
        status = (find_item(url, items()) or {}).get('status')
    except SystemExit:
        print('GitHub Project unavailable; checking explicit Issue status and Lead-assigned ownership.')
        return claim_issue(task, member)
    ready, in_progress = values.get('ready', 'Ready'), values.get('in_progress', 'In Progress')
    initial_owners = owners(task)
    same_owner = initial_owners == [member['github'].lower()]
    if (status != ready and not (status == in_progress and same_owner)) or (initial_owners and not same_owner):
        raise SystemExit('Task must be Ready/unclaimed or already claimed by this developer; claim stopped.')

    branch = f'task/issue-{number}'
    workspace = prepare_branch(branch)
    current_owners = owners(issue_state(url))
    if current_owners and current_owners != [member['github'].lower()]:
        raise SystemExit('Competing owner claimed task before assignment; claim stopped.')
    added_by_us = False
    if not current_owners:
        added_by_us = True
        assigned = run(['gh', 'issue', 'edit', url, '--add-assignee', member['github']])
        if assigned.returncode != 0:
            verify_owner(url, member['github'], added_by_us)
            raise SystemExit(assigned.stderr or 'Owner assignment failed; task remains Ready.')
    verify_owner(url, member['github'], added_by_us)
    try:
        set_status(url, 'in_progress', claim_owner=member['github'])
    except SystemExit:
        verify_owner(url, member['github'], added_by_us)
        raise
    verify_owner(url, member['github'], added_by_us)
    final_status = (find_item(url, items()) or {}).get('status')
    if final_status != in_progress:
        raise SystemExit('Project status changed before claim completed; claim not reported as successful.')
    verify_owner(url, member['github'], added_by_us)
    print(f"TASK CLAIM RESULT\n- Owner: {member['name']}\n- GitHub: {member['github']}\n- Issue: {url}\n- Branch/worktree: {workspace}\n- Status: In Progress")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('issue')
    claim(parser.parse_args().issue)
