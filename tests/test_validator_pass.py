"""Fixture checks for tools/check_validator_pass.py, the validator gate.

Run: python3 -m unittest discover -s tests -v

The API is a fake fetch, so no network. In the merge queue, a PR whose
head has a `validator` success from the validator app passes; the same
status from any other creator, or no PR in the entry, fails. On a pull
request the job reports and passes.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import check_validator_pass as cvp  # noqa: E402

REPO = "si4ai/example"
HEAD = "a" * 40
BASE = "b" * 40
QHEAD = "c" * 40
APP = {"login": "si4ai-validator[bot]", "type": "Bot"}
PERSON = {"login": "someone", "type": "User"}


def status(creator: dict, state: str, sid: int = 1) -> dict:
    return {"id": sid, "context": "validator", "state": state, "creator": creator,
            "url": f"https://api.github.com/repos/{REPO}/statuses/{HEAD}"}


def fake(statuses: list[dict]):
    def fetch(path: str):
        if path.startswith(f"/repos/{REPO}/compare/"):
            return {"commits": []}
        if path == f"/repos/{REPO}/pulls/5":
            return {"head": {"sha": HEAD}}
        if path.startswith(f"/repos/{REPO}/commits/{HEAD}/statuses"):
            return statuses
        raise AssertionError(path)
    return fetch


def queue_event(n: int = 5) -> dict:
    return {"merge_group": {"head_ref": f"refs/heads/gh-readonly-queue/main/pr-{n}-{QHEAD}",
                            "base_sha": BASE, "head_sha": QHEAD}}


def run(name: str, event: dict, statuses: list[dict]) -> tuple[int, list[str]]:
    lines: list[str] = []
    rc = cvp.run(name, event, REPO, fake(statuses), out=lines.append)
    return rc, lines


class ValidatorPassFixtures(unittest.TestCase):
    def test_queue_passes_on_app_success(self):
        rc, lines = run("merge_group", queue_event(), [status(APP, "success")])
        self.assertEqual(rc, 0, lines)

    def test_queue_ignores_other_creator(self):
        rc, lines = run("merge_group", queue_event(), [status(PERSON, "success")])
        self.assertEqual(rc, 1, lines)
        self.assertIn("missing", lines[0])

    def test_queue_latest_app_status_wins(self):
        rc, lines = run("merge_group", queue_event(),
                        [status(APP, "failure", 2), status(APP, "success", 1)])
        self.assertEqual(rc, 1, lines)

    def test_queue_without_pr_fails_closed(self):
        event = {"merge_group": {"head_ref": "refs/heads/other", "base_sha": BASE, "head_sha": QHEAD}}
        rc, lines = run("merge_group", event, [])
        self.assertEqual(rc, 1, lines)

    def test_pull_request_reports_and_passes(self):
        event = {"pull_request": {"number": 5, "head": {"sha": HEAD}}}
        rc, lines = run("pull_request", event, [])
        self.assertEqual(rc, 0, lines)
        self.assertTrue(lines[0].startswith("WAITING"), lines)


if __name__ == "__main__":
    unittest.main()
