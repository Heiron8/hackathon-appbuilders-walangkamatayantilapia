from __future__ import annotations

import contextlib
import io
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import _common
import bootstrap


class SafeSyncTests(unittest.TestCase):
    def git(self, path, *args):
        return subprocess.run(['git', *args], cwd=path, check=True, text=True,
                              capture_output=True).stdout.strip()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.remote = self.base / 'remote.git'
        self.seed = self.base / 'seed'
        self.local = self.base / 'local'
        self.git(self.base, 'init', '--bare', '--initial-branch=main', str(self.remote))
        self.git(self.base, 'clone', str(self.remote), str(self.seed))
        for key, value in [('user.name', 'Fixture'), ('user.email', 'fixture@example.test')]:
            self.git(self.seed, 'config', key, value)
        (self.seed / 'file.txt').write_text('base\n')
        (self.seed / '.gitignore').write_text('.workspace-local/\nprivate.txt\n')
        (self.seed / '.orchestrator').mkdir()
        (self.seed / '.orchestrator/project-state.json').write_text(json.dumps({'project': {'phase': 'planning'}}))
        (self.seed / '.orchestrator/team.json').write_text('{"members": []}')
        (self.seed / '.orchestrator/architecture-state.json').write_text(json.dumps({
            'status': 'approved', 'completed_sections': list(_common.PROFESSIONAL_ARCHITECTURE_SECTIONS)}))
        (self.seed / 'workspace.config.json').write_text('{"github": {}}')
        self.git(self.seed, 'add', '.')
        self.git(self.seed, 'commit', '-m', 'fixture')
        self.git(self.seed, 'push', 'origin', 'main')
        self.git(self.base, 'clone', str(self.remote), str(self.local))
        for key, value in [('user.name', 'Fixture'), ('user.email', 'fixture@example.test')]:
            self.git(self.local, 'config', key, value)
        (self.local / '.workspace-local').mkdir()
        self.identity = self.local / '.workspace-local/member.json'
        self.identity.write_text('{"member_id": "preserved"}')
        self.initial = self.git(self.local, 'rev-parse', 'HEAD')
        patcher = patch.object(_common, 'ROOT', self.local)
        patcher.start()
        self.addCleanup(patcher.stop)

    def remote_ahead(self):
        (self.seed / 'file.txt').write_text('remote\n')
        (self.seed / '.orchestrator/project-state.json').write_text(json.dumps({'project': {'phase': 'implementation'}}))
        self.git(self.seed, 'add', '.')
        self.git(self.seed, 'commit', '-m', 'remote ahead')
        self.git(self.seed, 'push', 'origin', 'main')
        return self.git(self.seed, 'rev-parse', 'HEAD')

    def preserved(self, status='NOT UPDATED'):
        head = self.git(self.local, 'rev-parse', 'HEAD')
        files = {p.relative_to(self.local): p.read_bytes() for p in self.local.rglob('*')
                 if p.is_file() and '.git' not in p.relative_to(self.local).parts}
        result = _common.sync_main()
        self.assertEqual(result.status, status, result)
        self.assertEqual(self.git(self.local, 'rev-parse', 'HEAD'), head)
        self.assertEqual({p: (self.local / p).read_bytes() for p in files}, files)
        return result

    def test_clean_main_remote_ahead_preserves_identity(self):
        target = self.remote_ahead()
        self.assertEqual(_common.sync_main().status, 'UPDATED')
        self.assertEqual(self.git(self.local, 'rev-parse', 'HEAD'), target)
        self.assertEqual(self.identity.read_text(), '{"member_id": "preserved"}')
        self.assertEqual(_common.sync_main().status, 'ALREADY CURRENT')

    def test_already_current(self):
        self.preserved('ALREADY CURRENT')

    def test_dirty_staged_and_untracked_skip_fetch(self):
        self.remote_ahead()
        (self.local / 'file.txt').write_text('developer\n')
        with patch.object(_common, 'run_network') as network:
            self.preserved()
            self.git(self.local, 'add', 'file.txt')
            self.preserved()
            self.git(self.local, 'commit', '-m', 'local work')
            (self.local / 'untracked.txt').write_text('keep')
            self.preserved()
            network.assert_not_called()

    def test_active_task_branch_and_detached_head(self):
        self.git(self.local, 'switch', '-c', 'task/fixture')
        with patch.object(_common, 'run_network') as network:
            self.assertIn('preserved', self.preserved().message)
            self.git(self.local, 'switch', '--detach')
            self.preserved()
            network.assert_not_called()

    def test_local_ahead_and_divergence(self):
        (self.local / 'local.txt').write_text('local')
        self.git(self.local, 'add', '.')
        self.git(self.local, 'commit', '-m', 'local ahead')
        self.assertIn('ahead', self.preserved().message)
        self.remote_ahead()
        self.assertIn('diverged', self.preserved().message)

    def test_fetch_failure_is_offline(self):
        self.git(self.local, 'remote', 'set-url', 'origin', str(self.base / 'missing.git'))
        self.preserved('OFFLINE')

    def test_timeout_is_offline_and_network_is_noninteractive(self):
        real_run = _common.run
        def timed(cmd, **kwargs):
            if 'fetch' in cmd:
                self.assertEqual(kwargs['timeout'], 30)
                self.assertEqual(kwargs['env']['GIT_TERMINAL_PROMPT'], '0')
                self.assertIn('BatchMode=yes', kwargs['env']['GIT_SSH_COMMAND'])
                raise subprocess.TimeoutExpired(cmd, 30)
            return real_run(cmd, **kwargs)
        with patch.object(_common, 'run', side_effect=timed):
            self.preserved('OFFLINE')

    def test_interrupted_operations_preserved(self):
        for marker in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply', 'sequencer'):
            with self.subTest(marker=marker):
                path = self.local / self.git(self.local, 'rev-parse', '--git-path', marker)
                if marker.endswith('_HEAD'):
                    path.write_text(self.initial + '\n')
                else:
                    path.mkdir()
                with patch.object(_common, 'run_network') as network:
                    self.preserved()
                    network.assert_not_called()
                if path.is_dir(): path.rmdir()
                else: path.unlink()

    def test_inspection_failure_not_clean(self):
        real_run = _common.run
        def broken(cmd, **kwargs):
            if 'status' in cmd:
                return subprocess.CompletedProcess(cmd, 1, '', 'inspection failed')
            return real_run(cmd, **kwargs)
        with patch.object(_common, 'run', side_effect=broken), patch.object(_common, 'run_network') as network:
            self.assertIn('inspection failed', self.preserved().message)
            network.assert_not_called()

    def test_missing_origin_preserved(self):
        self.git(self.local, 'remote', 'remove', 'origin')
        self.preserved()

    def test_checkout_change_during_fetch_preserved(self):
        self.remote_ahead()
        real_network = _common.run_network
        def raced(cmd):
            result = real_network(cmd)
            (self.local / 'untracked.txt').write_text('concurrent work')
            return result
        with patch.object(_common, 'run_network', side_effect=raced):
            self.assertEqual(_common.sync_main().status, 'NOT UPDATED')
        self.assertEqual(self.git(self.local, 'rev-parse', 'HEAD'), self.initial)
        self.assertEqual((self.local / 'untracked.txt').read_text(), 'concurrent work')

    def test_merge_does_not_autostash_or_overwrite_ignored_file(self):
        (self.seed / 'private.txt').write_text('remote file')
        self.git(self.seed, 'add', '-f', 'private.txt')
        self.git(self.seed, 'commit', '-m', 'tracked private')
        self.git(self.seed, 'push', 'origin', 'main')
        (self.local / 'private.txt').write_text('private local work')
        self.git(self.local, 'config', 'merge.autoStash', 'true')
        self.preserved()

    def test_project_reads_updated_state(self):
        self.remote_ahead()
        out = io.StringIO()
        with patch.object(_common, 'ORCH', self.local / '.orchestrator'), patch.object(
            _common, 'LOCAL', self.local / '.workspace-local'
        ), contextlib.redirect_stdout(out):
            runpy.run_path(str(ROOT / 'scripts/project_sync.py'))
        self.assertIn('UPDATED', out.getvalue())
        self.assertIn('Phase: implementation', out.getvalue())
        self.assertEqual(self.identity.read_text(), '{"member_id": "preserved"}')

    def test_offline_sync_still_reads_local_state(self):
        self.git(self.local, 'remote', 'set-url', 'origin', str(self.base / 'missing.git'))
        out = io.StringIO()
        with patch.object(_common, 'ORCH', self.local / '.orchestrator'), patch.object(
            _common, 'LOCAL', self.local / '.workspace-local'
        ), contextlib.redirect_stdout(out):
            runpy.run_path(str(ROOT / 'scripts/project_sync.py'))
        self.assertIn('OFFLINE', out.getvalue())
        self.assertIn('Phase: planning', out.getvalue())


class BootstrapOrderingTests(unittest.TestCase):
    def test_sync_precedes_configuration_identity_and_verification(self):
        events = []
        def script(name, _label): events.append(name)
        def config(*_args):
            self.assertEqual(events, ['prerequisites', 'project_sync.py'])
            events.append('config')
            return {}
        def identity(_login):
            self.assertIn('config', events)
            events.append('identity')
            return {'id': 'me', 'name': 'Heiron8', 'github': 'Heiron8'}
        with patch.object(bootstrap, 'check_prerequisites', side_effect=lambda: events.append('prerequisites')), \
             patch.object(bootstrap, 'read_json_object', side_effect=config), \
             patch.object(bootstrap, 'check_github_access', return_value=('Heiron8', [])), \
             patch.object(bootstrap, 'resolve_member', side_effect=identity), \
             patch.object(bootstrap, 'run_existing_script', side_effect=script), \
             patch.object(bootstrap, 'classify_readiness', return_value=('READY TO CLAIM', 'Ready')), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(bootstrap.main(), 0)
        self.assertLess(events.index('identity'), events.index('verify_workspace.py'))

    def test_issues_readiness_requires_exclusive_owner_and_one_status(self):
        tasks = [
            {'url': 'one', 'assignees': [{'login': 'Heiron8'}], 'labels': [{'name': 'status:ready'}]},
            {'url': 'two', 'assignees': [{'login': 'Heiron8'}, {'login': 'other'}], 'labels': [{'name': 'status:ready'}]},
            {'url': 'three', 'assignees': [{'login': 'Heiron8'}], 'labels': [{'name': 'status:ready'}, {'name': 'status:done'}]},
        ]
        with patch.object(bootstrap, 'run_network', return_value=subprocess.CompletedProcess([], 0, json.dumps(tasks), '')):
            self.assertEqual(bootstrap.ready_issues({'github': {'owner': 'o', 'repo': 'r'}}, 'Heiron8'),
                             [{'status': 'Ready', 'content': {'url': 'one'}}])


if __name__ == '__main__':
    unittest.main()
