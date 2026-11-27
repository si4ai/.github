"""Fixture checks for the shared scripts in tools/ (standard library only).

Run: python3 -m unittest discover -s tests -v

A PR body with a made-up personal name fails pr_text and shows up in the
hygiene report; a clean body passes both. The hygiene report exits 0 on a
finding unless --strict is given.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "tools"
FIX = HERE / "fixtures"


def pr_text(event: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, GITHUB_EVENT_NAME="pull_request", GITHUB_EVENT_PATH=str(event))
    return subprocess.run(
        [sys.executable, str(TOOLS / "check_pr_text.py"), "event"],
        env=env, capture_output=True, text=True, timeout=120,
    )


def git(root: Path, *args: str) -> str:
    env = dict(os.environ, GIT_AUTHOR_NAME="ci", GIT_AUTHOR_EMAIL="ci@example.com",
               GIT_COMMITTER_NAME="ci", GIT_COMMITTER_EMAIL="ci@example.com")
    return subprocess.run(["git", *args], cwd=root, env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


class PrTextFixtures(unittest.TestCase):
    def test_name_token_fails(self):
        r = pr_text(FIX / "pr_name.json")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("PR #7 body:4: personal name token", r.stderr)
        self.assertNotIn("Zorblat", r.stdout + r.stderr)

    def test_clean_passes(self):
        r = pr_text(FIX / "pr_clean.json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("pr-text hygiene ok", r.stdout)


class TemplateFixture(unittest.TestCase):
    def test_org_template_passes_pr_text(self):
        import json
        body = (HERE.parent / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as d:
            ev = Path(d) / "event.json"
            ev.write_text(json.dumps({"pull_request": {
                "number": 1, "title": "Add the shared checks", "body": body,
                "user": {"login": "ci", "type": "User"},
                "base": {"sha": "0" * 40}, "head": {"sha": "1" * 40}}}), encoding="utf-8")
            r = pr_text(ev)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class HygieneFixtures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        # The tree is the ordinary-word list: a word used lower-case here is prose.
        (self.root / "a.txt").write_text("add the shared checks; brief\n", encoding="utf-8")
        # Heading words a caller allows mid-line go in its words file.
        (self.root / "tools").mkdir()
        (self.root / "tools" / "hygiene_words.txt").write_text("brief\nchangelog\n", encoding="utf-8")
        git(self.root, "add", "a.txt", "tools/hygiene_words.txt")
        git(self.root, "commit", "-q", "-m", "first")
        self.base = git(self.root, "rev-parse", "HEAD")
        (self.root / "a.txt").write_text("add the shared checks; brief\ntwo\n", encoding="utf-8")
        git(self.root, "commit", "-q", "-am", "second")

    def tearDown(self):
        self.tmp.cleanup()

    def run_hygiene(self, event: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(TOOLS / "check_hygiene.py"), "--root", str(self.root),
             "--base", self.base, "--head", "HEAD", "--event", str(event), *extra],
            capture_output=True, text=True, timeout=120,
        )

    def test_name_token_reported_not_gated(self):
        r = self.run_hygiene(FIX / "pr_name.json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("in PR body", r.stdout)
        self.assertNotIn("Zorblat", r.stdout + r.stderr)

    def test_name_token_strict_fails(self):
        r = self.run_hygiene(FIX / "pr_name.json", "--strict")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_clean_passes_strict(self):
        r = self.run_hygiene(FIX / "pr_clean.json", "--strict")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("no findings.", r.stdout)


if __name__ == "__main__":
    unittest.main()
