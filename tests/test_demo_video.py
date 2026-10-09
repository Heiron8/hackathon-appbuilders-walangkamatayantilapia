from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DemoVideoTests(unittest.TestCase):
    def test_role_and_skill_are_discoverable(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        for location in ('agents/demo-video-producer/CHARTER.md', 'skills/demo-video/SKILL.md', 'demo/README.md'):
            self.assertIn(location, readme)
            self.assertTrue((ROOT / location).is_file())
        skill = (ROOT / 'skills/demo-video/SKILL.md').read_text(encoding='utf-8')
        metadata = skill.split('---', 2)[1]
        self.assertIn('name: demo-video', metadata)
        self.assertIn('do not load for normal frontend/backend development', metadata)

    def test_links_and_existing_submission_integration_resolve(self):
        for location in ('agents/demo-video-producer/CHARTER.md', 'skills/demo-video/SKILL.md', 'demo/README.md'):
            source = ROOT / location
            content = source.read_text(encoding='utf-8')
            # Source links must resolve in a clean clone; ignored rehearsal media
            # links describe local evidence and are checked by the media pipeline.
            for link in re.findall(r'\]\(([^)]+\.md)\)', content):
                if not link.startswith('https://'):
                    self.assertTrue((source.parent / link).resolve().is_file(), link)
            self.assertIn('submission-readiness.md', content)

    def test_demo_dependencies_and_artifacts_are_isolated(self):
        package = json.loads((ROOT / 'demo/package.json').read_text(encoding='utf-8'))
        self.assertTrue(package['private'])
        self.assertTrue(all(re.fullmatch(r'\d+\.\d+\.\d+', version) for version in package['dependencies'].values()))
        paths = ['demo/node_modules/probe', 'demo/output/probe.mp4']
        result = subprocess.run(['git', 'check-ignore', *paths], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(result.stdout.splitlines()), set(paths))

    def test_pipeline_behavior(self):
        # Optional media capability: clean workspace verification needs only Python.
        # When installed, the canonical suite exercises actual behavioral checks too.
        node = shutil.which('node')
        if not node or not (ROOT / 'demo/node_modules/ffmpeg-static').exists():
            self.skipTest('Demo dependencies absent; run npm --prefix demo ci and npm --prefix demo test')
        result = subprocess.run([node, '--test', 'test/pipeline.test.mjs'], cwd=ROOT / 'demo',
                                capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
