from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "technical-defense" / "SKILL.md"
CONTRACT = ROOT / "response-contracts" / "technical-defense.md"
CHECKLIST = ROOT / "docs" / "qa" / "submission-readiness.md"


class TechnicalDefenseTests(unittest.TestCase):
    def test_skill_is_discoverable_with_narrow_trigger(self):
        skill = SKILL.read_text(encoding="utf-8")
        metadata = skill.split("---", 2)[1]
        self.assertIn("name: technical-defense", metadata)
        self.assertIn("judge Q&A", metadata)
        self.assertIn("do not load during normal coding work", metadata)
        self.assertIn("skills/technical-defense/SKILL.md", (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_supporting_markdown_links_resolve(self):
        for path in (SKILL, CONTRACT, ROOT / "docs" / "workspace" / "hackathon-mode.md"):
            text = path.read_text(encoding="utf-8")
            links = re.findall(r"\]\(([^)]+\.md(?:#[^)]+)?)\)", text)
            self.assertTrue(links, path.name)
            for link in links:
                with self.subTest(path=path.name, link=link):
                    self.assertTrue((path.parent / link.split("#", 1)[0]).resolve().is_file())

    def test_templates_have_no_prefilled_product_or_submission_values(self):
        for path in (CONTRACT, CHECKLIST):
            text = path.read_text(encoding="utf-8")
            metadata = text.split("##", 1)[0]
            fields = re.findall(r"^- [^\n:]+:(.*)$", metadata, re.MULTILINE)
            self.assertTrue(fields, path.name)
            self.assertTrue(all(not value.strip() for value in fields), path.name)
            self.assertNotRegex(text, r"https?://|(?i:appbuilders)")
        rows = [line for line in CHECKLIST.read_text(encoding="utf-8").splitlines() if line.startswith("| ")][2:]
        self.assertTrue(rows)
        for row in rows:
            cells = [cell.strip() for cell in row.split("|")[1:-1]]
            self.assertEqual(len(cells), 4)
            self.assertEqual(cells[1:], ["", "", ""])

    def test_evidence_rules_and_q_and_a_qualifications_are_present(self):
        skill = SKILL.read_text(encoding="utf-8")
        checklist = CHECKLIST.read_text(encoding="utf-8")
        contract = CONTRACT.read_text(encoding="utf-8")
        for status in ("VERIFIED", "KNOWN BUT NOT VERIFIED", "NOT READY", "NOT APPLICABLE"):
            self.assertIn(f"**{status}:**", checklist)
        for gap in ("NOT DOCUMENTED", "NEEDS TEAM CONFIRMATION"):
            self.assertIn(gap, skill)
            self.assertIn(gap, contract)
        for field in ("SHORT ANSWER", "DEEPER ANSWER", "EVIDENCE"):
            self.assertIn(field, contract)
        self.assertIn("missing evidence into PASS", checklist)
        self.assertIn("Workspace harness verification is not product verification", skill)
        self.assertIn("Omit AI-specific questions when the product has no AI", skill)
        self.assertIn("Do not force MVC", skill)

    def test_hackathon_final_stretch_references_support_in_order(self):
        guide = (ROOT / "docs" / "workspace" / "hackathon-mode.md").read_text(encoding="utf-8").split("## Final stretch and deferred work", 1)[1]
        sequence = (
            "feature freeze",
            "canonical verification",
            "public smoke test",
            "technical-defense preparation",
            "demo/video preparation",
            "submission readiness check",
        )
        positions = [guide.index(step) for step in sequence]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("adds no architecture approval gate", guide)


if __name__ == "__main__":
    unittest.main()
