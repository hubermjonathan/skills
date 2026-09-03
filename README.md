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

or without the marketplace, which also covers non-claude agents:

```sh
npx -y skills add hubermjonathan/skills
```

## skills

| skill | what it does |
|-------|--------------|
| [`caveman`](skills/caveman) | compressed response style. cuts output tokens, keeps technical substance. levels: lite, full, ultra |

## adding a skill

drop `skills/<name>/SKILL.md` with `name` and `description` frontmatter. that layout satisfies
both the plugin convention and `npx skills` discovery, so either install path picks it up. bump
`version` in `.claude-plugin/plugin.json` so installed copies refresh.
