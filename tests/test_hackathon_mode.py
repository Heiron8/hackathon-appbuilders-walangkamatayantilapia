from __future__ import annotations

import contextlib
import copy
import io
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import _common
import bootstrap
import publish_tasks
import verify_workspace


class HackathonModeTests(unittest.TestCase):
    def project_sync_output(self, config, architecture, phase="implementation"):
        values = {
            "workspace.config.json": config,
            "team.json": {"members": []},
            "project-state.json": {"project": {"phase": phase}},
            "architecture-state.json": architecture,
            "member.json": {},
        }

        def read(path, default=None):
            return copy.deepcopy(values.get(path.name, default))

        output = io.StringIO()
        with (
            patch.object(_common, "read_json", side_effect=read),
            patch.object(_common, "cmd_exists", return_value=False),
            contextlib.redirect_stdout(output),
        ):
            runpy.run_path(str(ROOT / "scripts" / "project_sync.py"))
        return output.getvalue()

    def test_hackathon_mode_is_active_and_discoverable(self):
        config = json.loads((ROOT / "workspace.config.json").read_text(encoding="utf-8"))
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        guide = (ROOT / "docs" / "workspace" / "hackathon-mode.md").read_text(encoding="utf-8")
        self.assertEqual(config["operating_mode"], _common.HACKATHON_MODE)
        self.assertIn("docs/workspace/hackathon-mode.md", agents)
        self.assertIn("simplifies ceremony, not engineering quality", guide)

    def test_normal_professional_mode_remains_supported(self):
        self.assertEqual(
            _common.operating_mode({"operating_mode": "professional"}),
            _common.PROFESSIONAL_MODE,
        )
        publish_tasks.require_architecture_approval(
            {
                "status": "approved",
                "completed_sections": list(_common.PROFESSIONAL_ARCHITECTURE_SECTIONS),
                "approval": None,
            },
            {"operating_mode": "professional"},
        )
        self.assertEqual(
            _common.required_architecture_sections({"operating_mode": "professional"}),
            _common.PROFESSIONAL_ARCHITECTURE_SECTIONS,
        )

    def test_unknown_operating_mode_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Unsupported operating mode"):
            _common.operating_mode({"operating_mode": "unknown"})

    def test_architecture_approval_is_still_required(self):
        with self.assertRaisesRegex(SystemExit, "explicit approval"):
            publish_tasks.require_architecture_approval(
                {
                    "status": "in_progress",
                    "completed_sections": list(_common.HACKATHON_ARCHITECTURE_SECTIONS),
                    "approval": None,
                },
                {"operating_mode": "hackathon-24h"},
            )

    def test_hackathon_approval_requires_complete_compact_kickoff(self):
        with self.assertRaisesRegex(SystemExit, "architecture is incomplete"):
            publish_tasks.require_architecture_approval(
                {
                    "status": "approved",
                    "completed_sections": [],
                    "approval": {
                        "approved_by": "Lead",
                        "approved_at": "2026-10-08T00:00:00Z",
                        "mode": "hackathon-24h",
                    },
                },
                {"operating_mode": "hackathon-24h"},
            )

    def test_hackathon_approval_requires_matching_human_approval_record(self):
        architecture = {
            "status": "approved",
            "completed_sections": list(_common.HACKATHON_ARCHITECTURE_SECTIONS),
            "approval": None,
        }
        with self.assertRaisesRegex(SystemExit, "explicit human approval"):
            publish_tasks.require_architecture_approval(
                architecture, {"operating_mode": "hackathon-24h"}
            )

    def test_complete_hackathon_kickoff_can_release_task_publication_gate(self):
        architecture = {
            "status": "approved",
            "completed_sections": list(_common.HACKATHON_ARCHITECTURE_SECTIONS),
            "approval": {
                "approved_by": "Lead",
                "approved_at": "2026-10-08T00:00:00Z",
                "mode": "hackathon-24h",
            },
        }
        publish_tasks.require_architecture_approval(
            architecture, {"operating_mode": "hackathon-24h"}
        )

    def test_architecture_release_rejects_malformed_approval_evidence(self):
        invalid_values = (
            ("approved_by", "   ", "approved_by"),
            ("approved_at", "   ", "approved_at"),
            ("approved_by", [], "approved_by"),
            ("approved_at", 123, "approved_at"),
            ("approved_at", "not-a-timestamp", "approved_at"),
        )
        for field, value, message in invalid_values:
            with self.subTest(field=field, value=value):
                approval = {
                    "approved_by": "Lead",
                    "approved_at": "2026-10-08T00:00:00Z",
                    "mode": "hackathon-24h",
                }
                approval[field] = value
                release = _common.architecture_release(
                    {
                        "status": "approved",
                        "completed_sections": list(_common.HACKATHON_ARCHITECTURE_SECTIONS),
                        "approval": approval,
                    },
                    {"operating_mode": "hackathon-24h"},
                )
                self.assertEqual(release.outcome, "invalid")
                self.assertIn(message, release.message)

    def test_valid_human_approval_still_releases_architecture(self):
        release = _common.architecture_release(
            {
                "status": "approved",
                "completed_sections": list(_common.HACKATHON_ARCHITECTURE_SECTIONS),
                "approval": {
                    "approved_by": "  Lead Architect  ",
                    "approved_at": "  2026-10-08T00:00:00+00:00  ",
                    "mode": "hackathon-24h",
                },
            },
            {"operating_mode": "hackathon-24h"},
        )
        self.assertTrue(release.released)

    def test_architecture_state_rejects_whitespace_only_approve_by(self):
        with (
            patch.object(sys, "argv", ["architecture_state.py", "--approve-by", "   "]),
            self.assertRaisesRegex(SystemExit, "--approve-by must be a non-empty string"),
        ):
            runpy.run_path(str(ROOT / "scripts" / "architecture_state.py"))

    def test_bootstrap_and_publication_share_architecture_release_validator(self):
        self.assertIs(bootstrap.architecture_release, publish_tasks.architecture_release)
        architecture = {
            "status": "approved",
            "completed_sections": [],
            "approval": None,
        }
        release = _common.architecture_release(
            architecture, {"operating_mode": "hackathon-24h"}
        )
        self.assertEqual(release.outcome, "incomplete")
        with (
            patch.object(bootstrap, "read_json_object", return_value={"project": {"phase": "implementation"}}),
            patch.object(bootstrap, "read_json", return_value=architecture),
        ):
            state, action = bootstrap.classify_readiness(
                {"operating_mode": "hackathon-24h", "github": {}},
                [{"status": "Ready", "content": {"url": "https://github.com/org/repo/issues/1"}}],
            )
        self.assertEqual((state, action), ("READY FOR ARCHITECTURE", release.message))
        with self.assertRaisesRegex(SystemExit, release.message):
            publish_tasks.require_architecture_approval(
                architecture, {"operating_mode": "hackathon-24h"}
            )

    def test_invalid_architecture_state_is_not_ready(self):
        architecture = {
            "status": "approved",
            "completed_sections": list(_common.HACKATHON_ARCHITECTURE_SECTIONS),
            "approval": None,
        }
        with (
            patch.object(bootstrap, "read_json_object", return_value={"project": {"phase": "implementation"}}),
            patch.object(bootstrap, "read_json", return_value=architecture),
        ):
            with self.assertRaisesRegex(bootstrap.BootstrapError, "Architecture state is invalid"):
                bootstrap.classify_readiness(
                    {"operating_mode": "hackathon-24h", "github": {}},
                    [{"status": "Ready", "content": {"url": "https://github.com/org/repo/issues/1"}}],
                )

    def test_implementation_readiness_cannot_bypass_architecture(self):
        architecture = {"status": "review_pending", "completed_sections": []}
        config = {
            "operating_mode": "hackathon-24h",
            "github": {"status_values": {"ready": "Ready"}},
        }
        items = [{"status": "Ready", "content": {"url": "https://github.com/org/repo/issues/1"}}]
        with (
            patch.object(bootstrap, "read_json_object", return_value={"project": {"phase": "implementation"}}),
            patch.object(bootstrap, "read_json", return_value=architecture),
        ):
            state, _action = bootstrap.classify_readiness(config, items)
        self.assertEqual(state, "READY FOR ARCHITECTURE")

    def test_mode_switching_preserves_completed_architecture_data(self):
        completed = list(_common.PROFESSIONAL_ARCHITECTURE_SECTIONS)
        architecture = {"status": "approved", "completed_sections": completed, "approval": None}
        original = copy.deepcopy(architecture)
        self.assertTrue(
            _common.architecture_release(
                architecture, {"operating_mode": "professional"}
            ).released
        )
        self.assertEqual(
            _common.architecture_release(
                architecture, {"operating_mode": "hackathon-24h"}
            ).outcome,
            "incomplete",
        )
        self.assertEqual(architecture, original)

        hackathon = {
            "status": "approved",
            "completed_sections": list(_common.HACKATHON_ARCHITECTURE_SECTIONS),
            "approval": {
                "approved_by": "Lead",
                "approved_at": "2026-10-08T00:00:00Z",
                "mode": "hackathon-24h",
            },
        }
        original_hackathon = copy.deepcopy(hackathon)
        self.assertTrue(
            _common.architecture_release(
                hackathon, {"operating_mode": "hackathon-24h"}
            ).released
        )
        self.assertEqual(
            _common.architecture_release(
                hackathon, {"operating_mode": "professional"}
            ).outcome,
            "incomplete",
        )
        self.assertEqual(hackathon, original_hackathon)

    def test_project_sync_hackathon_to_professional_switch_routes_to_architecture(self):
        architecture = {
            "status": "approved",
            "completed_sections": list(_common.HACKATHON_ARCHITECTURE_SECTIONS),
            "approval": {
                "approved_by": "Lead",
                "approved_at": "2026-10-08T00:00:00Z",
                "mode": "hackathon-24h",
            },
        }
        output = self.project_sync_output(
            {"operating_mode": "professional", "github": {}}, architecture
        )
        self.assertIn("Architecture release: incomplete", output)
        self.assertIn("Continue Architecture Kickoff", output)
        self.assertNotIn("Inspect your active GitHub task", output)

    def test_project_sync_professional_to_hackathon_switch_requires_active_mode_approval(self):
        architecture = {
            "status": "approved",
            "completed_sections": list(
                dict.fromkeys(
                    _common.PROFESSIONAL_ARCHITECTURE_SECTIONS
                    + _common.HACKATHON_ARCHITECTURE_SECTIONS
                )
            ),
            "approval": {
                "approved_by": "Lead",
                "approved_at": "2026-10-08T00:00:00Z",
                "mode": "professional",
            },
        }
        self.assertTrue(
            _common.architecture_release(
                architecture, {"operating_mode": "professional"}
            ).released
        )
        output = self.project_sync_output(
            {"operating_mode": "hackathon-24h", "github": {}}, architecture
        )
        self.assertIn("Architecture release: incomplete", output)
        self.assertIn("approval for the active mode", output)
        self.assertNotIn("Inspect your active GitHub task", output)

    def test_project_sync_invalid_release_reports_blocker(self):
        architecture = {
            "status": "approved",
            "completed_sections": list(_common.HACKATHON_ARCHITECTURE_SECTIONS),
            "approval": {
                "approved_by": "   ",
                "approved_at": "2026-10-08T00:00:00Z",
                "mode": "hackathon-24h",
            },
        }
        output = self.project_sync_output(
            {"operating_mode": "hackathon-24h", "github": {}}, architecture
        )
        self.assertIn("Architecture release: invalid", output)
        self.assertIn("BLOCKED:", output)
        self.assertNotIn("Inspect your active GitHub task", output)

    def test_project_sync_non_object_architecture_reports_blocker(self):
        for architecture in ([], None):
            with self.subTest(architecture=architecture):
                output = self.project_sync_output(
                    {"operating_mode": "hackathon-24h", "github": {}}, architecture
                )
                self.assertIn("Architecture release: invalid", output)
                self.assertIn("BLOCKED: architecture-state.json must contain a JSON object", output)
                self.assertNotIn("Traceback", output)
                self.assertNotIn("Inspect your active GitHub task", output)

    def test_project_sync_released_architecture_routes_to_implementation(self):
        architecture = {
            "status": "approved",
            "completed_sections": list(_common.HACKATHON_ARCHITECTURE_SECTIONS),
            "approval": {
                "approved_by": "Lead",
                "approved_at": "2026-10-08T00:00:00Z",
                "mode": "hackathon-24h",
            },
        }
        output = self.project_sync_output(
            {"operating_mode": "hackathon-24h", "github": {}}, architecture
        )
        self.assertIn("Architecture release: released", output)
        self.assertIn("Inspect your active GitHub task", output)

    def test_verification_and_independent_review_remain_required(self):
        policies = json.loads((ROOT / ".orchestrator" / "policies.json").read_text(encoding="utf-8"))
        review_contract = (ROOT / "response-contracts" / "pr-review.md").read_text(encoding="utf-8")
        guide = (ROOT / "docs" / "workspace" / "hackathon-mode.md").read_text(encoding="utf-8")
        self.assertIs(policies["verification_required"], True)
        self.assertIs(policies["independent_review_required"], True)
        self.assertIn("## Engineering Quality", review_contract)
        self.assertIn("small vertical slice -> verify -> independent review -> integrate", guide)

    def test_active_architecture_state_uses_compact_checklist(self):
        state = json.loads(
            (ROOT / ".orchestrator" / "architecture-state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            tuple(state["pending_sections"]),
            tuple(
                section for section in _common.HACKATHON_ARCHITECTURE_SECTIONS
                if section not in state["completed_sections"]
            ),
        )

    def test_non_object_workspace_config_is_rejected_cleanly(self):
        for value in ([], None, "professional", 123):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "workspace.config.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "JSON object at its root"):
                    _common.read_json_object(path, {}, "workspace.config.json")

    def test_bootstrap_reports_non_object_config_as_not_ready(self):
        output = io.StringIO()
        with (
            patch.object(bootstrap, "check_prerequisites"),
            patch.object(
                bootstrap,
                "read_json_object",
                side_effect=ValueError("workspace.config.json must contain a JSON object at its root."),
            ),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(bootstrap.main(), 1)
        self.assertIn("NOT READY", output.getvalue())
        self.assertIn("workspace.config.json must contain a JSON object", output.getvalue())

    def test_verifier_reports_non_object_config_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "workspace.config.json").write_text("[]", encoding="utf-8")
            output = io.StringIO()
            with (
                patch.object(verify_workspace, "ROOT", root),
                patch.object(sys, "argv", ["verify_workspace.py", "--quick"]),
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(verify_workspace.main(), 1)
        self.assertIn("workspace.config.json must contain a JSON object", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_verifier_rejects_duplicate_team_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            orchestrator = root / ".orchestrator"
            orchestrator.mkdir()
            (root / "workspace.config.json").write_text(
                json.dumps({"operating_mode": "professional"}), encoding="utf-8"
            )
            (orchestrator / "project-state.json").write_text("{}", encoding="utf-8")
            (orchestrator / "architecture-state.json").write_text("{}", encoding="utf-8")
            (orchestrator / "policies.json").write_text(json.dumps({
                "task_publication_requires_architecture_approval": True,
                "verification_required": True,
                "independent_review_required": True,
            }), encoding="utf-8")
            member = {"id": "same", "name": "One", "github": "one", "role": "dev", "status": "active"}
            duplicate = {**member, "name": "Two", "github": "two"}
            (orchestrator / "team.json").write_text(json.dumps({
                "lead_architect_member_id": None,
                "members": [member, duplicate],
            }), encoding="utf-8")
            output = io.StringIO()
            with (
                patch.object(verify_workspace, "ROOT", root),
                patch.object(sys, "argv", ["verify_workspace.py", "--quick"]),
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(verify_workspace.main(), 1)
        self.assertIn("FAIL | Team registry | Duplicate member ID", output.getvalue())


if __name__ == "__main__":
    unittest.main()
