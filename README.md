# skills

skills for coding agents. every skill lives under [`skills/`](skills) as a plain
`SKILL.md`, so any agent that speaks the skill format can use this repo. claude code and
codex each get a native plugin on top of that.

## install

### any agent

```sh
npx -y skills add hubermjonathan/skills
```

this is the main path. it copies the skills into whichever agent you point it at and works
for agents with no plugin system of their own.

### claude code

as a marketplace, which picks up every skill in the repo and keeps them updated together:

```sh
claude plugin marketplace add hubermjonathan/skills
claude plugin install skills@hubermjonathan
```

or from inside a session:

```
/plugin marketplace add hubermjonathan/skills
```

to declare it in `~/.claude/settings.json` instead, user scope, since project and local
scope cannot vouch for a marketplace:

```json
{
  "extraKnownMarketplaces": {
    "hubermjonathan": {
      "source": { "source": "github", "repo": "hubermjonathan/skills" }
    }
  },
  "enabledPlugins": { "skills@hubermjonathan": true }
}
```

### codex

```sh
codex plugin marketplace add hubermjonathan/skills
codex plugin install skills
```

the repo carries a portable [`plugin.json`](plugin.json) and a codex marketplace manifest at
[`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json). each skill also ships an
`agents/openai.yaml` so it gets a proper display name in codex.

## skills

| skill | what it does | user invoked |
|-------|--------------|--------------|
| [`caveman`](skills/caveman/SKILL.md) | compressed response style. cuts output tokens, keeps technical substance. levels: lite, full, ultra | no |
| [`grill-me`](skills/grill-me/SKILL.md) | interviews you round by round to stress-test a plan, decision, or idea | yes |
| [`unslop`](skills/unslop/SKILL.md) | rewrites text to strip AI writing tells | yes |

## adding a skill

see [AGENTS.md](AGENTS.md).
