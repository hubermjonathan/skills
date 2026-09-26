---
name: switch-design-profile
description: Switch which design profile HTML artifacts use, or turn profiles off.
disable-model-invocation: true
allowed-tools: [Bash]
---

# Switch the active design profile

```sh
sh scripts/switch-profile.sh --show     # what is selected now, and what is installed
sh scripts/switch-profile.sh acme       # switch to an installed profile
sh scripts/switch-profile.sh none       # opt out — the design-profile skill stands down
```

Writes the profile name to the mode file `~/.claude/artifact-design-profile`, one word on one line.
The resolver reads it on every run, so **the change applies to the next artifact — no restart**. It
refuses a name that is not installed, so it cannot select a profile that will fail to resolve; `none`
is always accepted.

Run `--show` first when the person hasn't named a profile — don't guess one.

The mode file is the whole mechanism: no settings edit, no restart, nothing else to check.
