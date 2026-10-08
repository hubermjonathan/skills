# Repo conventions

Skills live at `skills/<group>/<name>/SKILL.md`, one folder per skill. The first five groups
follow the steps of a change: `planning`, `coding`, `reviewing`, `pull-requests`, and `testing`.
The other four cut across them: `writing`, `communicating`, `agents`, and `tools`. Add a group
only when a skill fits none of these. The skill folder name, the `name` in frontmatter, and the
skill's invocation name all match. Names stay unique across groups, since the group never shows up
in the invocation name.

Claude Code does not scan nested folders, so every group folder is listed in the
`skills` array of `.claude-plugin/plugin.json`. A new group gets a new entry there.

The design profile skills are their own plugin, `design-profile`, at `skills/tools/design-profile/`,
so they invoke as `design-profile:create`, `design-profile:install`, and `design-profile:use`. It has
its own manifests and an entry in both marketplace files. Its skills sit at
`skills/tools/design-profile/skills/<name>/`, so their names only need to be unique inside it.

## Agent agnostic

Every skill works in any agent that loads `SKILL.md` files. Skill text names no agent's tools,
models, or file paths: say "invoke the `x` skill", "spawn a background subagent", "run it as a
background process", not an agent's tool names. When a script needs to know about specific agents,
such as where each one stores session logs, the script holds that list with an env var override,
and the skill text stays generic.

## Invocation

A skill is either model-invoked or user-invoked, and the setting is mirrored in both harnesses
so it never differs by agent.

**Model-invoked** is the default: the model can reach for it on its own. Omit
`disable-model-invocation` from the frontmatter and the `policy` block from `agents/openai.yaml`.
The `description` is model-facing. It says when to use the skill as cases ("use when asked to
babysit a PR, get its checks passing, or get it ready to merge"), never as quoted phrases to
match: the agent infers from the situation rather than matching strings.

**User-invoked** means only the human typing its name can fire it, never the model. Set both:

- `disable-model-invocation: true` in `SKILL.md` frontmatter, for Claude Code
- `policy.allow_implicit_invocation: false` in `agents/openai.yaml`, for Codex

The `description` is then human-facing, a one-line summary read while browsing slash commands,
with no trigger list.

## Files

`SKILL.md` frontmatter carries `name`, `description`, and, for user-invoked skills only,
`disable-model-invocation`.

`agents/openai.yaml`, next to each `SKILL.md`, holds Codex-only presentation metadata
(`interface.display_name`, `interface.short_description`) and, for user-invoked skills, the
invocation policy. It is not part of the `SKILL.md` standard and every other agent ignores it,
so nothing else belongs there.

## When adding or renaming a skill

- Add or update the row in the skills table in `README.md`, linking the name to its `SKILL.md`
  and filling the `user invoked` column with `Yes` or `No`
- Add or update `agents/openai.yaml` for the skill, with the `policy` block if user-invoked

## Manifests

| File | Who reads it |
|------|--------------|
| `plugin.json` | Portable agent-plugins manifest, used by Codex |
| `.claude-plugin/plugin.json` | Claude Code plugin |
| `.claude-plugin/marketplace.json` | Makes the repo its own Claude marketplace |
| `.agents/plugins/marketplace.json` | Makes the repo its own Codex marketplace |

No manifest sets `version`, so each commit counts as a new version and an update always pulls
it. Run `claude plugin validate .` after touching either Claude manifest. Skip `--strict`, which
fails on the missing version.

## Prose

All prose uses normal sentence case: `README.md`, `AGENTS.md`, and `SKILL.md` bodies. Commit
messages follow the `git` skill.

No em-dashes anywhere. Rewrite the sentence with a comma, colon, period, or conjunction
instead of substituting a character.
