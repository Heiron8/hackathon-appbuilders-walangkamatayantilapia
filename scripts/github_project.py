from _common import ROOT, read_json_object, cmd_exists, run
import argparse, json, re, time

try:
    cfg = read_json_object(ROOT/'workspace.config.json', {}, 'workspace.config.json')
except (OSError, ValueError) as exc:
    raise SystemExit(f'GitHub Project configuration is invalid: {exc}')
gh = cfg.get('github', {})
owner = gh.get('owner')
project = gh.get('project_number')
field = gh.get('status_field', 'Status')
values = gh.get('status_values', {})

def require():
    if not cmd_exists('gh') or run(['gh','auth','status']).returncode != 0:
        raise SystemExit('Authenticated GitHub CLI (gh) is required.')
    if not owner or project is None:
        raise SystemExit('Set github.owner and github.project_number in workspace.config.json first.')

def query(args):
    result = run(['gh','project',*args])
    if result.returncode != 0:
        raise SystemExit(result.stderr or f'GitHub Project lookup/update failed: {args[0]}')
    try:
        return json.loads(result.stdout)
    except (ValueError, TypeError):
        raise SystemExit(f'Invalid GitHub Project response: {args[0]}')

def items():
    require()
    graph = '''query($owner:String!, $repo:String!, $number:Int!, $field:String!) {
      repository(owner:$owner, name:$repo) { owner {
        ... on User { projectV2(number:$number) { id items(first:100) { totalCount nodes { id content { ... on Issue { url } } fieldValueByName(name:$field) { ... on ProjectV2ItemFieldSingleSelectValue { name } } } } } }
        ... on Organization { projectV2(number:$number) { id items(first:100) { totalCount nodes { id content { ... on Issue { url } } fieldValueByName(name:$field) { ... on ProjectV2ItemFieldSingleSelectValue { name } } } } } }
      } }
    }'''
    result = run(['gh','api','graphql','-f',f'owner={owner}','-f',f'repo={gh.get("repo")}',
                  '-F',f'number={project}','-f',f'field={field}','-f',f'query={graph}'])
    if result.returncode != 0:
        raise SystemExit(result.stderr or 'GitHub Project item lookup failed.')
    try:
        data = json.loads(result.stdout)
        if 'errors' in data:
            raise ValueError('GraphQL errors')
        project_data = data['data']['repository']['owner']['projectV2']
        listed = project_data['items']
        nodes = listed['nodes']
        if not project_data.get('id') or not isinstance(nodes, list) or listed['totalCount'] != len(nodes) or len(nodes) >= 100:
            raise ValueError('incomplete items')
        found = []
        for node in nodes:
            status_value = node['fieldValueByName']
            if status_value is not None and (not isinstance(status_value, dict) or not isinstance(status_value.get('name'), str) or not status_value['name']):
                raise ValueError('incomplete status')
            found.append({'id': node['id'], 'content': node['content'],
                          'status': status_value['name'] if status_value else None})
    except (KeyError, TypeError, ValueError, AttributeError):
        raise SystemExit('GitHub Project item lookup is incomplete.')
    return found

def _membership_query(graph, *variables):
    result = run(['gh', 'api', 'graphql', *variables, '-f', f'query={graph}'])
    try:
        payload = json.loads(result.stdout) if result.returncode == 0 else None
        if not isinstance(payload, dict) or 'errors' in payload:
            raise ValueError('failed query')
        return payload['data']
    except (KeyError, TypeError, ValueError):
        raise SystemExit('GitHub issue membership lookup failed or is incomplete.')


def _membership_item(node, url, project_id, expected_field):
    """Validate membership independently of a set or explicitly unset Status."""
    try:
        if (not isinstance(node['id'], str) or not node['id']
                or node['isArchived'] is not False
                or node['project']['id'] != project_id
                or node['content']['url'] != url):
            raise ValueError('mismatched membership')
        options = expected_field['options']
        if (expected_field['name'] != field
                or not isinstance(expected_field['id'], str) or not expected_field['id']
                or not isinstance(options, list)
                or any(not isinstance(option['id'], str) or not option['id']
                       or not isinstance(option['name'], str) or not option['name']
                       for option in options)):
            raise ValueError('invalid Status definition')
        # The key must exist; only an explicit null means a valid unset Status.
        status_value = node['fieldValueByName']
        if status_value is not None:
            status_field = status_value['field']
            if (status_field['name'] != field or status_field['id'] != expected_field['id']
                    or not isinstance(status_value['optionId'], str) or not status_value['optionId']
                    or status_value['name'] not in values.values()
                    or sum(option['id'] == status_value['optionId']
                           and option['name'] == status_value['name'] for option in options) != 1):
                raise ValueError('invalid Status value')
        return {'id': node['id'], 'content': {'url': url},
                'status': status_value['name'] if status_value is not None else None}
    except (KeyError, TypeError, ValueError):
        raise SystemExit('GitHub issue membership identity or Status is invalid.')


def _issue_membership(url):
    """Resolve only this issue when the Project connection omitted it; never cache."""
    require()
    match = re.fullmatch(
        re.escape(f'https://github.com/{owner}/{gh.get("repo")}/issues/') + r'([1-9][0-9]*)', url
    )
    if not match:
        raise SystemExit('Issue membership fallback requires the configured repository Issue URL.')
    graph = '''query($owner:String!, $repo:String!, $number:Int!, $issue:Int!, $field:String!) {
      repository(owner:$owner, name:$repo) {
        nameWithOwner owner {
          ... on User { projectV2(number:$number) { ...MembershipProject } }
          ... on Organization { projectV2(number:$number) { ...MembershipProject } }
        }
        issue(number:$issue) { url projectItems(first:100) { totalCount nodes {
          id isArchived project { id } content { ... on Issue { url } }
          fieldValueByName(name:$field) { ... on ProjectV2ItemFieldSingleSelectValue {
            name optionId field { ... on ProjectV2SingleSelectField { id name } }
          } }
        } } }
      }
    }
    fragment MembershipProject on ProjectV2 {
      id number field(name:$field) { ... on ProjectV2SingleSelectField {
        id name options { id name }
      } }
    }'''
    data = _membership_query(
        graph, '-f', f'owner={owner}', '-f', f'repo={gh.get("repo")}',
        '-F', f'number={project}', '-F', f'issue={match.group(1)}', '-f', f'field={field}',
    )
    try:
        repository = data['repository']
        target = repository['owner']['projectV2']
        issue = repository['issue']
        connection = issue['projectItems']
        nodes = connection['nodes']
        if (repository['nameWithOwner'] != f'{owner}/{gh.get("repo")}'
                or issue['url'] != url or target['number'] != project
                or not isinstance(target['id'], str) or not target['id']
                or not isinstance(nodes, list) or len(nodes) >= 100
                or connection['totalCount'] != len(nodes)):
            raise ValueError('incomplete membership')
        matches = [node for node in nodes if node['project']['id'] == target['id']]
        if len(matches) > 1:
            raise ValueError('ambiguous membership')
    except (KeyError, TypeError, ValueError):
        raise SystemExit('GitHub issue membership lookup is ambiguous, mismatched, or incomplete.')
    if not matches:
        # Verified absence is not permission to claim or update Status.
        return None
    snapshot = matches[0]
    item = _membership_item(snapshot, url, target['id'], target.get('field'))
    graph = '''query($id:ID!, $field:String!) {
      node(id:$id) { ... on ProjectV2Item {
        id isArchived project { id } content { ... on Issue { url } }
        fieldValueByName(name:$field) { ... on ProjectV2ItemFieldSingleSelectValue {
          name optionId field { ... on ProjectV2SingleSelectField { id name } }
        } }
      } }
    }'''
    fresh = _membership_query(graph, '-f', f'id={item["id"]}', '-f', f'field={field}')
    try:
        node = fresh['node']
        current = _membership_item(node, url, target['id'], target.get('field'))
        if current != item or node['fieldValueByName'] != snapshot['fieldValueByName']:
            raise ValueError('stale membership')
    except (KeyError, TypeError, ValueError):
        raise SystemExit('GitHub issue membership changed during lookup; retry from fresh state.')
    return current


def find_item(url, found):
    item = next((item for item in found if (item.get('content') or {}).get('url') == url), None)
    return item if item is not None else _issue_membership(url)

def add(url: str, known_new: bool = False):
    """Return (item, newly_added); keep existing items and statuses intact."""
    existing = None if known_new else find_item(url, items())
    if existing:
        if not existing.get('id'):
            raise SystemExit('GitHub Project item lookup returned no ID.')
        return existing, False
    result = run(['gh','project','item-add',str(project),'--owner',str(owner),'--url',url,'--format','json'])
    if result.returncode != 0:
        existing = find_item(url, items())
        if existing:
            if not existing.get('id'):
                raise SystemExit('GitHub Project item lookup returned no ID.')
            return existing, False
        raise SystemExit(result.stderr or 'GitHub Project item-add failed.')
    try:
        item = json.loads(result.stdout)
        if not item.get('id'):
            raise ValueError('missing item ID')
    except (ValueError, TypeError, AttributeError):
        raise SystemExit('Invalid GitHub Project item-add response.')
    for attempt in range(10):
        visible = find_item(url, items())
        if visible:
            return visible, True
        if attempt < 9:
            time.sleep(1)
    raise SystemExit(f'GitHub Project item not visible after add: {url}')

def status(url: str, logical_status: str, claim_owner: str | None = None):
    require()
    project_data = query(['view',str(project),'--owner',str(owner),'--format','json'])
    fields = query(['field-list',str(project),'--owner',str(owner),'--limit','10000','--format','json'])
    fields = fields.get('fields') if isinstance(fields, dict) else None
    if not isinstance(fields, list) or len(fields) >= 10000:
        raise SystemExit('GitHub Project field lookup is incomplete.')
    status_field = next((f for f in fields if f.get('name') == field), None)
    option = next((o for o in (status_field or {}).get('options', []) if o.get('name') == values.get(logical_status, logical_status)), None)
    if not isinstance(project_data, dict) or not project_data.get('id') or not status_field or not status_field.get('id') or not option or not option.get('id'):
        raise SystemExit(f'GitHub Project Status configuration is missing: {logical_status}')
    if claim_owner is not None:
        if logical_status != 'in_progress':
            raise SystemExit('Claim ownership guard applies only to In Progress.')
        issue = run(['gh', 'issue', 'view', url, '--json', 'assignees'])
        try:
            assignees = json.loads(issue.stdout)['assignees'] if issue.returncode == 0 else None
            owners = [a['login'].lower() for a in assignees]
        except (AttributeError, KeyError, TypeError, ValueError):
            raise SystemExit('Claim ownership could not be verified; status left unchanged.')
        if owners != [claim_owner.lower()]:
            raise SystemExit('Claim ownership changed; status left unchanged.')
    # Read live status at the mutation boundary, after ownership checks.
    item = None
    for attempt in range(10):
        item = find_item(url, items())
        if item:
            break
        if attempt < 9:
            time.sleep(1)
    if not item or not item.get('id'):
        raise SystemExit(f'GitHub Project item not found: {url}')
    if logical_status == 'backlog' and item.get('status'):
        return {'status': item['status'], 'skipped': True}
    if claim_owner is not None:
        current = item.get('status')
        if current == values.get('in_progress', 'In Progress'):
            return {'status': current, 'skipped': True}
        if current != values.get('ready', 'Ready'):
            raise SystemExit(f'Project status changed to {current!r}; In Progress write refused.')
    return query(['item-edit','--id',item['id'],'--project-id',project_data['id'],
                  '--field-id',status_field['id'],'--single-select-option-id',option['id'],'--format','json'])

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='cmd', required=True)
    add_parser = subparsers.add_parser('add'); add_parser.add_argument('url'); add_parser.add_argument('--status', dest='initial_status')
    status_parser = subparsers.add_parser('status'); status_parser.add_argument('url'); status_parser.add_argument('value', choices=['backlog','ready','in_progress','in_review','blocked','done'])
    args = parser.parse_args()
    if args.cmd == 'add':
        item, created = add(args.url)
        print(json.dumps(item))
        if args.initial_status and created:
            print(json.dumps(status(args.url, args.initial_status)))
    else:
        print(json.dumps(status(args.url, args.value)))

if __name__ == '__main__':
    main()
