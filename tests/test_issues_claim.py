import contextlib
import copy
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import _common
import bootstrap
import claim_task


def result(stdout='', code=0):
    return subprocess.CompletedProcess([], code, stdout, '')


class IssuesClaimTests(unittest.TestCase):
    def setUp(self):
        self.member = {'id': 'me', 'name': 'Heiron8', 'github': 'Heiron8', 'role': 'full-stack', 'status': 'active'}
        self.team = {'lead_architect_member_id': 'me', 'members': [self.member]}
        self.task = {'number': 10, 'url': 'https://github.com/o/r/issues/10', 'state': 'OPEN',
                     'assignees': [{'login': 'Heiron8'}], 'labels': [{'name': 'status:ready'}]}
        self.edits = []
        self.views = 0
        self.race = None
        self.failed_edit = False
        self.output = io.StringIO()
        self.arch = {'status': 'approved', 'completed_sections': list(_common.PROFESSIONAL_ARCHITECTURE_SECTIONS)}
        for name, value in [('read_json', self.read), ('cmd_exists', lambda _: True),
                            ('run_network', self.network), ('run', lambda _: result()),
                            ('project_number', None), ('prepare_branch', lambda _: 'isolated/task')]:
            patcher = patch.object(claim_task, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def read(self, path, default=None):
        return {'team.json': self.team, 'member.json': {'member_id': 'me'},
                'workspace.config.json': {'github': {'owner': 'o', 'repo': 'r'}}, 'architecture-state.json': self.arch,
                'project-state.json': {'project': {'phase': 'implementation'}}}.get(path.name, default)

    def network(self, args):
        if args[:3] == ['gh', 'auth', 'status']:
            return result()
        if args[:3] == ['gh', 'api', 'user']:
            return result('Heiron8')
        if args[:3] == ['gh', 'issue', 'view']:
            self.views += 1
            if self.race: self.race(self.views)
            return result(json.dumps(self.task))
        if args[:3] == ['gh', 'issue', 'edit']:
            self.edits.append(args)
            self.task['labels'] = [{'name': 'status:in-progress'}]
            return result(code=1 if self.failed_edit else 0)
        self.fail(f'Unexpected network call: {args}')

    def claim(self):
        with contextlib.redirect_stdout(self.output): claim_task.claim(10)

    def test_issue_only_success_and_idempotent_retry(self):
        with patch.object(claim_task, 'items') as projects:
            self.claim()
            self.claim()
            projects.assert_not_called()
        self.assertEqual(len(self.edits), 1)
        self.assertNotIn('--add-assignee', self.edits[0])
        self.assertIn('Source: GitHub Issues', self.output.getvalue())

    def test_competing_and_unassigned_owner_block_before_branch(self):
        for owners in ([], [{'login': 'other'}], [{'login': 'Heiron8'}, {'login': 'other'}]):
            with self.subTest(owners=owners), patch.object(claim_task, 'prepare_branch') as branch:
                self.task['assignees'] = owners
                with self.assertRaisesRegex(SystemExit, 'Lead-assigned'):
                    self.claim()
                branch.assert_not_called()
        self.assertEqual(self.edits, [])

    def test_closed_ambiguous_missing_and_later_status_block(self):
        for state, labels in [('CLOSED', ['ready']), ('OPEN', []), ('OPEN', ['ready', 'done']),
                              ('OPEN', ['backlog']), ('OPEN', ['blocked']), ('OPEN', ['in-review']),
                              ('OPEN', ['done']), ('OPEN', ['unknown'])]:
            with self.subTest(state=state, labels=labels), patch.object(claim_task, 'prepare_branch') as branch:
                self.task['state'] = state
                self.task['labels'] = [{'name': 'status:' + label} for label in labels]
                with self.assertRaises(SystemExit): self.claim()
                branch.assert_not_called()
        self.assertEqual(self.edits, [])

    def test_owner_or_status_race_before_transition_preserved(self):
        initial = copy.deepcopy(self.task)
        for kind in ('owner', 'status'):
            self.task = copy.deepcopy(initial)
            self.views = 0
            def race(view):
                if view == 2:
                    if kind == 'owner': self.task['assignees'] = [{'login': 'other'}]
                    else: self.task['labels'] = [{'name': 'status:done'}]
            self.race = race
            with self.assertRaises(SystemExit): self.claim()
        self.assertEqual(self.edits, [])

    def test_owner_race_after_transition_never_reports_success(self):
        def race(view):
            if view == 3: self.task['assignees'].append({'login': 'other'})
        self.race = race
        with self.assertRaisesRegex(SystemExit, 'not reported'): self.claim()
        self.assertNotIn('TASK CLAIM RESULT', self.output.getvalue())
        self.assertEqual(len(self.task['assignees']), 2)

    def test_failed_transition_retry_reads_applied_remote_state(self):
        self.failed_edit = True
        with self.assertRaisesRegex(SystemExit, 'No claim success'): self.claim()
        self.failed_edit = False
        self.claim()
        self.assertEqual(len(self.edits), 1)

    def test_unavailable_project_lookup_falls_back_to_explicit_issue(self):
        with patch.object(claim_task, 'project_number', 1), patch.object(
            claim_task, 'items', side_effect=SystemExit('Project unavailable')
        ):
            self.claim()
        self.assertIn('Project unavailable', self.output.getvalue())

    def test_failed_project_mutation_does_not_fall_back(self):
        with patch.object(claim_task, 'project_number', 1), patch.object(
            claim_task, 'items', return_value=[{'content': {'url': self.task['url']}, 'status': 'Ready'}]
        ), patch.object(claim_task, 'set_status', side_effect=SystemExit('Project mutation failed')):
            with self.assertRaisesRegex(SystemExit, 'Project mutation failed'): self.claim()
        self.assertEqual(self.edits, [])

    def test_identity_mismatch_or_unapproved_architecture_blocks(self):
        with patch.object(claim_task, 'run_network', return_value=result('OtherUser')):
            with self.assertRaisesRegex(SystemExit, 'match the local'): self.claim()
        self.arch['status'] = 'review_pending'
        with self.assertRaisesRegex(SystemExit, 'approved architecture'): self.claim()
        self.assertEqual(self.views, 0)

    def test_lookup_failure_stops_without_mutation(self):
        with patch.object(claim_task, 'issue_state', side_effect=SystemExit('Issue unavailable')):
            with self.assertRaisesRegex(SystemExit, 'Issue unavailable'): self.claim()
        self.assertEqual(self.edits, [])

    def test_foreign_repository_issue_blocks_before_branch(self):
        self.task['url'] = 'https://github.com/o/other/issues/10'
        with patch.object(claim_task, 'prepare_branch') as branch:
            with self.assertRaisesRegex(SystemExit, 'configured repository'): self.claim()
            branch.assert_not_called()
        self.assertEqual(self.edits, [])


class BootstrapOptionalProjectTests(unittest.TestCase):
    def test_project_access_unavailable_preserves_issue_ready_path(self):
        config = {'github': {'owner': 'o', 'repo': 'r', 'project_number': 1}}
        with patch.object(bootstrap, 'run', side_effect=[result(), result('Heiron8'), result()]), \
             patch.object(bootstrap, 'check_project_update_access', side_effect=bootstrap.BootstrapError('No Project access')), \
             patch.object(bootstrap, 'ready_issues', return_value=[{'status': 'Ready', 'content': {'url': 'issue'}}]), \
             contextlib.redirect_stdout(io.StringIO()):
            login, tasks = bootstrap.check_github_access(config)
        self.assertEqual(login, 'Heiron8')
        self.assertEqual(tasks[0]['status'], 'Ready')


if __name__ == '__main__':
    unittest.main()
