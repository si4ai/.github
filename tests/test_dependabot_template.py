"""Fixture checks for templates/dependabot.yml (standard library only).

The template is a version 2 config with weekly pip and github-actions
entries, and the github-actions updates are grouped into one PR.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "dependabot.yml"


class DependabotTemplate(unittest.TestCase):
    def setUp(self):
        self.text = TEMPLATE.read_text(encoding="utf-8")

    def test_version_2(self):
        self.assertRegex(self.text, r"(?m)^version: 2$")

    def test_ecosystems_weekly(self):
        eco = re.findall(r"(?m)^  - package-ecosystem: (\S+)$", self.text)
        self.assertEqual(eco, ["pip", "github-actions"])
        self.assertEqual(len(re.findall(r"(?m)^      interval: weekly$", self.text)), 2)

    def test_actions_grouped(self):
        self.assertIn('      actions:\n        patterns: ["*"]\n', self.text)


if __name__ == "__main__":
    unittest.main()
