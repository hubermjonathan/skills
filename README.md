# skills

skills for coding agents. this repo is a claude code plugin marketplace named
`hubermjonathan`, exposing a single plugin, `skills`, that carries everything under
[`skills/`](skills).

## install

as a marketplace, which picks up every skill in the repo and keeps them updated together:

```sh
claude plugin marketplace add hubermjonathan/skills
claude plugin install skills@hubermjonathan
```

or from inside a session:

```
/plugin marketplace add hubermjonathan/skills
```

to declare it in `~/.claude/settings.json` instead — user scope, since project and local
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

`hubermjonathan/dot` declares it this way in its `claude` module.

for a single skill without the marketplace, or for a non-claude agent:

```sh
npx -y skills add hubermjonathan/skills -g -y -a claude-code -s <skill>
```

`--all` takes every skill, and `-a '*'` every supported agent. note the agent token is
`claude-code`, not `claude`.

## skills

| skill | what it does |
|-------|--------------|
| [`caveman`](skills/caveman) | compressed response style. cuts output tokens, keeps technical substance. levels: lite, full, ultra |

## adding a skill

drop `skills/<name>/SKILL.md` with `name` and `description` frontmatter. that layout satisfies
both the plugin convention and `npx skills` discovery, so either install path picks it up. bump
`version` in `.claude-plugin/plugin.json` so installed copies refresh.
