# Repo conventions

Skills live at `skills/<group>/<name>/SKILL.md`, one folder per skill. The first five groups
follow the steps of a change: `planning`, `coding`, `reviewing`, `pull-requests`, and `testing`.
The other four cut across them: `writing`, `communicating`, `agents`, and `tools`. Add a group
only when a skill fits none of these. The skill folder name, the `name` in frontmatter, and the
skill's invocation name all match. Names stay unique across groups, since the group never shows up
in the invocation name.

`skills/tools/design-profile/` is a second plugin, `design-profile`, with its own manifests and an
entry in both marketplace files. Its skills sit at `skills/tools/design-profile/skills/<name>/`, so
their names only need to be unique inside it.

## Agent agnostic

Every skill works in any agent that loads `SKILL.md` files. Skill text names no agent's tools,
models, or file paths: say "invoke the `x` skill", "spawn a background subagent", "run it as a
background process", not an agent's tool names. When a script needs to know about specific agents,
such as where each one stores session logs, the script holds that list with an env var override,
and the skill text stays generic.

## Invocation

Choose model-invoked or user-invoked as `writing-for-agents` describes. Mirror the choice in both
harnesses, so it never differs by agent:

| | `SKILL.md` frontmatter | `agents/openai.yaml` | `description` |
|---|---|---|---|
| Model-invoked, the default | `name`, `description` | `interface` only | Model-facing: when to use the skill, as situations the agent recognizes, such as "use when asked to babysit a PR, get its checks passing, or get it ready to merge" |
| User-invoked | adds `disable-model-invocation: true` | adds `policy.allow_implicit_invocation: false` | Human-facing: a one-line summary read while browsing slash commands |

`agents/openai.yaml` holds Codex-only presentation metadata, `interface.display_name` and
`interface.short_description`, plus the policy for a user-invoked skill. Every other agent ignores
it, so nothing else goes there.

## When adding or renaming a skill

- Add or update its row in the skills table in `README.md`, linking the name to its `SKILL.md`
  and filling the `User invoked` column with `Yes` or `No`
- Add or update its `agents/openai.yaml`
- For a new group, add the group folder to the `skills` array in `.claude-plugin/plugin.json`.
  Claude Code does not scan nested folders

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

`README.md`, `AGENTS.md`, and `SKILL.md` bodies are in sentence case. Commit messages follow the
`git` skill.

Join clauses with a comma, colon, period, or conjunction. Never use an em-dash, or a character
standing in for one.
