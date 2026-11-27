"""Fixture checks for tools/check_hidden_code.py, the action-pin check.

Run: python3 -m unittest discover -s tests -v

An added `uses:` line pinned to a tag is reported as not pinned to a
40-hex sha; one pinned to a full sha is not. The report exits 0 on a
finding unless --strict is given. A docs-only change is clean even
with --strict.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent / "tools"
WF = ".github/workflows/ci.yml"
BASE_WF = (
    "name: ci\n"
    "on: [pull_request]\n"
    "jobs:\n"
    "  test:\n"
    "    runs-on: ubuntu-latest\n"
    "    steps:\n"
    "      - run: echo hi\n"
)
PINNED = "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1\n"
TAGGED = "      - uses: actions/checkout@v4\n"


def git(root: Path, *args: str) -> str:
    env = dict(os.environ, GIT_AUTHOR_NAME="ci", GIT_AUTHOR_EMAIL="ci@example.com",
               GIT_COMMITTER_NAME="ci", GIT_COMMITTER_EMAIL="ci@example.com",
               GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")
    return subprocess.run(["git", *args], cwd=root, env=env, check=True,
                          capture_output=True, text=True).stdout.strip()


class ActionPinFixtures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        (self.root / ".github" / "workflows").mkdir(parents=True)
        (self.root / WF).write_text(BASE_WF, encoding="utf-8")
        (self.root / "README.md").write_text("readme\n", encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "base")
        self.base = git(self.root, "rev-parse", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def change(self, rel: str, text: str) -> None:
        (self.root / rel).write_text(text, encoding="utf-8")
        git(self.root, "commit", "-q", "-am", "change")

    def scan(self, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(TOOLS / "check_hidden_code.py"), "--root", str(self.root),
             "--base", self.base, "--head", "HEAD", *extra],
            capture_output=True, text=True, timeout=120,
        )

    def unpinned(self, r: subprocess.CompletedProcess) -> list[dict]:
        return [f for f in json.loads(r.stdout)["findings"]
                if "not pinned to a 40-hex sha" in f["reason"]]

    def test_tag_pin_reported_not_gated(self):
        self.change(WF, BASE_WF + TAGGED)
        r = self.scan("--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        hits = self.unpinned(r)
        self.assertEqual(len(hits), 1, r.stdout)
        self.assertEqual(hits[0]["path"], WF)

    def test_tag_pin_strict_fails(self):
        self.change(WF, BASE_WF + TAGGED)
        r = self.scan("--strict")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_sha_pin_not_reported(self):
        self.change(WF, BASE_WF + PINNED)
        r = self.scan("--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.unpinned(r), [], r.stdout)

    def test_docs_only_clean_strict(self):
        self.change("README.md", "readme\nmore\n")
        r = self.scan("--strict")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
