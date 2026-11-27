# CodeQL

`.github/workflows/codeql.yml` is the-mill's CodeQL job as a reusable
workflow: one `analyze` job per language, `build-mode: none`, the same
pinned `actions/checkout` and `github/codeql-action` shas. Two inputs:

- `languages`: a JSON list, default `["python", "actions"]`.
- `config-file`: a path in the caller's tree, default empty (the stock
  queries). The-mill passes `./.github/codeql/codeql-config.yml`, which
  swaps two stock clear-text queries for its own pack; those queries stay
  in the-mill.

Where it runs today: the-mill's `codeql.yml` calls it from job `analyze`
(card 1336), so its checks are `analyze / analyze (python)` and
`analyze / analyze (actions)`. The-mill's main ruleset requires
`analyze (python)` and `analyze (actions)` today; those names change
with the call. repo-context-optimizer
has no CodeQL yet.

A caller adds `.github/workflows/codeql.yml`:

```yaml
name: codeql
on:
  push:
    branches: [main]
  pull_request:
  merge_group:
  schedule:
    - cron: "17 6 * * 1"
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: codeql-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
jobs:
  codeql:
    permissions:
      contents: read
      security-events: write
    uses: si4ai/.github/.github/workflows/codeql.yml@<40-hex sha>
    # with:
    #   languages: '["python", "actions"]'
    #   config-file: ./.github/codeql/codeql-config.yml
```

The checks are then named `codeql / analyze (python)` and so on. A repo
that requires the old `analyze (...)` names changes its ruleset in the
same step. Keep merge_group in the triggers if analyze is required, or
the queue waits on it.
