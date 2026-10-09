from __future__ import annotations
import contextlib, copy, importlib, io, json, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import _common, claim_task, github_project, publish_tasks

def result(stdout='', returncode=0, stderr=''):
    return SimpleNamespace(stdout=stdout, returncode=returncode, stderr=stderr)

class PublicationTests(unittest.TestCase):
    def setUp(self):
        # These tests exercise the existing configured-Project path.
        for name, value in [('project_number', 1), ('check_claim_context', lambda *_: None),
                            ('run_network', lambda args: claim_task.run(args))]:
            patcher = patch.object(claim_task, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
    def test_issue_body_preserves_plan_metadata(self):
        task = {'key':'TASK-1','goal':'Goal','module':'team','acceptance_criteria':['Criterion'],
                'dependencies':['TASK-0'],'definition_of_ready':{'common':'Common gate','task':'Task gate'},
                'owner_specialty':'Backend Engineer','reviewers':'security, QA','risk':'high',
                'exit_evidence':'Review record'}
        body = publish_tasks.issue_body(task)
        for value in ('workspace-task-key: TASK-1','Goal','team','- [ ] Criterion','TASK-0',
                      'Common gate','Task gate','Backend Engineer','Unassigned','security, QA',
                      'high','Review record'):
            self.assertIn(value, body)
        self.assertIn('assign when claimed after Ready', body)
        self.assertNotIn('assign before Ready', body)

    def test_claim_prepares_branch_and_owner_before_progress(self):
        url = 'https://github.com/org/repo/issues/101'
        events = []
        state = {'owner':None, 'status':'Ready'}
        def read(path, default=None):
            return {'members':[{'id':'member-1','name':'A','github':'a'}]} if path.name == 'team.json' else {'member_id':'member-1'}
        def command(args):
            events.append(tuple(args))
            if args[:3] == ['gh','issue','view']:
                return result(json.dumps({'number':9,'url':url,'assignees':([{'login':state['owner']}] if state['owner'] else [])}))
            if args[:3] == ['git','branch','--show-current']:
                return result('main\n')
            if args[:3] == ['git','show-ref','--verify']:
                return result(returncode=1)
            if args[:3] == ['gh','issue','edit']:
                state['owner'] = 'a'
            return result()
        def progress(url, value, claim_owner):
            events.append(('status', url, value))
            state['status'] = 'In Progress'
        with patch.object(claim_task, 'read_json', side_effect=read), patch.object(claim_task, 'cmd_exists', return_value=True), patch.object(claim_task, 'run', side_effect=command), patch.object(claim_task, 'items', side_effect=lambda: [{'content':{'url':url},'status':state['status']}]), patch.object(claim_task, 'set_status', side_effect=progress), contextlib.redirect_stdout(io.StringIO()):
            claim_task.claim('9')
        self.assertLess(events.index(('git','switch','-c','task/issue-9')), events.index(('gh','issue','edit',url,'--add-assignee','a')))
        self.assertLess(events.index(('gh','issue','edit',url,'--add-assignee','a')), events.index(('status',url,'in_progress')))

    def test_claim_refuses_non_ready_task_before_mutation(self):
        url = 'https://github.com/org/repo/issues/101'
        events = []
        def read(path, default=None):
            return {'members':[{'id':'member-1','name':'A','github':'a'}]} if path.name == 'team.json' else {'member_id':'member-1'}
        def command(args):
            events.append(tuple(args))
            return result(json.dumps({'number':9,'url':url,'assignees':[]})) if args[:3] == ['gh','issue','view'] else result()
        with patch.object(claim_task, 'read_json', side_effect=read), patch.object(claim_task, 'cmd_exists', return_value=True), patch.object(claim_task, 'run', side_effect=command), patch.object(claim_task, 'items', return_value=[{'content':{'url':url},'status':'Backlog'}]), patch.object(claim_task, 'set_status') as status:
            with self.assertRaises(SystemExit):
                claim_task.claim('9')
            status.assert_not_called()
        self.assertFalse(any(args[:2] == ('git','switch') or args[:3] == ('gh','issue','edit') for args in events))

    def test_claim_retries_after_assignment_failure_on_existing_branch(self):
        url = 'https://github.com/org/repo/issues/101'
        state = {'branch':'main', 'owner':None, 'status':'Ready', 'edits':0}
        def read(path, default=None):
            return {'members':[{'id':'member-1','name':'A','github':'a'}]} if path.name == 'team.json' else {'member_id':'member-1'}
        def command(args):
            if args[:3] == ['gh','issue','view']:
                return result(json.dumps({'number':9,'url':url,'assignees':([{'login':state['owner']}] if state['owner'] else [])}))
            if args[:3] == ['git','branch','--show-current']:
                return result(state['branch'])
            if args[:3] == ['git','show-ref','--verify']:
                return result(returncode=1)
            if args[:3] == ['git','switch','-c']:
                state['branch'] = args[3]
            if args[:3] == ['gh','issue','edit']:
                state['edits'] += 1
                if state['edits'] == 1:
                    return result(returncode=1, stderr='assignment failed')
                state['owner'] = 'a'
            return result()
        def progress(url, value, claim_owner):
            self.assertEqual(state['owner'], 'a')
            state['status'] = 'In Progress'
        with patch.object(claim_task, 'read_json', side_effect=read), patch.object(claim_task, 'cmd_exists', return_value=True), patch.object(claim_task, 'run', side_effect=command), patch.object(claim_task, 'items', side_effect=lambda: [{'content':{'url':url},'status':state['status']}]), patch.object(claim_task, 'set_status', side_effect=progress), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                claim_task.claim('9')
            self.assertEqual((state['branch'], state['owner'], state['status']), ('task/issue-9', None, 'Ready'))
            claim_task.claim('9')
        self.assertEqual((state['edits'], state['status']), (2, 'In Progress'))

    def test_claim_retries_after_project_status_failure(self):
        url = 'https://github.com/org/repo/issues/101'
        for status_applied_before_failure in (False, True):
            with self.subTest(status_applied_before_failure=status_applied_before_failure):
                state = {'branch':'main', 'owner':None, 'status':'Ready', 'edits':0, 'transitions':0}
                def read(path, default=None):
                    return {'members':[{'id':'member-1','name':'A','github':'a'}]} if path.name == 'team.json' else {'member_id':'member-1'}
                def command(args):
                    if args[:3] == ['gh','issue','view']:
                        return result(json.dumps({'number':9,'url':url,'assignees':([{'login':state['owner']}] if state['owner'] else [])}))
                    if args[:3] == ['git','branch','--show-current']:
                        return result(state['branch'])
                    if args[:3] == ['git','show-ref','--verify']:
                        return result(returncode=1)
                    if args[:3] == ['git','switch','-c']:
                        state['branch'] = args[3]
                    if args[:3] == ['gh','issue','edit']:
                        state['edits'] += 1
                        state['owner'] = 'a'
                    return result()
                def progress(url, value, claim_owner):
                    if state['status'] == 'In Progress':
                        return {'skipped':True}
                    state['transitions'] += 1
                    if state['transitions'] == 1:
                        if status_applied_before_failure:
                            state['status'] = 'In Progress'
                        raise SystemExit('status update failed')
                    state['status'] = 'In Progress'
                with patch.object(claim_task, 'read_json', side_effect=read), patch.object(claim_task, 'cmd_exists', return_value=True), patch.object(claim_task, 'run', side_effect=command), patch.object(claim_task, 'items', side_effect=lambda: [{'content':{'url':url},'status':state['status']}]), patch.object(claim_task, 'set_status', side_effect=progress), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        claim_task.claim('9')
                    claim_task.claim('9')
                self.assertEqual((state['owner'], state['status'], state['edits']), ('a', 'In Progress', 1))
                self.assertEqual(state['transitions'], 1 if status_applied_before_failure else 2)

    def test_claim_preserves_other_ownership_and_progress(self):
        url = 'https://github.com/org/repo/issues/101'
        def read(path, default=None):
            return {'members':[{'id':'member-1','name':'A','github':'a'}]} if path.name == 'team.json' else {'member_id':'member-1'}
        for status, assignees in [('Ready',[{'login':'other'}]), ('In Progress',[{'login':'other'}]), ('Done',[{'login':'a'}])]:
            with self.subTest(status=status), patch.object(claim_task, 'read_json', side_effect=read), patch.object(claim_task, 'cmd_exists', return_value=True), patch.object(claim_task, 'run', side_effect=[result(), result(json.dumps({'number':9,'url':url,'assignees':assignees}))]) as run, patch.object(claim_task, 'items', return_value=[{'content':{'url':url},'status':status}]), patch.object(claim_task, 'set_status') as progress:
                with self.assertRaises(SystemExit):
                    claim_task.claim('9')
                self.assertEqual(run.call_count, 2)
                progress.assert_not_called()

    def test_claim_reuses_existing_task_worktree(self):
        commands = []
        def command(args):
            commands.append(tuple(args))
            if args[:3] == ['git','branch','--show-current']:
                return result('main\n')
            if args[:3] == ['git','worktree','list']:
                return result('worktree C:/repo\nbranch refs/heads/main\n\nworktree C:/task-9\nbranch refs/heads/task/issue-9\n')
            return result()
        with patch.object(claim_task, 'run', side_effect=command):
            self.assertEqual(claim_task.prepare_branch('task/issue-9'), 'C:/task-9')
        self.assertFalse(any(args[:2] == ('git','switch') for args in commands))

    def test_claim_refuses_owner_who_claims_after_initial_read(self):
        url = 'https://github.com/org/repo/issues/101'
        views = 0
        edits = []
        def read(path, default=None):
            return {'members':[{'id':'member-1','name':'A','github':'a'}]} if path.name == 'team.json' else {'member_id':'member-1'}
        def command(args):
            nonlocal views
            if args[:3] == ['gh','issue','view']:
                views += 1
                assignees = [] if views == 1 else [{'login':'other'}]
                return result(json.dumps({'number':9,'url':url,'assignees':assignees}))
            if args[:3] == ['git','branch','--show-current']:
                return result('task/issue-9')
            if args[:3] == ['gh','issue','edit']:
                edits.append(args)
            return result()
        with patch.object(claim_task, 'read_json', side_effect=read), patch.object(claim_task, 'cmd_exists', return_value=True), patch.object(claim_task, 'run', side_effect=command), patch.object(claim_task, 'items', return_value=[{'content':{'url':url},'status':'Ready'}]), patch.object(claim_task, 'set_status') as progress:
            with self.assertRaisesRegex(SystemExit, 'Competing owner'):
                claim_task.claim('9')
            self.assertEqual(edits, [])
            progress.assert_not_called()

    def test_claim_compensates_only_its_assignment_after_concurrent_claim(self):
        url = 'https://github.com/org/repo/issues/101'
        state = {'owners':[], 'edits':[]}
        def read(path, default=None):
            return {'members':[{'id':'member-1','name':'A','github':'a'}]} if path.name == 'team.json' else {'member_id':'member-1'}
        def command(args):
            if args[:3] == ['gh','issue','view']:
                return result(json.dumps({'number':9,'url':url,'assignees':[{'login':x} for x in state['owners']]}))
            if args[:3] == ['git','branch','--show-current']:
                return result('task/issue-9')
            if args[:3] == ['gh','issue','edit']:
                state['edits'].append(tuple(args))
                if '--add-assignee' in args:
                    state['owners'] = ['other', 'a']
                elif '--remove-assignee' in args:
                    state['owners'].remove('a')
            return result()
        with patch.object(claim_task, 'read_json', side_effect=read), patch.object(claim_task, 'cmd_exists', return_value=True), patch.object(claim_task, 'run', side_effect=command), patch.object(claim_task, 'items', return_value=[{'content':{'url':url},'status':'Ready'}]), patch.object(claim_task, 'set_status') as progress, contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaisesRegex(SystemExit, 'Competing'):
                claim_task.claim('9')
            progress.assert_not_called()
        self.assertEqual(state['owners'], ['other'])
        self.assertEqual(state['edits'][-1], ('gh','issue','edit',url,'--remove-assignee','a'))
        self.assertNotIn('TASK CLAIM RESULT', output.getvalue())

    def test_claim_detects_competing_owner_after_status_mutation(self):
        url = 'https://github.com/org/repo/issues/101'
        state = {'owners':[], 'status':'Ready', 'removed':False}
        def read(path, default=None):
            return {'members':[{'id':'member-1','name':'A','github':'a'}]} if path.name == 'team.json' else {'member_id':'member-1'}
        def command(args):
            if args[:3] == ['gh','issue','view']:
                return result(json.dumps({'number':9,'url':url,'assignees':[{'login':x} for x in state['owners']]}))
            if args[:3] == ['git','branch','--show-current']:
                return result('task/issue-9')
            if args[:3] == ['gh','issue','edit']:
                if '--add-assignee' in args:
                    state['owners'] = ['a']
                else:
                    state['owners'].remove('a')
                    state['removed'] = True
            return result()
        def progress(url, value, claim_owner):
            state['status'] = 'In Progress'
            state['owners'].append('other')
        with patch.object(claim_task, 'read_json', side_effect=read), patch.object(claim_task, 'cmd_exists', return_value=True), patch.object(claim_task, 'run', side_effect=command), patch.object(claim_task, 'items', side_effect=lambda: [{'content':{'url':url},'status':state['status']}]), patch.object(claim_task, 'set_status', side_effect=progress), contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaisesRegex(SystemExit, 'Competing'):
                claim_task.claim('9')
        self.assertEqual(state['owners'], ['other'])
        self.assertTrue(state['removed'])
        self.assertNotIn('TASK CLAIM RESULT', output.getvalue())

    def test_status_helper_refuses_progress_between_claim_check_and_mutation(self):
        url = 'https://github.com/org/repo/issues/101'
        def read(path, default=None):
            return {'members':[{'id':'member-1','name':'A','github':'a'}]} if path.name == 'team.json' else {'member_id':'member-1'}
        def command(args):
            if args[:3] == ['gh','issue','view']:
                return result(json.dumps({'number':9,'url':url,'assignees':[{'login':'a'}]}))
            if args[:3] == ['git','branch','--show-current']:
                return result('task/issue-9')
            return result()
        def query(args):
            if args[0] == 'view': return {'id':'project-1'}
            if args[0] == 'field-list': return {'fields':[{'id':'field-1','name':'Status','options':[{'id':'option-1','name':'In Progress'}]}]}
            self.fail(f'Status mutation attempted: {args}')
        for progressed in ('In Review', 'Blocked', 'Done', 'Custom status'):
            with self.subTest(progressed=progressed), patch.object(claim_task, 'read_json', side_effect=read), patch.object(claim_task, 'cmd_exists', return_value=True), patch.object(claim_task, 'run', side_effect=command), patch.object(claim_task, 'items', return_value=[{'content':{'url':url},'status':'Ready'}]), patch.object(claim_task, 'set_status', side_effect=github_project.status), patch.object(github_project, 'require'), patch.object(github_project, 'run', return_value=result('{"assignees":[{"login":"a"}]}')), patch.object(github_project, 'items', return_value=[{'id':'item-1','content':{'url':url},'status':progressed}]), patch.object(github_project, 'query', side_effect=query) as project_query:
                with self.assertRaisesRegex(SystemExit, progressed):
                    claim_task.claim('9')
                self.assertEqual(project_query.call_count, 2)

    def test_claim_status_helper_accepts_ready_and_skips_same_claim_progress(self):
        url = 'https://github.com/org/repo/issues/101'
        def query(args):
            if args[0] == 'view': return {'id':'project-1'}
            if args[0] == 'field-list': return {'fields':[{'id':'field-1','name':'Status','options':[{'id':'option-1','name':'In Progress'}]}]}
            if args[0] == 'item-edit': return {'updated':True}
            self.fail(f'Unexpected Project query: {args}')
        for current in ('Ready', 'In Progress'):
            with self.subTest(current=current), patch.object(github_project, 'require'), patch.object(github_project, 'run', return_value=result('{"assignees":[{"login":"a"}]}')), patch.object(github_project, 'items', return_value=[{'id':'item-1','content':{'url':url},'status':current}]), patch.object(github_project, 'query', side_effect=query) as project_query:
                outcome = github_project.status(url, 'in_progress', claim_owner='a')
                self.assertEqual(outcome, {'updated':True} if current == 'Ready' else {'status':'In Progress','skipped':True})
                self.assertEqual(project_query.call_count, 3 if current == 'Ready' else 2)

    def test_claim_status_helper_refuses_owner_changed_at_mutation_boundary(self):
        url = 'https://github.com/org/repo/issues/101'
        def query(args):
            if args[0] == 'view': return {'id':'project-1'}
            if args[0] == 'field-list': return {'fields':[{'id':'field-1','name':'Status','options':[{'id':'option-1','name':'In Progress'}]}]}
            self.fail(f'Status mutation attempted: {args}')
        with patch.object(github_project, 'require'), patch.object(github_project, 'run', return_value=result('{"assignees":[{"login":"a"},{"login":"other"}]}')), patch.object(github_project, 'items') as live_items, patch.object(github_project, 'query', side_effect=query) as project_query:
            with self.assertRaisesRegex(SystemExit, 'ownership changed'):
                github_project.status(url, 'in_progress', claim_owner='a')
            live_items.assert_not_called()
            self.assertEqual(project_query.call_count, 2)

    def test_status_waits_for_new_project_item_visibility(self):
        url = 'https://github.com/org/repo/issues/1'
        item = {'id':'item-1','content':{'url':url}}
        def query(args):
            if args[0] == 'view': return {'id':'project-1'}
            if args[0] == 'field-list': return {'fields':[{'id':'field-1','name':'Status','options':[{'id':'option-1','name':'Backlog'}]}]}
            if args[0] == 'item-edit': return {}
            self.fail(f'Unexpected Project query: {args}')
        with patch.object(github_project, 'require'), patch.object(github_project, 'items', side_effect=[[],[item]]) as items, patch.object(github_project, '_issue_membership', return_value=None), patch.object(github_project.time, 'sleep') as sleep, patch.object(github_project, 'query', side_effect=query):
            self.assertEqual(github_project.status(url, 'backlog'), {})
            self.assertEqual(items.call_count, 2)
            sleep.assert_called_once_with(1)

    def test_helper_import_does_not_parse_command_line(self):
        with patch.object(sys, 'argv', ['unrelated-command', '--unexpected']):
            importlib.reload(github_project)
            importlib.reload(publish_tasks)

    def setup_plan(self, root, tasks):
        (root/'.orchestrator').mkdir()
        (root/'docs/plans').mkdir(parents=True)
        architecture = {
            'status': 'approved',
            'completed_sections': list(_common.PROFESSIONAL_ARCHITECTURE_SECTIONS),
            'approval': None,
        }
        (root/'.orchestrator/architecture-state.json').write_text(json.dumps(architecture))
        (root/'workspace.config.json').write_text('{"operating_mode":"professional","github":{"owner":"org","repo":"repo","project_number":1}}')
        (root/'docs/plans/approved-tasks.json').write_text(json.dumps(tasks))

    def test_lookup_failure_or_incomplete_response_creates_nothing(self):
        task = {'key':'TASK-1','title':'Task','dependencies':[]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.setup_plan(root, [task])
            for response in (result(returncode=1, stderr='API unavailable'), result('[[{"body":null}]]')):
                with self.subTest(response=response), patch.object(publish_tasks, 'ROOT', root), patch.object(publish_tasks, 'ORCH', root/'.orchestrator'), patch.object(publish_tasks, 'project_require'), patch.object(publish_tasks, 'run', return_value=response) as run, patch.object(publish_tasks, 'project_add') as add:
                    with self.assertRaises(SystemExit):
                        publish_tasks.publish()
                    self.assertEqual(run.call_count, 1)
                    add.assert_not_called()

    def test_missing_body_field_stops_before_issue_creation(self):
        task = {'key':'TASK-1','title':'Task','dependencies':[]}
        response = result('[[{"html_url":"https://github.com/org/repo/issues/1"}]]')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.setup_plan(root, [task])
            with patch.object(publish_tasks, 'ROOT', root), patch.object(publish_tasks, 'ORCH', root/'.orchestrator'), patch.object(publish_tasks, 'project_require'), patch.object(publish_tasks, 'run', return_value=response) as run, patch.object(publish_tasks, 'project_add') as add:
                with self.assertRaisesRegex(SystemExit, 'Invalid GitHub issue lookup response'):
                    publish_tasks.publish()
                self.assertEqual(run.call_count, 1)
                add.assert_not_called()

    def test_null_body_field_is_valid(self):
        issue = {'body':None,'html_url':'https://github.com/org/repo/issues/1'}
        with patch.object(publish_tasks, 'run', return_value=result(json.dumps([[issue]]))):
            self.assertEqual(publish_tasks.issue_lookup('org/repo'), [issue])

    def test_rerun_reuses_issue_and_preserves_existing_item_status(self):
        task = {'key':'TASK-1','title':'Task','dependencies':[]}
        url = 'https://github.com/org/repo/issues/1'
        issues = []
        calls = []
        def gh(cmd):
            calls.append(cmd)
            if cmd[:2] == ['gh','api']:
                return result(json.dumps([issues]))
            if cmd[:3] == ['gh','issue','create']:
                body = cmd[cmd.index('--body')+1]
                issues.append({'body':body,'html_url':url})
                return result(url)
            self.fail(f'Unexpected command: {cmd}')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.setup_plan(root, [task])
            with patch.object(publish_tasks, 'ROOT', root), patch.object(publish_tasks, 'ORCH', root/'.orchestrator'), patch.object(publish_tasks, 'project_require'), patch.object(publish_tasks, 'run', side_effect=gh), patch.object(publish_tasks, 'project_add', side_effect=[({'id':'item'},True), ({'id':'item','status':'In Progress'},False)]) as add, patch.object(publish_tasks, 'project_status') as status, contextlib.redirect_stdout(io.StringIO()):
                publish_tasks.publish()
                publish_tasks.publish()
            self.assertEqual(sum(cmd[:3] == ['gh','issue','create'] for cmd in calls), 1)
            self.assertEqual(add.call_count, 2)
            status.assert_called_once_with(url, 'backlog')

    def test_first_publication_preserves_existing_progressed_project_item(self):
        task = {'key':'TASK-1','title':'Task','dependencies':[]}
        url = 'https://github.com/org/repo/issues/1'
        calls = []
        def gh(cmd):
            calls.append(cmd)
            if cmd[:2] == ['gh','api']:
                return result('[[]]')
            if cmd[:3] == ['gh','issue','create']:
                return result(url)
            self.fail(f'Unexpected command: {cmd}')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.setup_plan(root, [task])
            for progressed in ('In Progress', 'Done'):
                with self.subTest(status=progressed), patch.object(publish_tasks, 'ROOT', root), patch.object(publish_tasks, 'ORCH', root/'.orchestrator'), patch.object(publish_tasks, 'project_require'), patch.object(publish_tasks, 'run', side_effect=gh), patch.object(publish_tasks, 'project_add', return_value=({'id':'item-1','status':progressed},False)) as add, patch.object(publish_tasks, 'project_status') as status, contextlib.redirect_stdout(io.StringIO()):
                    publish_tasks.publish()
                    add.assert_called_once_with(url, known_new=True)
                    status.assert_not_called()
            self.assertEqual(sum(cmd[:3] == ['gh','issue','create'] for cmd in calls), 2)

    def test_failed_backlog_assignment_is_recovered_on_rerun(self):
        task = {'key':'TASK-1','title':'Task','dependencies':[]}
        url = 'https://github.com/org/repo/issues/1'
        issues = []
        items = []
        calls = []
        def gh(cmd):
            calls.append(cmd)
            if cmd[:2] == ['gh','api']:
                return result(json.dumps([issues]))
            if cmd[:3] == ['gh','issue','create']:
                issues.append({'body':cmd[cmd.index('--body')+1],'html_url':url})
                return result(url)
            if cmd[:3] == ['gh','project','item-add']:
                item = {'id':'item-1','content':{'url':url}}
                items.append(item)
                return result(json.dumps(item))
            if cmd[:3] == ['gh','project','view']:
                return result('{"id":"project-1"}')
            if cmd[:3] == ['gh','project','field-list']:
                return result('{"fields":[{"id":"field-1","name":"Status","options":[{"id":"option-1","name":"Backlog"}]}]}')
            if cmd[:3] == ['gh','project','item-edit']:
                edits = sum(call[:3] == ['gh','project','item-edit'] for call in calls)
                if edits == 1:
                    return result(returncode=1, stderr='Status update failed')
                items[0]['status'] = 'Backlog'
                return result('{}')
            self.fail(f'Unexpected command: {cmd}')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.setup_plan(root, [task])
            with patch.object(publish_tasks, 'ROOT', root), patch.object(publish_tasks, 'ORCH', root/'.orchestrator'), patch.object(publish_tasks, 'project_require'), patch.object(publish_tasks, 'run', side_effect=gh), patch.object(github_project, 'require'), patch.object(github_project, 'run', side_effect=gh), patch.object(github_project, 'items', side_effect=lambda: items), patch.object(github_project, 'owner', 'org'), patch.object(github_project, 'project', 1), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(SystemExit, 'Status update failed'):
                    publish_tasks.publish()
                self.assertNotIn('status', items[0])
                publish_tasks.publish()
                publish_tasks.publish()
            self.assertEqual(sum(cmd[:3] == ['gh','issue','create'] for cmd in calls), 1)
            self.assertEqual(sum(cmd[:3] == ['gh','project','item-add'] for cmd in calls), 1)
            self.assertEqual(sum(cmd[:3] == ['gh','project','item-edit'] for cmd in calls), 2)
            self.assertEqual(items[0]['status'], 'Backlog')

    def test_duplicate_plan_keys_stop_before_issue_lookup(self):
        tasks = [{'key':'TASK-1','title':'First'}, {'key':'TASK-1','title':'Second'}]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.setup_plan(root, tasks)
            with patch.object(publish_tasks, 'ROOT', root), patch.object(publish_tasks, 'ORCH', root/'.orchestrator'), patch.object(publish_tasks, 'run') as run:
                with self.assertRaisesRegex(SystemExit, 'Duplicate task keys'):
                    publish_tasks.publish()
                run.assert_not_called()

    def test_duplicate_existing_issue_keys_stop_before_creation(self):
        marker = 'workspace-task-key: TASK-1'
        issues = [[{'body':marker,'html_url':'https://github.com/org/repo/issues/1'},
                   {'body':marker,'html_url':'https://github.com/org/repo/issues/2'}]]
        task = {'key':'TASK-1','title':'Task'}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.setup_plan(root, [task])
            with patch.object(publish_tasks, 'ROOT', root), patch.object(publish_tasks, 'ORCH', root/'.orchestrator'), patch.object(publish_tasks, 'project_require'), patch.object(publish_tasks, 'run', return_value=result(json.dumps(issues))) as run, patch.object(publish_tasks, 'project_add') as add:
                with self.assertRaisesRegex(SystemExit, 'Duplicate GitHub issues'):
                    publish_tasks.publish()
                self.assertEqual(run.call_count, 1)
                add.assert_not_called()

    def test_existing_issue_new_project_item_starts_backlog(self):
        url = 'https://github.com/org/repo/issues/1'
        task = {'key':'TASK-1','title':'Task','dependencies':[]}
        issues = [[{'body':'workspace-task-key: TASK-1','html_url':url}]]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.setup_plan(root, [task])
            with patch.object(publish_tasks, 'ROOT', root), patch.object(publish_tasks, 'ORCH', root/'.orchestrator'), patch.object(publish_tasks, 'project_require'), patch.object(publish_tasks, 'run', return_value=result(json.dumps(issues))) as run, patch.object(publish_tasks, 'project_add', return_value=({'id':'item'},True)), patch.object(publish_tasks, 'project_status') as status, contextlib.redirect_stdout(io.StringIO()):
                publish_tasks.publish()
                self.assertEqual(run.call_count, 1)
                status.assert_called_once_with(url, 'backlog')

    def test_existing_project_item_is_not_added_or_reset(self):
        url = 'https://github.com/org/repo/issues/1'
        item = {'id':'item-1','content':{'url':url},'status':'In Progress'}
        with patch.object(github_project, 'require'), patch.object(github_project, 'items', return_value=[item]) as listed, patch.object(github_project, 'run') as run:
            self.assertEqual(github_project.add(url), (item, False))
            listed.assert_called_once_with()
            run.assert_not_called()

    def test_new_issue_already_on_project_keeps_progressed_status(self):
        url = 'https://github.com/org/repo/issues/1'
        item = {'id':'item-1','content':{'url':url},'status':'In Progress'}
        with patch.object(github_project, 'items', return_value=[item]) as listed, patch.object(github_project, 'run', return_value=result('{"id":"item-1"}')):
            self.assertEqual(github_project.add(url, known_new=True), (item, True))
            listed.assert_called_once_with()

    def test_new_project_item_gets_real_id_based_status_update(self):
        url = 'https://github.com/org/repo/issues/1'
        item = {'id':'item-1','content':{'url':url}}
        def gh(cmd):
            command = cmd[2]
            if command == 'item-list': return result(json.dumps({'items':[item]}))
            if command == 'view': return result('{"id":"project-1"}')
            if command == 'field-list': return result('{"fields":[{"id":"field-1","name":"Status","options":[{"id":"option-1","name":"Backlog"}]}]}')
            if command == 'item-edit':
                self.assertIn('--id', cmd); self.assertIn('item-1', cmd)
                self.assertIn('--project-id', cmd); self.assertIn('project-1', cmd)
                self.assertIn('--field-id', cmd); self.assertIn('field-1', cmd)
                self.assertIn('--single-select-option-id', cmd); self.assertIn('option-1', cmd)
                self.assertNotIn('--url', cmd)
                return result('{}')
            self.fail(f'Unexpected command: {cmd}')
        with patch.object(github_project, 'require'), patch.object(github_project, 'run', side_effect=gh), patch.object(github_project, 'items', return_value=[item]):
            self.assertEqual(github_project.status(url, 'backlog'), {})

    def test_project_lookup_uses_complete_lightweight_graphql_response(self):
        url = 'https://github.com/org/repo/issues/1'
        data = {'data':{'repository':{'owner':{'projectV2':{'id':'project-1','items':{
            'totalCount':1,'nodes':[{'id':'item-1','content':{'url':url},'fieldValueByName':{'name':'Backlog'}}]}}}}}}
        with patch.object(github_project, 'require'), patch.object(github_project, 'run', return_value=result(json.dumps(data))) as run:
            self.assertEqual(github_project.items(), [{'id':'item-1','content':{'url':url},'status':'Backlog'}])
            self.assertEqual(run.call_args.args[0][:3], ['gh','api','graphql'])
            data['data']['repository']['owner']['projectV2']['items']['totalCount'] = 2
            run.return_value = result(json.dumps(data))
            with self.assertRaisesRegex(SystemExit, 'incomplete'):
                github_project.items()

    def test_partial_graphql_status_never_triggers_backlog_write(self):
        url = 'https://github.com/org/repo/issues/1'
        node = {'id':'item-1','content':{'url':url},'fieldValueByName':None}
        payload = {
            'data': {'repository': {'owner': {'projectV2': {
                'id': 'project-1', 'items': {'totalCount': 1, 'nodes': [node]}
            }}}},
            'errors': [{'message': 'Status resolution failed'}],
        }
        def query(args):
            if args[0] == 'view': return {'id':'project-1'}
            if args[0] == 'field-list': return {'fields':[{'id':'field-1','name':'Status','options':[{'id':'option-1','name':'Backlog'}]}]}
            self.fail(f'Status mutation attempted: {args}')
        with patch.object(github_project, 'require'), patch.object(github_project, 'run', return_value=result(json.dumps(payload))) as run, patch.object(github_project, 'query', side_effect=query) as project_query:
            with self.assertRaisesRegex(SystemExit, 'incomplete'):
                github_project.status(url, 'backlog')
            self.assertEqual(project_query.call_count, 2)
            run.assert_called_once()
            del payload['errors']
            del node['fieldValueByName']
            run.return_value = result(json.dumps(payload))
            with self.assertRaisesRegex(SystemExit, 'incomplete'):
                github_project.status(url, 'backlog')
            self.assertEqual(project_query.call_count, 4)

    def test_backlog_rechecks_status_after_stale_publication_snapshot(self):
        task = {'key':'TASK-1','title':'Task','dependencies':[]}
        url = 'https://github.com/org/repo/issues/1'
        issues = [[{'body':'workspace-task-key: TASK-1','html_url':url}]]
        def query(args):
            if args[0] == 'view': return {'id':'project-1'}
            if args[0] == 'field-list': return {'fields':[{'id':'field-1','name':'Status','options':[{'id':'option-1','name':'Backlog'}]}]}
            self.fail(f'Status mutation attempted: {args}')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.setup_plan(root, [task])
            for progressed in ('Ready','In Progress','In Review','Blocked','Done','Custom status'):
                current = {'id':'item-1','content':{'url':url},'status':progressed}
                with self.subTest(status=progressed), patch.object(publish_tasks, 'ROOT', root), patch.object(publish_tasks, 'ORCH', root/'.orchestrator'), patch.object(publish_tasks, 'project_require'), patch.object(publish_tasks, 'run', return_value=result(json.dumps(issues))), patch.object(publish_tasks, 'project_add', return_value=({'id':'item-1','status':None},False)), patch.object(publish_tasks, 'project_status', side_effect=github_project.status), patch.object(github_project, 'require'), patch.object(github_project, 'items', return_value=[current]) as live_items, patch.object(github_project, 'query', side_effect=query) as project_query, contextlib.redirect_stdout(io.StringIO()):
                    publish_tasks.publish()
                    live_items.assert_called_once_with()
                    self.assertEqual(project_query.call_count, 2)

class IssueMembershipFallbackTests(unittest.TestCase):
    def setUp(self):
        for name, value in [('project_number', 1), ('check_claim_context', lambda *_: None),
                            ('run_network', lambda args: claim_task.run(args))]:
            patcher = patch.object(claim_task, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.url = 'https://github.com/org/repo/issues/7'
        self.status_values = dict(zip(
            ('backlog', 'ready', 'in_progress', 'in_review', 'blocked', 'done'),
            ('Backlog', 'Ready', 'In Progress', 'In Review', 'Blocked', 'Done'),
        ))
        self.status_field = {'id': 'field-1', 'name': 'Status', 'options': [
            {'id': name, 'name': name} for name in self.status_values.values()
        ]}
        self.node = {
            'id': 'item-1', 'isArchived': False, 'project': {'id': 'project-1'},
            'content': {'url': self.url},
            'fieldValueByName': {'name': 'Backlog', 'optionId': 'Backlog',
                                 'field': {'id': 'field-1', 'name': 'Status'}},
        }
        self.repository = {
            'nameWithOwner': 'org/repo',
            'owner': {'projectV2': {'id': 'project-1', 'number': 1, 'field': self.status_field}},
            'issue': {'url': self.url, 'projectItems': {'totalCount': 1, 'nodes': [self.node]}},
        }
        self.payload = {'data': {'repository': self.repository}}
        self.fresh = {'data': {'node': copy.deepcopy(self.node)}}
        self.assignees = [{'login': 'a'}]
        self.edits = []
        for name, value in (
            ('require', lambda: None), ('owner', 'org'), ('project', 1), ('field', 'Status'),
            ('gh', {'repo': 'repo'}), ('values', self.status_values),
        ):
            patcher = patch.object(github_project, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(github_project, 'run', side_effect=self.command)
        self.run = patcher.start()
        self.addCleanup(patcher.stop)

    def command(self, args):
        if args[:3] == ['gh', 'api', 'graphql']:
            payload = self.fresh if 'id=item-1' in args else self.payload
            return result(json.dumps(payload))
        if args[:3] == ['gh', 'issue', 'view']:
            return result(json.dumps({'assignees': self.assignees}))
        self.fail(f'Unexpected command or mutation: {args}')

    def project_query(self, args):
        if args[0] == 'view':
            return {'id': 'project-1'}
        if args[0] == 'field-list':
            return {'fields': [self.status_field]}
        if args[0] == 'item-edit':
            self.edits.append(args)
            return {'updated': True}
        self.fail(f'Unexpected Project command: {args}')

    def set_status(self, status):
        for node in (self.node, self.fresh['data']['node']):
            node['fieldValueByName']['name'] = status
            node['fieldValueByName']['optionId'] = status

    def test_normal_enumeration_does_not_use_fallback(self):
        item = {'id': 'item-1', 'content': {'url': self.url}, 'status': 'Ready'}
        self.assertIs(github_project.find_item(self.url, [item]), item)
        self.run.assert_not_called()

    def test_empty_enumeration_finds_verified_existing_membership(self):
        self.assertEqual(github_project.find_item(self.url, []), {
            'id': 'item-1', 'content': {'url': self.url}, 'status': 'Backlog',
        })
        self.assertEqual(self.run.call_count, 2)

    def test_existing_membership_is_not_readded(self):
        with patch.object(github_project, 'items', return_value=[]):
            item, added = github_project.add(self.url)
        self.assertFalse(added)
        self.assertEqual(item['id'], 'item-1')
        self.assertEqual(self.run.call_count, 2)

    def test_valid_unset_status_membership_is_found_and_reused(self):
        self.node['fieldValueByName'] = None
        self.fresh['data']['node']['fieldValueByName'] = None
        with patch.object(github_project, 'items', return_value=[]):
            item, added = github_project.add(self.url)
        self.assertEqual(item, {'id': 'item-1', 'content': {'url': self.url}, 'status': None})
        self.assertFalse(added)
        self.assertEqual(self.run.call_count, 2)

    def test_unset_status_can_be_initialized_to_backlog(self):
        self.node['fieldValueByName'] = None
        self.fresh['data']['node']['fieldValueByName'] = None
        with patch.object(github_project, 'items', return_value=[]), patch.object(
            github_project, 'query', side_effect=self.project_query
        ):
            self.assertEqual(github_project.status(self.url, 'backlog'), {'updated': True})
        self.assertEqual(len(self.edits), 1)
        self.assertIn('item-1', self.edits[0])
        self.assertEqual(self.edits[0][self.edits[0].index('--single-select-option-id') + 1], 'Backlog')

    def test_publication_reuses_unset_existing_issue_and_initializes_backlog_once(self):
        self.node['fieldValueByName'] = None
        self.fresh['data']['node']['fieldValueByName'] = None
        issues = [[{'body': 'workspace-task-key: TASK-1', 'html_url': self.url}]]
        def query(args):
            outcome = self.project_query(args)
            if args[0] == 'item-edit':
                for node in (self.node, self.fresh['data']['node']):
                    node['fieldValueByName'] = {
                        'name': 'Backlog', 'optionId': 'Backlog',
                        'field': {'id': 'field-1', 'name': 'Status'},
                    }
            return outcome
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            PublicationTests.setup_plan(self, root, [{'key': 'TASK-1', 'title': 'Task'}])
            with patch.object(publish_tasks, 'ROOT', root), patch.object(
                publish_tasks, 'ORCH', root / '.orchestrator'
            ), patch.object(publish_tasks, 'project_require'), patch.object(
                publish_tasks, 'run', return_value=result(json.dumps(issues))
            ) as publication_run, patch.object(github_project, 'items', return_value=[]), patch.object(
                github_project, 'query', side_effect=query
            ), contextlib.redirect_stdout(io.StringIO()):
                publish_tasks.publish()
                publish_tasks.publish()
        self.assertEqual(publication_run.call_count, 2)
        self.assertTrue(all(call.args[0][:2] == ['gh', 'api'] for call in publication_run.call_args_list))
        self.assertEqual(len(self.edits), 1)
        self.assertEqual(self.node['fieldValueByName']['name'], 'Backlog')

    def test_verified_membership_supports_ready_status_update(self):
        with patch.object(github_project, 'items', return_value=[]), patch.object(
            github_project, 'query', side_effect=self.project_query
        ):
            self.assertEqual(github_project.status(self.url, 'ready'), {'updated': True})
        self.assertEqual(len(self.edits), 1)
        self.assertIn('item-1', self.edits[0])
        self.assertIn('project-1', self.edits[0])

    def test_wrong_repository_url_stops_before_api_lookup(self):
        with self.assertRaisesRegex(SystemExit, 'configured repository'):
            github_project.find_item('https://github.com/org/other/issues/7', [])
        self.run.assert_not_called()

    def test_other_project_membership_is_not_used(self):
        self.node['project']['id'] = 'another-project'
        self.assertIsNone(github_project.find_item(self.url, []))
        self.assertEqual(self.run.call_count, 1)

    def test_verified_absence_returns_no_item(self):
        self.repository['issue']['projectItems'] = {'totalCount': 0, 'nodes': []}
        self.assertIsNone(github_project.find_item(self.url, []))
        self.assertEqual(self.run.call_count, 1)

    def test_ambiguous_or_incomplete_membership_fails_closed(self):
        for nodes, total in (([self.node, self.node], 2), ([self.node], 2)):
            with self.subTest(total=total, nodes=len(nodes)):
                self.repository['issue']['projectItems'] = {'totalCount': total, 'nodes': nodes}
                with self.assertRaisesRegex(SystemExit, 'ambiguous, mismatched, or incomplete'):
                    github_project.find_item(self.url, [])

    def test_mismatched_repository_issue_or_project_fails_closed(self):
        original = copy.deepcopy(self.payload)
        for mismatch in ('repository', 'issue', 'project-number', 'project-id'):
            with self.subTest(mismatch=mismatch):
                self.payload = copy.deepcopy(original)
                repository = self.payload['data']['repository']
                if mismatch == 'repository': repository['nameWithOwner'] = 'org/other'
                if mismatch == 'issue': repository['issue']['url'] += '0'
                if mismatch == 'project-number': repository['owner']['projectV2']['number'] = 2
                if mismatch == 'project-id': repository['owner']['projectV2']['id'] = None
                with self.assertRaises(SystemExit):
                    github_project.find_item(self.url, [])

    def test_missing_or_mismatched_fresh_item_fails_closed(self):
        original = copy.deepcopy(self.node)
        for mismatch in ('missing', 'id', 'project', 'url', 'archived'):
            with self.subTest(mismatch=mismatch):
                node = copy.deepcopy(original)
                if mismatch == 'missing': node = None
                if mismatch == 'id': node['id'] = 'different-item'
                if mismatch == 'project': node['project']['id'] = 'different-project'
                if mismatch == 'url': node['content']['url'] += '0'
                if mismatch == 'archived': node['isArchived'] = True
                self.fresh = {'data': {'node': node}}
                with self.assertRaises(SystemExit):
                    github_project.find_item(self.url, [])

    def test_unresolved_or_unknown_status_field_or_option_fails_closed(self):
        original = copy.deepcopy(self.node)
        for mismatch in ('missing', 'malformed', 'unknown', 'field-id', 'field-name', 'option-id'):
            with self.subTest(mismatch=mismatch):
                self.node.clear()
                self.node.update(copy.deepcopy(original))
                status = self.node['fieldValueByName']
                if mismatch == 'missing': del self.node['fieldValueByName']
                if mismatch == 'malformed': self.node['fieldValueByName'] = {}
                if mismatch == 'unknown': status['name'] = 'Custom status'
                if mismatch == 'field-id': status['field']['id'] = 'another-field'
                if mismatch == 'field-name': status['field']['name'] = 'Other Status'
                if mismatch == 'option-id': status['optionId'] = 'unknown-option'
                self.fresh = {'data': {'node': copy.deepcopy(self.node)}}
                with self.assertRaisesRegex(SystemExit, 'identity or Status is invalid'):
                    github_project.find_item(self.url, [])

    def test_status_change_between_membership_and_node_read_fails_closed(self):
        self.set_status('Ready')
        self.fresh['data']['node']['fieldValueByName'].update(name='Done', optionId='Done')
        with self.assertRaisesRegex(SystemExit, 'changed during lookup'):
            github_project.find_item(self.url, [])

    def test_unset_status_changed_before_fresh_read_fails_closed(self):
        self.node['fieldValueByName'] = None
        with self.assertRaisesRegex(SystemExit, 'changed during lookup'):
            github_project.find_item(self.url, [])

    def test_unset_status_does_not_hide_missing_or_mismatched_membership(self):
        self.node['fieldValueByName'] = None
        original = copy.deepcopy(self.node)
        for mismatch in ('missing-status-key', 'malformed-status', 'project', 'url', 'item-id'):
            with self.subTest(mismatch=mismatch):
                node = copy.deepcopy(original)
                if mismatch == 'missing-status-key': del node['fieldValueByName']
                if mismatch == 'malformed-status': node['fieldValueByName'] = []
                if mismatch == 'project': node['project']['id'] = 'another-project'
                if mismatch == 'url': node['content']['url'] += '0'
                if mismatch == 'item-id': node['id'] = ''
                self.fresh = {'data': {'node': node}}
                with self.assertRaises(SystemExit):
                    github_project.find_item(self.url, [])

    def test_missing_project_status_definition_fails_closed(self):
        del self.repository['owner']['projectV2']['field']
        with self.assertRaisesRegex(SystemExit, 'identity or Status is invalid'):
            github_project.find_item(self.url, [])

    def test_partial_graphql_or_failed_query_fails_closed(self):
        for response in (
            result(returncode=1, stderr='API unavailable'), result('null'),
            result(json.dumps(dict(self.payload, errors=[{'message': 'Partial response'}]))),
        ):
            with self.subTest(response=response), patch.object(github_project, 'run', return_value=response):
                with self.assertRaises(SystemExit):
                    github_project.find_item(self.url, [])

    def test_claim_status_guard_still_refuses_unsafe_statuses(self):
        for status in ('Backlog', 'In Review', 'Blocked', 'Done'):
            with self.subTest(status=status):
                self.set_status(status)
                with patch.object(github_project, 'items', return_value=[]), patch.object(
                    github_project, 'query', side_effect=self.project_query
                ):
                    with self.assertRaisesRegex(SystemExit, 'In Progress write refused'):
                        github_project.status(self.url, 'in_progress', claim_owner='a')
        self.assertEqual(self.edits, [])

    def test_owner_guard_still_runs_before_fallback(self):
        self.assignees.append({'login': 'other'})
        with patch.object(github_project, 'items') as items, patch.object(
            github_project, 'query', side_effect=self.project_query
        ):
            with self.assertRaisesRegex(SystemExit, 'ownership changed'):
                github_project.status(self.url, 'in_progress', claim_owner='a')
        items.assert_not_called()
        self.assertEqual(self.edits, [])

    def test_claim_status_accepts_ready_and_preserves_same_owner_progress(self):
        for status in ('Ready', 'In Progress'):
            with self.subTest(status=status):
                self.set_status(status)
                self.edits.clear()
                with patch.object(github_project, 'items', return_value=[]), patch.object(
                    github_project, 'query', side_effect=self.project_query
                ):
                    outcome = github_project.status(self.url, 'in_progress', claim_owner='a')
                self.assertEqual(outcome, {'updated': True} if status == 'Ready' else {
                    'status': 'In Progress', 'skipped': True,
                })
                self.assertEqual(len(self.edits), 1 if status == 'Ready' else 0)

    def test_claim_refuses_other_owner_with_valid_ready_membership(self):
        self.set_status('Ready')
        def read(path, default=None):
            return {'members': [{'id': 'me', 'name': 'A', 'github': 'a'}]} if path.name == 'team.json' else {'member_id': 'me'}
        with patch.object(claim_task, 'read_json', side_effect=read), patch.object(
            claim_task, 'cmd_exists', return_value=True
        ), patch.object(claim_task, 'items', return_value=[]), patch.object(
            claim_task, 'run', side_effect=[result(), result(json.dumps({
                'number': 7, 'url': self.url, 'assignees': [{'login': 'other'}],
            }))]
        ) as run, patch.object(claim_task, 'set_status') as progress:
            with self.assertRaisesRegex(SystemExit, 'Ready/unclaimed'):
                claim_task.claim('7')
        self.assertEqual(run.call_count, 2)
        progress.assert_not_called()

    def test_claim_refuses_unset_status_before_branch_or_assignment(self):
        self.node['fieldValueByName'] = None
        self.fresh['data']['node']['fieldValueByName'] = None
        def read(path, default=None):
            return {'members': [{'id': 'me', 'name': 'A', 'github': 'a'}]} if path.name == 'team.json' else {'member_id': 'me'}
        with patch.object(claim_task, 'read_json', side_effect=read), patch.object(
            claim_task, 'cmd_exists', return_value=True
        ), patch.object(claim_task, 'items', return_value=[]), patch.object(
            claim_task, 'run', side_effect=[result(), result(json.dumps({
                'number': 7, 'url': self.url, 'assignees': [],
            }))]
        ) as run, patch.object(claim_task, 'set_status') as progress:
            with self.assertRaisesRegex(SystemExit, 'Ready/unclaimed'):
                claim_task.claim('7')
        self.assertEqual(run.call_count, 2)
        progress.assert_not_called()


if __name__ == '__main__':
    unittest.main()
