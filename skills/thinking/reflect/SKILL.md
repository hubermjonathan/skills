---
name: reflect
description: Mine the session so far for durable learnings and turn each into an edit to a skill, a CLAUDE.md, a setting, or a new skill. Works mid-session.
disable-model-invocation: true
---

# Reflect

Turn what happened in this session into durable changes to the setup that produced it: skills, CLAUDE.md files, settings, and hooks. Runs mid-session, so the work in progress stays where it is and resumes after.

Skip when nothing durable happened. One-offs are not learnings.

## Pick the mode

- **Quick**: the user points at a moment ("reflect on that", "reflect: you should have checked the ticket first"). Take that one learning straight to step 4 as a single Accepted row. No fan-out.
- **Full**: plain "reflect". Run every step.

## 1. Locate the transcript

Claude Code writes each session to `~/.claude/projects/<encoded-dir>/<session-id>.jsonl`, where the encoded dir is the session's starting directory with `/` and `.` replaced by `-`. Subagent transcripts sit under `<session-id>/subagents/`.

```bash
ls -t ~/.claude/projects/<encoded-dir>/*.jsonl | head -5
```

Take the newest file whose first user message matches this conversation's opening prompt. Read only the first line of the other candidates. If none matches, write a tight digest of the session and pass that instead.

## 2. Spawn three reviewers in parallel

One message, three Agent calls, `subagent_type: general-purpose`, `run_in_background: true`. Pass each template verbatim with the transcript path or digest substituted where marked.

| Lens | `model` | Prompt template |
|---|---|---|
| Judgment | `opus` | `references/judgment-reviewer.md` |
| Tooling | `sonnet` | `references/tooling-reviewer.md` |
| Divergent | `opus` | `references/divergent-reviewer.md` |

Keep working on the user's task while they run, if there is one.

## 3. Synthesize

One Agent call, `model: opus`, with `references/synthesizer.md` verbatim and each reviewer's full output inlined where marked. It returns an Accepted, Rejected, and Backlog list.

Then check the Accepted list yourself: an item a hook, script, lint rule, or permission rule would enforce more reliably than prose moves to a `settings` or `structural` routing.

## 4. Present and wait

Show the Accepted, Rejected, and Backlog output, numbered, and wait for the user to pick. They may approve a subset or redirect a routing. Config changes shape every future session, so nothing is applied without a yes.

## 5. Apply

Find the real file before editing anything:

- Resolve symlinks with `readlink -f`. A symlinked CLAUDE.md or settings file is edited at its target, which usually lives in a dotfiles repo.
- Never edit an installed plugin copy under `~/.claude/plugins/cache/`. It is overwritten on update. Find the source checkout of that plugin's repo and edit there.
- A skill from a repo the user owns is edited in that repo, on a branch, following its own AGENTS.md or CLAUDE.md.

Then follow each approved row's routing:

- `edit skill: <skill> <section>`: a one-line bullet or a corrected fact is edited directly. Anything bigger, call the Skill tool with "writing-for-agents" first.
- `tune description: <skill>`: the skill existed and did not fire when it should have. Rewrite its description's triggers. Call the Skill tool with "writing-for-agents" first.
- `new skill: <name>`: call the Skill tool with "skill-creator" if it is installed, and "writing-for-agents".
- `claude md: <file> <section>`: add or tighten a line in the global, machine-local, or project CLAUDE.md the routing names. One rule, one place. Replace a weaker existing line instead of adding a second.
- `settings: <file>`: a hook, permission, or env change. Call the Skill tool with "update-config".
- `structural: <mechanism>`: a script, lint rule, or check. Build it if small, otherwise it goes to Backlog.

Validate what you touched when the repo has a validator, such as `claude plugin validate . --strict` for a plugin repo.

## 6. Summarize

Short list, no preamble:

- Applied: `<file>`, what changed, one line each.
- New skills: `<path>`, one line each.
- Backlog: one line each. Offer to append them to `.scratch/reflect-backlog.md`.
- Dropped: one line per rejected finding, with the synthesizer's reason.

Then pick the interrupted task back up where it stopped.
