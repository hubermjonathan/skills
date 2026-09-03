# skills

skills for coding agents.

## skills

| skill | what it does |
|-------|--------------|
| `caveman` | compressed response style. cuts output tokens, keeps technical substance. levels: lite, full, ultra (default) |

## install

via `npx skills`:

```sh
npx -y skills add hubermjonathan/skills -g -y -a claude-code -s caveman
```

or as a claude code plugin marketplace:

```sh
/plugin marketplace add hubermjonathan/skills
```

## always-on

a skill only activates when something triggers it. to make `caveman` the default for every
session rather than a per-session opt-in, assert it in `~/.claude/CLAUDE.md`:

```md
- always respond using the caveman skill in ultra mode
```

`hubermjonathan/dot` does this in its `claude` module.
