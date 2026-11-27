# The hidden-code report and the action-pin check

`.github/workflows/hidden_code.yml` runs `tools/check_hidden_code.py`, a
byte-identical copy of repo-context-optimizer's script (`4570220d`,
sha256 `e82cc7a9...`). Section 4 of the report is the action-pin check:
an added `uses:` line under `.github/**` that is not pinned to a full
40-hex sha is reported as `uses not pinned to a 40-hex sha`.

Where it runs today, each with its own copy:

- repo-context-optimizer: `ci.yml` job `hidden_code_report`, a required
  check on main.
- the-mill: `ci.yml` job `hidden_code_report` (card 1155), an older copy
  of the script, not a required check.

Call it from a job in the caller's `ci.yml` with pull_request, push and
merge_group triggers:

```yaml
  hidden_code:
    permissions:
      contents: read
    uses: si4ai/.github/.github/workflows/hidden_code.yml@<40-hex sha>
    # with:
    #   strict: true   # fail on any finding; default false is report only
```

The check is then named `hidden_code / hidden_code_report`. A repo that
requires the old `hidden_code_report` name must change the required
check in its ruleset in the same step as the switch.

The caller's optional `ci/hidden-code.toml` (map, control_plane, locks)
and its `ci/test-select.toml` map are read from the caller's tree.
