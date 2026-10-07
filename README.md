# Skills

Skills for coding agents. Every skill lives under [`skills/`](skills) as a plain
`SKILL.md`, so any agent that speaks the skill format can use this repo. Claude Code and
Codex each get a native plugin on top of that.

## Install

### Any agent

```sh
npx -y skills add hubermjonathan/skills
```

This is the main path. It copies the skills into whichever agent you point it at and works
for agents with no plugin system of their own.

### Claude Code

As a marketplace, which picks up every skill in the repo and keeps them updated together:

```sh
claude plugin marketplace add hubermjonathan/skills
claude plugin install skills@hubermjonathan
```

Or from inside a session:

```
/plugin marketplace add hubermjonathan/skills
```

To declare it in `~/.claude/settings.json` instead, user scope, since project and local
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

### Codex

```sh
codex plugin marketplace add hubermjonathan/skills
codex plugin install skills
```

The repo carries a portable [`plugin.json`](plugin.json) and a Codex marketplace manifest at
[`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json). Each skill also ships an
`agents/openai.yaml` so it gets a proper display name in Codex.

## Skills

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`audit-skills`](skills/thinking/audit-skills/SKILL.md) | Measures from past session transcripts how often each skill loads when it should, and proposes fixes for the misses | Yes |
| [`brief`](skills/thinking/brief/SKILL.md) | Turns an investigation, the session, or a block of text into a short, plain, non-technical version for Slack, Jira, or a PR | No |
| [`explain-by-example`](skills/thinking/explain-by-example/SKILL.md) | Explains something in more depth by walking through one concrete example, step by step | No |
| [`grill-me`](skills/thinking/grill-me/SKILL.md) | Interviews you round by round to stress-test a plan, decision, or idea | No |
| [`reflect`](skills/thinking/reflect/SKILL.md) | Mines the session so far and turns learnings into skill, instruction file, or settings edits | Yes |
| [`show-me-your-work`](skills/thinking/show-me-your-work/SKILL.md) | Keeps a TSV decision log for long or unattended runs | No |
| [`swarm`](skills/thinking/swarm/SKILL.md) | Fans out parallel workers (slices or races) and returns one report. `review-code` uses it for multi-reviewer runs | No |
| [`technical-writing`](skills/thinking/technical-writing/SKILL.md) | Layered writing standard for chat replies, docs, PRs, tickets, and commits | No |
| [`unslop`](skills/thinking/unslop/SKILL.md) | Rewrites text to strip AI writing tells | No |
| [`writing-for-agents`](skills/thinking/writing-for-agents/SKILL.md) | Writes skills, CLAUDE.md, AGENTS.md, and prompts for subagents and other sessions | No |
| [`refine-ticket`](skills/planning/refine-ticket/SKILL.md) | Turns a ticket into a plan you agree with before any code | No |
| [`babysit-pr`](skills/coding/babysit-pr/SKILL.md) | Drives a PR to green checks, answered comments, and approval | No |
| [`comment-pr`](skills/coding/comment-pr/SKILL.md) | Reads every kind of PR comment and replies in the right place | No |
| [`git`](skills/coding/git/SKILL.md) | Branch, worktree, commit, and cleanup conventions | No |
| [`kill-comments`](skills/coding/kill-comments/SKILL.md) | Deletes code comments and "what" docs so code is the what and docs are the why | No |
| [`open-pr`](skills/coding/open-pr/SKILL.md) | Opens a draft PR with a fixed title and body format | No |
| [`pr-walkthrough`](skills/coding/pr-walkthrough/SKILL.md) | Builds a CodeRabbit-style change stack page for a human reviewer: changes grouped by area of impact in reading order, what each group depends on, the ticket's asks mapped to the diff, questions only the author can answer, and reading checkboxes | No |
| [`principles`](skills/coding/principles/SKILL.md) | Six code-level principles `write-code` reads before building | No |
| [`push-pr`](skills/coding/push-pr/SKILL.md) | Pushes to an open PR, then fixes its title and body to match | No |
| [`review-code`](skills/coding/review-code/SKILL.md) | Reviews a PR against its ticket, optionally fixes the findings | No |
| [`write-code`](skills/coding/write-code/SKILL.md) | Smallest change that solves the problem, then a simplification pass | No |
| [`run-test-plan`](skills/shipping/run-test-plan/SKILL.md) | Runs a test plan against an environment and records evidence for each step | No |
| [`write-test-plan`](skills/shipping/write-test-plan/SKILL.md) | Writes a before and after test plan an agent can run | No |
| [`design-profile:use`](skills/tools/design-profile/skills/use/SKILL.md) | Styles an HTML page with a named design profile | No |
| [`design-profile:install`](skills/tools/design-profile/skills/install/SKILL.md) | Installs or updates a design profile from local files | Yes |
| [`design-profile:create`](skills/tools/design-profile/skills/create/SKILL.md) | Mines a design system into a new profile | Yes |
| [`imessage`](skills/tools/imessage/SKILL.md) | Texts you an iMessage from a Mac, for example when a long task finishes or needs you | No |
| [`slack`](skills/tools/slack/SKILL.md) | Drafts and sends short Slack messages | No |

## Adding a skill

See [AGENTS.md](AGENTS.md).
