# The validator gate

`.github/workflows/validator.yml` runs `tools/check_validator_pass.py`
(sha256 `3e5bb9aa...`). The script lives here; the-mill calls this
workflow (card 1336). It trusts one creator: the si4ai-validator app
(`si4ai-validator[bot]`, type Bot). A `validator` status from anyone else
counts as neither pass nor fail.

- merge_group: passes only when every PR in the queue entry has a
  `validator` success on its head sha. No PR found fails closed.
- pull_request: reports WAITING or REPORT and passes, so a PR can wait
  for its verdict without a red check.

Where it runs today: the-mill's `validator.yml` calls it from job
`validator_pass`, so the check is `validator_pass / validator_pass`
(card 1336). The-mill's main ruleset requires the `validator`
status itself (posted by the app), not `validator_pass`. repo-context-optimizer's
`validator.yml` holds different, repo-specific jobs (`readme_ledger`,
`config_tamper`); those stay in that repo.

A caller adds `.github/workflows/validator.yml`:

```yaml
name: validator
on:
  pull_request:
    types: [opened, synchronize, reopened]
  merge_group:
permissions:
  contents: read
concurrency:
  group: validator-${{ github.event_name }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
jobs:
  validator:
    permissions:
      contents: read
      pull-requests: read
      statuses: read
    uses: si4ai/.github/.github/workflows/validator.yml@<40-hex sha>
```

The check is then named `validator / validator_pass`. Require either
it or the `validator` status in the main ruleset so the merge queue
enforces the verdict; which one is a ruleset decision for the human. The
validator app must be installed on the repo to post its status.
