# Dependabot

Dependabot reads only the repo's own `.github/dependabot.yml`. There is no
way to call a shared config the way a workflow is called, so each repo
keeps a small copy of the template.

`templates/dependabot.yml` is repo-context-optimizer's config, byte for
byte: weekly pip updates for the root `pyproject.toml`, and weekly
github-actions updates grouped into one PR.

To adopt it in a repo:

1. Copy `templates/dependabot.yml` to `.github/dependabot.yml`.
2. Drop the pip entry if the repo has no Python packages; add one entry
   per extra manifest folder (the-mill adds `/tools/ci-lock`, an npm
   folder and a docker folder).
3. Turn on dependabot security updates in the repo settings, under code
   security. Only a repo admin can do that.

The github-actions entry also bumps the `si4ai/.github` pins in caller
workflows, since a reusable workflow ref is updated like an action.
The template does not change when a repo adds entries; compare by hand
when the template changes.
