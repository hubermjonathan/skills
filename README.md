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
| [`brief`](skills/thinking/brief/SKILL.md) | turns an investigation, the session, or a block of text into a short, plain, non-technical version for slack, jira, or a pr | no |
| [`grill-me`](skills/thinking/grill-me/SKILL.md) | interviews you round by round to stress-test a plan, decision, or idea | no |
| [`reflect`](skills/thinking/reflect/SKILL.md) | mines the session so far and turns learnings into skill, instruction file, or settings edits | yes |
| [`show-me-your-work`](skills/thinking/show-me-your-work/SKILL.md) | keeps a tsv decision log for long or unattended runs | no |
| [`swarm`](skills/thinking/swarm/SKILL.md) | fans out parallel workers (slices or races) and returns one report. `review-code` uses it for multi-reviewer runs | no |
| [`technical-writing`](skills/thinking/technical-writing/SKILL.md) | layered writing standard for chat replies, docs, prs, tickets, and commits | no |
| [`unslop`](skills/thinking/unslop/SKILL.md) | rewrites text to strip ai writing tells | no |
| [`writing-for-agents`](skills/thinking/writing-for-agents/SKILL.md) | writes skills, CLAUDE.md, AGENTS.md, and prompts for subagents and other sessions | no |
| [`create-change-ticket`](skills/planning/create-change-ticket/SKILL.md) | creates the prod change ticket per service, linked to the original ticket | no |
| [`refine-ticket`](skills/planning/refine-ticket/SKILL.md) | turns a ticket into a plan you agree with before any code | no |
| [`babysit-pr`](skills/coding/babysit-pr/SKILL.md) | drives a pr to green checks, answered comments, and approval | no |
| [`comment-pr`](skills/coding/comment-pr/SKILL.md) | reads every kind of pr comment and replies in the right place | no |
| [`git`](skills/coding/git/SKILL.md) | branch, worktree, commit, and cleanup conventions | no |
| [`kill-comments`](skills/coding/kill-comments/SKILL.md) | deletes code comments and "what" docs so code is the what and docs are the why | no |
| [`open-pr`](skills/coding/open-pr/SKILL.md) | opens a draft pr with a fixed title and body format | no |
| [`principles`](skills/coding/principles/SKILL.md) | six code-level principles `write-code` reads before building | no |
| [`push-pr`](skills/coding/push-pr/SKILL.md) | pushes to an open pr, then fixes its title and body to match | no |
| [`review-code`](skills/coding/review-code/SKILL.md) | reviews a pr against its ticket, optionally fixes the findings | no |
| [`write-code`](skills/coding/write-code/SKILL.md) | smallest change that solves the problem, then a simplification pass | no |
| [`create-prod-pr`](skills/shipping/create-prod-pr/SKILL.md) | opens a prod promotion pr per service, sets up review and tickets | no |
| [`deploy-prod`](skills/shipping/deploy-prod/SKILL.md) | merges an approved prod pr, watches its actions, then hands off to `monitor-prod` | no |
| [`monitor-prod`](skills/shipping/monitor-prod/SKILL.md) | watches a prod rollout in datadog by version, flags regressions, closes the change ticket after a 30 minute soak. starts from a pr, a ticket, or a service and version | no |
| [`deploy-staging`](skills/shipping/deploy-staging/SKILL.md) | follows ci promotion prs until the change is on staging | no |
| [`walk-test-plan`](skills/shipping/walk-test-plan/SKILL.md) | walks a test plan one step at a time, recording each result | no |
| [`write-test-plan`](skills/shipping/write-test-plan/SKILL.md) | writes a staging test plan a later session can run | no |
| [`design-profile:use`](skills/tools/design-profile/skills/use/SKILL.md) | styles an html page with a named design profile | no |
| [`design-profile:install`](skills/tools/design-profile/skills/install/SKILL.md) | installs or updates a design profile from local files | yes |
| [`design-profile:create`](skills/tools/design-profile/skills/create/SKILL.md) | mines a design system into a new profile | yes |
| [`slack`](skills/tools/slack/SKILL.md) | drafts and sends short slack messages | no |
| [`wizard`](skills/tools/wizard/SKILL.md) | writes a bash wizard that walks you through steps only a human can do | no |

## adding a skill

see [AGENTS.md](AGENTS.md).
