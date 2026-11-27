# si4ai/.github

Shared checks, the org-default PR template, and the guide for a new public
si4ai repo. Repos call these workflows; they do not copy them.

## What is here

| Path | What it is |
| --- | --- |
| `.github/workflows/pr_text.yml` | Reusable PR and issue text scan (title, body, comments on post and edit; daily sweep). Fails on a hit. |
| `.github/workflows/hygiene.yml` | Reusable hygiene report on the commit range and the PR title and body. Report only unless `strict: true`. |
| `.github/pull_request_template.md` | Org-default PR template (brief, claims, evidence, done check, risks, changelog). GitHub uses it for any repo that has no template of its own. |
| `tools/` | The scripts the workflows run. |
| `tests/` | Fixture tests for those scripts; `ci.yml` runs them. |

The scripts are byte-identical copies. Until the source repos call these
workflows themselves, fix a script upstream first, then copy it here.

| File | Copied from | sha256 |
| --- | --- | --- |
| `tools/check_pr_text.py` | the-mill `2c8e08e7` | `a2553c16...` |
| `tools/check_pack.py` | the-mill `2c8e08e7` | `f5d25a21...` |
| `tools/docs_only.py` | the-mill `2c8e08e7` | `e6863fc3...` |
| `tools/hygiene_words.txt` | the-mill `2c8e08e7` | `e9bff478...` |
| `tools/check_hygiene.py` | repo-context-optimizer `4570220d` | `f2b8ec7d...` |

## Turn on the shared checks in a new public repo

Pin `uses:` to a full commit sha of this repo's main, never a branch or
tag. Each workflow checks out this repo at that same sha
(`job.workflow_sha`), so the pin covers the scripts too. Dependabot's
`github-actions` updates bump the pin like any other action.

`.github/workflows/pr_text.yml` in the caller:

```yaml
name: pr_text
on:
  pull_request:
    types: [opened, edited, synchronize, reopened]
  issues:
    types: [opened, edited]
  issue_comment:
    types: [created, edited]
  schedule:
    - cron: "17 6 * * *"
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: pr-text-${{ github.event_name }}-${{ github.event.pull_request.number || github.event.issue.number || github.run_id }}
  cancel-in-progress: true
jobs:
  pr_text:
    permissions:
      contents: read
      issues: read
      pull-requests: read
    uses: si4ai/.github/.github/workflows/pr_text.yml@<40-hex sha>
```

A job in the caller's `ci.yml`, with the caller's own pull_request, push
and merge_group triggers:

```yaml
  hygiene_report:
    permissions:
      contents: read
    uses: si4ai/.github/.github/workflows/hygiene.yml@<40-hex sha>
    # with:
    #   strict: true   # fail on any finding; default false is report only
```

What each check reads from the caller:

- pr_text: the ordinary-word list is the shared `tools/hygiene_words.txt`
  plus every lower-case word in the caller's tree, as in the-mill.
- hygiene: the caller's optional `ci/hygiene.toml` (roles, words_file,
  words) and its `tools/hygiene_words.txt`.

A Title-case word that the caller never uses in lower case reads as a
name. Keep a `tools/hygiene_words.txt` in the repo (start from
repo-context-optimizer's) and make sure it lists the template headings:
brief, claims, evidence, done, check, risks, changelog.

## Required checks and the merge queue

Set these with a branch ruleset on main (repo-context-optimizer's is the
model):

- Block deletion and force pushes; require a pull request (0 approvals,
  dismiss stale approvals); allowed merge methods merge and squash.
- Required status checks, strict (branch up to date): the repo's own test
  jobs (for example `pytest`, `spin`) and `hidden_code_report`.
- Merge queue: merge method MERGE (merge commits are the default),
  grouping ALLGREEN, build up to 5, merge 1 to 5, no wait, 60 minute
  check timeout.
- Do not make `pr_text` required: it does not run in the merge queue.
  `hygiene_report` is required only if the caller sets `strict: true`.

The validator measures each PR and merges through the queue. Builder
never merges to main.

## Releases

Each repo keeps its own release flow for now:

- the-mill: `docs/dev/RELEASE-FLOW.md`.
- repo-context-optimizer: `release.yml`, a `v*` tag on main publishes to
  PyPI through trusted publishing.

The Python build, tag and PyPI release moves here only when a third repo
needs it. Non-Python repos will not call it.

## Shared checks, one page each

Each has its own page under `docs/`:

- `docs/hidden-code.md`: the hidden-code report with the action-pin check.
- `docs/validator-pass.md`: the validator gate for the merge queue.
- `docs/codeql.md`: CodeQL code scanning.
- `docs/dependabot.md`: the Dependabot template and how a repo adopts it.

Test suites, readme ledger and claims, RCO pack checks and the-mill SQL
tests stay in each repo.
