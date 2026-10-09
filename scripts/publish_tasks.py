from _common import (
    ROOT,
    ORCH,
    architecture_release,
    read_json,
    read_json_object,
    run,
)
from github_project import add as project_add, status as project_status, require as project_require
import json, sys

def issue_marker(key):
    return f'workspace-task-key: {key}'

def issue_lookup(repo):
    # Direct enumeration avoids search indexing delays hiding a just-created key.
    result = run(['gh','api',f'repos/{repo}/issues?state=all&per_page=100','--paginate','--slurp'])
    if result.returncode != 0:
        raise SystemExit(result.stderr or 'GitHub issue lookup failed; publication stopped.')
    try:
        pages = json.loads(result.stdout)
        if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
            raise ValueError('unexpected pages')
        issues = [issue for page in pages for issue in page]
        if any(not isinstance(issue, dict) or 'body' not in issue or not isinstance(issue['body'], (str, type(None))) or not isinstance(issue.get('html_url'), str) for issue in issues):
            raise ValueError('incomplete issue data')
        return [issue for issue in issues if 'pull_request' not in issue]
    except (ValueError, TypeError):
        raise SystemExit('Invalid GitHub issue lookup response; publication stopped.')

def find_issue(key, issues):
    marker = issue_marker(key)
    matches = [issue for issue in issues if marker in (issue.get('body') or '').splitlines()]
    if len(matches) > 1:
        raise SystemExit(f'Duplicate GitHub issues already use {marker}; publication stopped.')
    return matches[0] if matches else None

def issue_body(task):
    ready = task.get('definition_of_ready') or {}
    parts = [
        issue_marker(task['key']),
        '## Goal\n' + task.get('goal', ''),
        '## Module\n' + task.get('module', ''),
        '## Acceptance criteria\n' + '\n'.join(f"- [ ] {x}" for x in task.get('acceptance_criteria', [])),
        '## Dependencies\n' + (', '.join(task.get('dependencies', [])) or 'None'),
        '## Definition of Ready\n**Common:** ' + ready.get('common', '') + '\n\n**Task:** ' + ready.get('task', ''),
        '## Ownership and review\n**Owner specialty:** ' + (task.get('owner_specialty') or 'Not specified') +
        '\n\n**Assignee:** Unassigned; assign when claimed after Ready.\n\n**Reviewers:** ' + task.get('reviewers', ''),
        '## Risk\n' + task.get('risk', 'medium'),
        '## Exit evidence\n' + task.get('exit_evidence', ''),
    ]
    return '\n\n'.join(parts)

def require_architecture_approval(arch, config):
    release = architecture_release(arch, config)
    if not release.released:
        raise SystemExit(release.message)
    return release

def publish():
    arch = read_json(ORCH/'architecture-state.json', {})
    config = read_json_object(ROOT/'workspace.config.json', {}, 'workspace.config.json')
    require_architecture_approval(arch, config)
    plan_path = ROOT/'docs/plans/approved-tasks.json'
    if not plan_path.exists():
        raise SystemExit('Missing docs/plans/approved-tasks.json (copy/edit the example after task-plan approval).')
    tasks = json.loads(plan_path.read_text(encoding='utf-8'))
    keys = [task['key'] for task in tasks]
    if len(keys) != len(set(keys)):
        raise SystemExit('Duplicate task keys in approved-tasks.json; publication stopped.')
    github = config.get('github', {})
    if not github.get('owner') or not github.get('repo'):
        raise SystemExit('Set github.owner and github.repo in workspace.config.json first.')
    repo = f"{github['owner']}/{github['repo']}"
    project_require()
    issues = issue_lookup(repo)
    for task in tasks:
        key = task['key']
        match = find_issue(key, issues)
        if match:
            url = match['html_url']
            print(f'[EXISTS] {key}: {url}')
        else:
            body = issue_body(task)
            result = run(['gh','issue','create','--repo',repo,'--title',task['title'],'--body',body])
            if result.returncode != 0:
                print(result.stderr, file=sys.stderr)
                raise SystemExit(f'Failed publishing {key}')
            url = result.stdout.strip()
            if not url:
                raise SystemExit(f'Issue creation returned no URL for {key}; publication stopped.')
            issues.append({'body': body, 'html_url': url})
            print(f'[CREATED] {key}: {url}')
        item, _ = project_add(url, known_new=not bool(match))
        # A prior run may have added the item before its Backlog update failed.
        if not item.get('status'):
            project_status(url, 'backlog')
    print('Task publication complete; existing Project statuses preserved; new tasks are Backlog.')

if __name__ == '__main__':
    publish()
