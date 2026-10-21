# Skills

Skills for coding agents. Every skill is a plain `SKILL.md` under [`plugins/`](plugins), so any
agent that speaks the skill format can use this repo. Claude Code and Codex install them as
plugins, one per audience, from the `hubermjonathan` marketplace this repo hosts.

## Install

### Any agent

```sh
npx -y skills add hubermjonathan/skills
```

This is the main path. It copies the skills into whichever agent you point it at and works
for agents with no plugin system of their own.

### Claude Code

```sh
claude plugin marketplace add hubermjonathan/skills
claude plugin install engineering@hubermjonathan
claude plugin install design-profile@hubermjonathan
```

Installing `engineering` also installs `communication` and `agents`, which its skills call. To
declare them in `~/.claude/settings.json` instead, use user scope, since project and local scope
cannot vouch for a marketplace:

```json
{
  "extraKnownMarketplaces": {
    "hubermjonathan": {
      "source": { "source": "github", "repo": "hubermjonathan/skills" }
    }
  },
  "enabledPlugins": {
    "engineering@hubermjonathan": true,
    "communication@hubermjonathan": true,
    "agents@hubermjonathan": true,
    "design-profile@hubermjonathan": true
  }
}
```

### Codex

```sh
codex plugin marketplace add hubermjonathan/skills
codex plugin add engineering@hubermjonathan
codex plugin add communication@hubermjonathan
codex plugin add agents@hubermjonathan
codex plugin add design-profile@hubermjonathan
```

Codex has no plugin dependencies, so add each plugin you want.

## Skills

Each plugin is a folder under [`plugins/`](plugins), with one folder per skill in its `skills/`.

### Engineering

Take a code change from ticket to merge.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`refine-ticket`](plugins/engineering/skills/refine-ticket/SKILL.md) | Gets a ticket ready to build: requirements, acceptance criteria, technical facts, and a bug's reproduction | No |
| [`plan-implementation`](plugins/engineering/skills/plan-implementation/SKILL.md) | Plans how to build a ready ticket, and how to prove each acceptance criterion, before any code | No |
| [`principles`](plugins/engineering/skills/principles/SKILL.md) | Six code-level principles `write-code` reads before building | No |
| [`write-code`](plugins/engineering/skills/write-code/SKILL.md) | Smallest change that solves the problem, then a simplification pass | No |
| [`kill-comments`](plugins/engineering/skills/kill-comments/SKILL.md) | Deletes code comments and "what" docs so code is the what and docs are the why | No |
| [`git`](plugins/engineering/skills/git/SKILL.md) | Branch, worktree, commit, and cleanup conventions | No |
| [`review-code`](plugins/engineering/skills/review-code/SKILL.md) | Reviews a PR against its ticket, optionally fixes the findings | No |
| [`walk-through-pr`](plugins/engineering/skills/walk-through-pr/SKILL.md) | Builds a CodeRabbit-style change stack page for a human reviewer: changes grouped by area of impact in reading order, what each group depends on, the ticket's asks mapped to the diff, questions only the author can answer, and reading checkboxes | No |
| [`open-pr`](plugins/engineering/skills/open-pr/SKILL.md) | Opens a PR, ready for review, with a fixed title and body format | No |
| [`push-pr`](plugins/engineering/skills/push-pr/SKILL.md) | Pushes to an open PR, then fixes its title and body to match | No |
| [`comment-pr`](plugins/engineering/skills/comment-pr/SKILL.md) | Reads every kind of PR comment and replies in the right place | No |
| [`address-feedback`](plugins/engineering/skills/address-feedback/SKILL.md) | Sorts a PR's review feedback, makes and verifies the changes, pushes, and answers every comment | No |
| [`babysit-pr`](plugins/engineering/skills/babysit-pr/SKILL.md) | Drives a PR to green checks, answered comments, and approval | No |
| [`verify`](plugins/engineering/skills/verify/SKILL.md) | Proves a change builds, passes the checks CI will run, and does what it says, in a blind subagent, and writes the PR's evidence | No |
| [`write-test-plan`](plugins/engineering/skills/write-test-plan/SKILL.md) | Writes a before and after test plan an agent can run | No |
| [`run-test-plan`](plugins/engineering/skills/run-test-plan/SKILL.md) | Runs a test plan against an environment and records evidence for each step | No |

### Communication

Write for people and reach them.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`brief`](plugins/communication/skills/brief/SKILL.md) | Turns an investigation, the session, or a block of text into a short, plain, non-technical version for someone outside the work | No |
| [`create-qr-code`](plugins/communication/skills/create-qr-code/SKILL.md) | Makes a QR code for a link and shows it in the reply | No |
| [`explain-by-example`](plugins/communication/skills/explain-by-example/SKILL.md) | Explains something in more depth by walking through one concrete example, step by step | No |
| [`grill-me`](plugins/communication/skills/grill-me/SKILL.md) | Interviews you round by round to stress-test a plan, decision, or idea | No |
| [`send-slack-message`](plugins/communication/skills/send-slack-message/SKILL.md) | Drafts and sends short Slack messages | No |
| [`show-me`](plugins/communication/skills/show-me/SKILL.md) | Shows a point as the smallest visual that makes it clear: pseudocode, a call or file tree, a diagram, or a diff-shaped sketch | No |
| [`technical-writing`](plugins/communication/skills/technical-writing/SKILL.md) | Layered writing standard for chat replies, docs, PRs, tickets, and commits | No |
| [`unslop`](plugins/communication/skills/unslop/SKILL.md) | Strips AI writing tells from PR bodies, tickets, Slack, and docs | No |

### Agents

How agents run work, and how the skills improve.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`audit-skills`](plugins/agents/skills/audit-skills/SKILL.md) | Measures from past session transcripts how often each skill loads when it should, and proposes fixes for the misses | Yes |
| [`find-transcript`](plugins/agents/skills/find-transcript/SKILL.md) | Finds this session's transcript, or lists where agents keep session transcripts | No |
| [`pause`](plugins/agents/skills/pause/SKILL.md) | Holds off on changes to a topic while the agent explains or looks things up, until you settle it | Yes |
| [`reflect`](plugins/agents/skills/reflect/SKILL.md) | Mines a session, this one by default, and turns learnings into skill, instruction file, or settings edits | Yes |
| [`show-me-your-work`](plugins/agents/skills/show-me-your-work/SKILL.md) | Keeps a TSV decision log for long or unattended runs | No |
| [`swarm`](plugins/agents/skills/swarm/SKILL.md) | Fans out parallel workers (slices or races) and returns one report. `review-code` uses it for multi-reviewer runs | No |
| [`writing-for-agents`](plugins/agents/skills/writing-for-agents/SKILL.md) | Writes skills, CLAUDE.md, AGENTS.md, and prompts for subagents and other sessions | No |

### Design profile

Style HTML pages with a design system.

| Skill | What it does | User invoked |
|-------|--------------|--------------|
| [`create-design-profile`](plugins/design-profile/skills/create-design-profile/SKILL.md) | Adds a design profile from finished files, or mines one from a design system | Yes |
| [`use-design-profile`](plugins/design-profile/skills/use-design-profile/SKILL.md) | Styles an HTML page with a named design profile | No |

## Adding a skill

See [AGENTS.md](AGENTS.md).
