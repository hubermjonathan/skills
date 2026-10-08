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

Each skill sits in a group folder under [`skills/`](skills). The first five groups follow the steps of a change, and the other four cut across them.

### Planning

Settle the plan before any code.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`grill-me`](skills/planning/grill-me/SKILL.md) | Interviews you round by round to stress-test a plan, decision, or idea | No |
| [`refine-ticket`](skills/planning/refine-ticket/SKILL.md) | Turns a ticket into a plan you agree with before any code | No |

### Coding

Write the change.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`git`](skills/coding/git/SKILL.md) | Branch, worktree, commit, and cleanup conventions | No |
| [`kill-comments`](skills/coding/kill-comments/SKILL.md) | Deletes code comments and "what" docs so code is the what and docs are the why | No |
| [`principles`](skills/coding/principles/SKILL.md) | Six code-level principles `write-code` reads before building | No |
| [`write-code`](skills/coding/write-code/SKILL.md) | Smallest change that solves the problem, then a simplification pass | No |

### Reviewing

Check a change before it merges.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`pr-walkthrough`](skills/reviewing/pr-walkthrough/SKILL.md) | Builds a CodeRabbit-style change stack page for a human reviewer: changes grouped by area of impact in reading order, what each group depends on, the ticket's asks mapped to the diff, questions only the author can answer, and reading checkboxes | No |
| [`review-code`](skills/reviewing/review-code/SKILL.md) | Reviews a PR against its ticket, optionally fixes the findings | No |

### Pull requests

Open a PR and get it merged.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`babysit-pr`](skills/pull-requests/babysit-pr/SKILL.md) | Drives a PR to green checks, answered comments, and approval | No |
| [`comment-pr`](skills/pull-requests/comment-pr/SKILL.md) | Reads every kind of PR comment and replies in the right place | No |
| [`open-pr`](skills/pull-requests/open-pr/SKILL.md) | Opens a PR, ready for review, with a fixed title and body format | No |
| [`push-pr`](skills/pull-requests/push-pr/SKILL.md) | Pushes to an open PR, then fixes its title and body to match | No |

### Testing

Prove a change works on a deployed environment.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`run-test-plan`](skills/testing/run-test-plan/SKILL.md) | Runs a test plan against an environment and records evidence for each step | No |
| [`write-test-plan`](skills/testing/write-test-plan/SKILL.md) | Writes a before and after test plan an agent can run | No |

### Writing

Standards for how prose reads, whether a person or an agent reads it.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`technical-writing`](skills/writing/technical-writing/SKILL.md) | Layered writing standard for chat replies, docs, PRs, tickets, and commits | No |
| [`unslop`](skills/writing/unslop/SKILL.md) | Strips AI writing tells from PR bodies, tickets, Slack, and docs | No |
| [`writing-for-agents`](skills/writing/writing-for-agents/SKILL.md) | Writes skills, CLAUDE.md, AGENTS.md, and prompts for subagents and other sessions | No |

### Communicating

Get something to a person.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`brief`](skills/communicating/brief/SKILL.md) | Turns an investigation, the session, or a block of text into a short, plain, non-technical version for someone outside the work | No |
| [`explain-by-example`](skills/communicating/explain-by-example/SKILL.md) | Explains something in more depth by walking through one concrete example, step by step | No |
| [`imessage`](skills/communicating/imessage/SKILL.md) | Texts you an iMessage from a Mac, for example when a long task finishes or needs you | No |
| [`slack`](skills/communicating/slack/SKILL.md) | Drafts and sends short Slack messages | No |

### Agents

How agents run work, and how the skills improve.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`audit-skills`](skills/agents/audit-skills/SKILL.md) | Measures from past session transcripts how often each skill loads when it should, and proposes fixes for the misses | Yes |
| [`find-transcript`](skills/agents/find-transcript/SKILL.md) | Finds this session's transcript, or lists where agents keep session transcripts | No |
| [`reflect`](skills/agents/reflect/SKILL.md) | Mines the session so far and turns learnings into skill, instruction file, or settings edits | Yes |
| [`show-me-your-work`](skills/agents/show-me-your-work/SKILL.md) | Keeps a TSV decision log for long or unattended runs | No |
| [`swarm`](skills/agents/swarm/SKILL.md) | Fans out parallel workers (slices or races) and returns one report. `review-code` uses it for multi-reviewer runs | No |

### Tools

Single-purpose utilities.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`create-qr-code`](skills/tools/create-qr-code/SKILL.md) | Makes a QR code for a link and shows it in the reply | No |
| [`design-profile:use`](skills/tools/design-profile/skills/use/SKILL.md) | Styles an HTML page with a named design profile | No |
| [`design-profile:create`](skills/tools/design-profile/skills/create/SKILL.md) | Adds a design profile from finished files, or mines one from a design system | Yes |

## Adding a skill

See [AGENTS.md](AGENTS.md).
