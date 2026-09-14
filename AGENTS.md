# repo conventions

skills live at `skills/<name>/SKILL.md`, one folder per skill, flat. the folder name, the
`name` in frontmatter, and the skill's invocation name all match.

## invocation

a skill is either model-invoked or user-invoked, and the setting is mirrored in both harnesses
so it never differs by agent.

**model-invoked** is the default: the model can reach for it on its own. omit
`disable-model-invocation` from the frontmatter and the `policy` block from `agents/openai.yaml`.
the `description` is model-facing, so it keeps trigger phrasing ("use when the user says...")
that auto-invocation matches against.

**user-invoked** means only the human typing its name can fire it, never the model. set both:

- `disable-model-invocation: true` in `SKILL.md` frontmatter, for claude code
- `policy.allow_implicit_invocation: false` in `agents/openai.yaml`, for codex

the `description` is then human-facing, a one-line summary read while browsing slash commands,
with no trigger list.

## files

`SKILL.md` frontmatter carries `name`, `description`, and, for user-invoked skills only,
`disable-model-invocation`.

`skills/<name>/agents/openai.yaml` holds codex-only presentation metadata
(`interface.display_name`, `interface.short_description`) and, for user-invoked skills, the
invocation policy. it is not part of the `SKILL.md` standard and every other agent ignores it,
so nothing else belongs there.

## when adding or renaming a skill

- add or update the row in the skills table in `README.md`, linking the name to its `SKILL.md`
- add or update `agents/openai.yaml` for the skill, with the `policy` block if user-invoked
- bump `version` in both `plugin.json` and `.claude-plugin/plugin.json`, keeping them identical,
  so installed copies refresh. once per pr, not per commit: if the branch already carries a
  bump, amend that value instead of bumping again

## manifests

| file | who reads it |
|------|--------------|
| `plugin.json` | portable agent-plugins manifest, used by codex |
| `.claude-plugin/plugin.json` | claude code plugin |
| `.claude-plugin/marketplace.json` | makes the repo its own single-plugin claude marketplace |
| `.agents/plugins/marketplace.json` | makes the repo its own single-plugin codex marketplace |

run `claude plugin validate . --strict` after touching either claude manifest.

## prose

`README.md`, `AGENTS.md`, and commit messages are lowercase. `SKILL.md` bodies are
instructions an agent reads, so they use normal sentence case.

no em-dashes anywhere. rewrite the sentence with a comma, colon, period, or conjunction
instead of substituting a character.
