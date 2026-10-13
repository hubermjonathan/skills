# Repo conventions

Each plugin is a folder at `plugins/<plugin>/`, with one folder per skill at
`plugins/<plugin>/skills/<name>/SKILL.md`. Plugins split by audience, the people who would install
them. Add a plugin only when a skill's audience matches none of the existing ones.

This repo hosts the `hubermjonathan` marketplace. It lists every plugin, including `admin`, `sso`,
`factory`, and `factory-mono-repo-apps` from the private `hubermjonathan/dot-work` repo, which uses
the same layout.

## Names

- Name a skill that does a task by the task, verb first, with no prefix: `open-pr`,
  `send-slack-message`, `login-aws`. Name a skill that holds a standard by its topic: `principles`,
  `technical-writing`.
- The skill folder name and the `name` in frontmatter match.
- Skill names stay unique across every plugin in the marketplace, in both repos. `npx skills`
  installs skills flat by name, and a bare `/<name>` runs a skill, so a reused name hides another.
- Name a plugin for its audience, in kebab-case: `engineering`, `design-profile`.

## Agent agnostic

Every skill works in any agent that loads `SKILL.md` files. Skill text names no agent's tools,
models, or file paths: say "invoke the `x` skill", "spawn a background subagent", "run it as a
background process", not an agent's tool names. When a script needs to know about specific agents,
such as where each one stores session logs, the script holds that list with an env var override,
and the skill text stays generic.

## Waiting

When a skill waits on CI, a deploy, or a bot, say how to tell it's done from a signal the agent can
check, such as a check run, a run's status, or the live version, and what failure looks like. Leave
out how long it usually takes: CI load and service size change that, so a duration goes stale. A
polling interval or a soak time the user chose is fine.

## Stages

A stage skill, such as `open-pr` or `deploy-prod`, does its one stage, reports what it finished,
and stops. Only a factory skill, such as dot-work's `run-mono-repo-apps-factory`, starts the next
stage. A stage skill may still invoke another skill for work its own stage needs, the way `open-pr`
gets its evidence from `verify`.

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

## Manifests

`.claude-plugin/marketplace.json` is the only manifest you edit. It holds each plugin's name,
display name, description, source, and dependencies. Claude Code reads each entry as that plugin's
manifest, so no plugin has a `.claude-plugin/plugin.json`.

- A plugin's `dependencies` list each plugin whose skills it tells the agent to invoke by name,
  and each plugin whose skill one of its skills overlays, such as `slack-conventions` over
  `send-slack-message`.
- No manifest sets `version`, so each commit counts as a new version and an update always pulls it.
- To rename or remove a plugin, map its old name in `renames`, so existing installs follow it.

## After a change

Run `scripts/sync-plugins.sh` after you edit the marketplace or add, rename, or move a skill. It
writes the Codex marketplace, `.agents/plugins/marketplace.json`, and each plugin's portable
`plugin.json`, the one Codex reads. It reaches dot-work's plugins through a checkout beside this
repo, or under `REPOS_DIR`. Then it checks every skill and runs `claude plugin validate .`. It fails
until each skill has its row in its plugin's table in `README.md` and its `agents/openai.yaml`.
`scripts/sync-plugins.sh --check` writes nothing and fails on any file out of date.

When you rename a skill, update every "invoke the `x` skill" that names it, in both repos.
