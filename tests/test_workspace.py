from __future__ import annotations
import contextlib, io, json, runpy, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import _common, guardrails

class WorkspaceTests(unittest.TestCase):
    def test_state_files_are_json_objects(self):
        for name in ("project-state.json","architecture-state.json","team.json","policies.json"):
            with self.subTest(name=name): self.assertIsInstance(json.loads((ROOT/".orchestrator"/name).read_text()),dict)
    def test_response_contracts_have_required_sections(self):
        for path in (ROOT/"response-contracts").glob("*.md"):
            with self.subTest(path=path.name):
                text=path.read_text(encoding="utf-8"); self.assertIn("#",text); self.assertGreater(len(text),150)
    def test_adapter_contracts_are_provider_optional(self):
        for name in ("vscode","codex","orca","kiro","claude","gemini","generic"):
            text=(ROOT/"adapters"/name/"README.md").read_text(encoding="utf-8").lower()
            self.assertIn("canonical",text)
    def test_secret_scanner_finds_and_allows_examples(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad=Path(tmp)/"bad.env"; bad.write_text("API_KEY=" + "abcdefgh12345\n")
            sample=Path(tmp)/"sample.env"; sample.write_text("API_KEY=your_key_here\n")
            self.assertTrue(guardrails.scan([bad])); self.assertFalse(guardrails.scan([sample]))
    def test_task_publisher_is_marked_idempotent_and_gated(self):
        source=(ROOT/"scripts"/"publish_tasks.py").read_text(encoding="utf-8")
        self.assertIn("architecture_release",source)
        self.assertIn("workspace-task-key",source)
        self.assertIn("[EXISTS]",source)
    def test_fresh_project_sync_does_not_query_unconfigured_github(self):
        def read(path, default=None):
            if path.name == 'workspace.config.json':
                return {'github': {'owner': '', 'repo': '', 'project_number': None}}
            return default or {}
        output = io.StringIO()
        with (patch.object(_common, 'read_json', side_effect=read),
              patch.object(_common, 'cmd_exists', side_effect=lambda name: name == 'gh'),
              patch.object(_common, 'run', side_effect=AssertionError('No external query expected')),
              contextlib.redirect_stdout(output)):
            runpy.run_path(str(ROOT/'scripts/project_sync.py'))
        self.assertIn('Repository and Project are not configured', output.getvalue())

    def test_hooks_call_canonical_checks(self):
        self.assertIn("guardrails.py",(ROOT/".githooks"/"pre-commit").read_text())
        self.assertIn("protected-branch",(ROOT/".githooks"/"pre-push").read_text())

if __name__ == "__main__": unittest.main()
