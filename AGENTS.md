# repo conventions

skills live at `skills/<name>/SKILL.md`, one folder per skill, flat. the folder name, the
`name` in frontmatter, and the skill's invocation name all match.

`SKILL.md` frontmatter carries `name` and `description` only. the description is what an agent
reads to decide whether to load the skill, so it says what the skill does and when to reach
for it.

`skills/<name>/agents/openai.yaml` holds codex-only presentation metadata (`interface.display_name`,
`interface.short_description`). it is not part of the `SKILL.md` standard and every other agent
ignores it, so nothing behavioral belongs there.

## when adding or renaming a skill

- add or update the row in the skills table in `README.md`, linking the name to its `SKILL.md`
- add or update `agents/openai.yaml` for the skill
- bump `version` in both `plugin.json` and `.claude-plugin/plugin.json`, keeping them identical,
  so installed copies refresh

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
