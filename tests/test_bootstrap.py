from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bootstrap
import onboard_member
import _common


def result(stdout: str = "", returncode: int = 0, stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(stdout=stdout, returncode=returncode, stderr=stderr)


class IdentityTests(unittest.TestCase):
    def paths(self, root: str) -> tuple[Path, Path]:
        base = Path(root)
        team = base / ".orchestrator" / "team.json"
        local = base / ".workspace-local" / "member.json"
        team.parent.mkdir(parents=True)
        team.write_text(json.dumps({"lead_architect_member_id": None, "members": []}), encoding="utf-8")
        return team, local

    def test_successful_first_onboarding_and_safe_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            team_path, local_path = self.paths(tmp)
            answers = iter(["", "Alice", "full-stack"])
            member = onboard_member.resolve_member(
                "AliceGH",
                team_path=team_path,
                local_path=local_path,
                input_fn=lambda _prompt: next(answers),
                output_fn=lambda _message: None,
            )
            first_team = team_path.read_text(encoding="utf-8")
            rerun = onboard_member.resolve_member(
                "alicegh",
                team_path=team_path,
                local_path=local_path,
                input_fn=lambda _prompt: self.fail("Rerun prompted instead of reusing identity"),
                output_fn=lambda _message: None,
            )
            self.assertEqual(member["id"], "member-gh-alicegh")
            self.assertEqual(rerun["id"], member["id"])
            self.assertEqual(team_path.read_text(encoding="utf-8"), first_team)
            self.assertEqual(
                json.loads(local_path.read_text(encoding="utf-8")),
                {"member_id": "member-gh-alicegh"},
            )

    def test_separate_fresh_clones_generate_non_colliding_member_ids(self):
        generated = []
        for username in ("alice", "bob"):
            with tempfile.TemporaryDirectory() as tmp:
                team_path, local_path = self.paths(tmp)
                answers = iter(["", username.title(), "full-stack"])
                member = onboard_member.resolve_member(
                    username,
                    team_path=team_path,
                    local_path=local_path,
                    input_fn=lambda _prompt: next(answers),
                    output_fn=lambda _message: None,
                )
                generated.append(member["id"])
        self.assertEqual(generated, ["member-gh-alice", "member-gh-bob"])
        self.assertEqual(len(set(generated)), 2)

    def test_existing_member_is_reused_by_authenticated_username(self):
        with tempfile.TemporaryDirectory() as tmp:
            team_path, local_path = self.paths(tmp)
            team_path.write_text(
                json.dumps({"lead_architect_member_id": None, "members": [
                    {"id": "member-07", "name": "Sam", "github": "SamGH", "role": "qa", "status": "active"}
                ]}),
                encoding="utf-8",
            )
            member = onboard_member.resolve_member(
                "samgh",
                team_path=team_path,
                local_path=local_path,
                input_fn=lambda _prompt: self.fail("Existing GitHub member should not prompt"),
                output_fn=lambda _message: None,
            )
            self.assertEqual(member["id"], "member-07")
            self.assertEqual(json.loads(local_path.read_text(encoding="utf-8"))["member_id"], "member-07")

    def test_duplicate_member_ids_are_rejected(self):
        members = [
            {"id": "member-01", "name": "One", "github": "one", "role": "dev", "status": "active"},
            {"id": "MEMBER-01", "name": "Two", "github": "two", "role": "dev", "status": "active"},
        ]
        with self.assertRaisesRegex(onboard_member.IdentityError, "Duplicate member ID"):
            onboard_member.validate_members(members)

    def test_duplicate_github_usernames_are_rejected(self):
        members = [
            {"id": "member-01", "name": "One", "github": "SameUser", "role": "dev", "status": "active"},
            {"id": "member-02", "name": "Two", "github": "sameuser", "role": "dev", "status": "active"},
        ]
        with self.assertRaisesRegex(onboard_member.IdentityError, "Duplicate GitHub username"):
            onboard_member.validate_members(members)

    def test_invalid_member_record_is_rejected(self):
        with self.assertRaisesRegex(onboard_member.IdentityError, "requires a non-empty role"):
            onboard_member.validate_members([
                {"id": "member-01", "name": "One", "github": "one", "status": "active"}
            ])

    def test_inconsistent_local_and_authenticated_members_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            team_path, local_path = self.paths(tmp)
            team_path.write_text(
                json.dumps({"lead_architect_member_id": None, "members": [
                    {"id": "member-01", "name": "One", "github": "one", "role": "dev", "status": "active"},
                    {"id": "member-02", "name": "Two", "github": "two", "role": "dev", "status": "active"},
                ]}),
                encoding="utf-8",
            )
            local_path.parent.mkdir(parents=True)
            local_path.write_text(json.dumps({"member_id": "member-01"}), encoding="utf-8")
            with self.assertRaisesRegex(onboard_member.IdentityError, "map to different shared members"):
                onboard_member.resolve_member(
                    "two", team_path=team_path, local_path=local_path, output_fn=lambda _message: None
                )


class BootstrapTests(unittest.TestCase):
    def test_successful_bootstrap_runs_hooks_verification_sync_and_reports_architecture(self):
        calls = []

        def script(name, label):
            calls.append((name, label))

        output = io.StringIO()
        with (
            patch.object(bootstrap, "check_prerequisites"),
            patch.object(bootstrap, "read_json", return_value={"github": {}}),
            patch.object(bootstrap, "check_github_access", return_value=("alice", None)),
            patch.object(bootstrap, "resolve_member", return_value={
                "id": "member-01", "name": "Alice", "github": "alice"
            }),
            patch.object(bootstrap, "run_existing_script", side_effect=script),
            patch.object(bootstrap, "classify_readiness", return_value=(
                "READY FOR ARCHITECTURE", "Continue Architecture Kickoff."
            )),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(bootstrap.main(), 0)
        self.assertEqual(
            [name for name, _label in calls],
            ["install_hooks.py", "verify_workspace.py", "project_sync.py"],
        )
        self.assertIn("READY FOR ARCHITECTURE", output.getvalue())
        self.assertNotIn("NOT READY", output.getvalue())

    def test_missing_github_cli_is_not_ready(self):
        with patch.object(bootstrap, "cmd_exists", side_effect=lambda name: name != "gh"):
            with self.assertRaisesRegex(bootstrap.BootstrapError, "GitHub CLI is required"):
                bootstrap.check_prerequisites()

    def test_missing_github_authentication_is_not_ready(self):
        with patch.object(bootstrap, "run", return_value=result(returncode=1, stderr="not logged in")):
            with self.assertRaisesRegex(bootstrap.BootstrapError, "gh auth login"):
                bootstrap.check_github_access({"github": {}})

    def test_configured_project_requires_update_permission(self):
        github = {"owner": "example", "repo": "workspace", "project_number": 1}
        response = json.dumps({
            "data": {"repository": {"owner": {"projectV2": {"viewerCanUpdate": False}}}}
        })
        with patch.object(bootstrap, "run", return_value=result(response)):
            with self.assertRaisesRegex(bootstrap.BootstrapError, "update permission"):
                bootstrap.check_project_update_access(github)

    def test_verification_failure_stops_before_project_sync_and_reports_not_ready(self):
        calls = []

        def script(name, _label):
            calls.append(name)
            if name == "verify_workspace.py":
                raise bootstrap.BootstrapError("Workspace verification failed: tests failed")

        output = io.StringIO()
        with (
            patch.object(bootstrap, "check_prerequisites"),
            patch.object(bootstrap, "read_json", return_value={"github": {}}),
            patch.object(bootstrap, "check_github_access", return_value=("alice", None)),
            patch.object(bootstrap, "resolve_member", return_value={
                "id": "member-01", "name": "Alice", "github": "alice"
            }),
            patch.object(bootstrap, "run_existing_script", side_effect=script),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(bootstrap.main(), 1)
        self.assertEqual(calls, ["install_hooks.py", "verify_workspace.py"])
        self.assertIn("NOT READY", output.getvalue())
        self.assertIn("Workspace verification failed", output.getvalue())

    def test_ready_for_architecture_classification(self):
        with (
            patch.object(bootstrap, "read_json_object", return_value={"project": {"phase": "new"}}),
            patch.object(bootstrap, "read_json", return_value={"status": "not_started", "completed_sections": []}),
        ):
            state, _action = bootstrap.classify_readiness({"github": {}}, None)
        self.assertEqual(state, "READY FOR ARCHITECTURE")

    def test_ready_to_claim_requires_approved_implementation_and_ready_task(self):
        architecture = {
            "status": "approved",
            "completed_sections": list(_common.PROFESSIONAL_ARCHITECTURE_SECTIONS),
            "approval": None,
        }
        config = {"operating_mode": "professional", "github": {"status_values": {"ready": "Ready"}}}
        items = [{"status": "Ready", "content": {"url": "https://github.com/org/repo/issues/1"}}]
        with (
            patch.object(bootstrap, "read_json_object", return_value={"project": {"phase": "implementation"}}),
            patch.object(bootstrap, "read_json", return_value=architecture),
        ):
            state, _action = bootstrap.classify_readiness(config, items)
        self.assertEqual(state, "READY TO CLAIM")

    def test_approved_project_without_ready_task_does_not_claim_readiness(self):
        architecture = {
            "status": "approved",
            "completed_sections": list(_common.PROFESSIONAL_ARCHITECTURE_SECTIONS),
            "approval": None,
        }
        with (
            patch.object(bootstrap, "read_json_object", return_value={"project": {"phase": "implementation"}}),
            patch.object(bootstrap, "read_json", return_value=architecture),
        ):
            state, action = bootstrap.classify_readiness({"operating_mode": "professional", "github": {}}, [])
        self.assertEqual(state, "READY FOR ARCHITECTURE")
        self.assertIn("Ready", action)

    def test_repository_remote_is_used_when_workspace_config_is_blank(self):
        with patch.object(
            bootstrap, "run", return_value=result("git@github.com:example/workspace.git\n")
        ):
            self.assertEqual(bootstrap.intended_repository({"github": {}}), "example/workspace")


if __name__ == "__main__":
    unittest.main()
