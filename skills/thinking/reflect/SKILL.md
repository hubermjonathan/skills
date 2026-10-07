---
name: reflect
description: Mine the session so far for durable learnings and turn each into an edit to a skill, an agent instruction file, a setting, or a new skill. Works mid-session.
disable-model-invocation: true
---

# Reflect

Turn what happened in this session into durable changes to the setup that produced it: skills, agent instruction files (CLAUDE.md, AGENTS.md, and the like), settings, and hooks. Runs mid-session, so the work in progress stays where it is and resumes after.

Skip when nothing durable happened. One-offs are not learnings.

## Pick the mode

- **Quick**: the user points at a moment ("reflect on that", "reflect: you should have checked the ticket first"). Take that one learning straight to step 4 as a single Accepted row. No fan-out.
- **Full**: plain "reflect". Run every step.

## 1. Locate the transcript

Run `../show-me-your-work/scripts/find-transcript.sh "<a distinctive phrase from this conversation's first user message>"`, relative to this skill's directory. It prints the matching session file and reads nothing from any other session. If it finds nothing, set `TRANSCRIPT_DIRS` to your agent's session store if you know it and retry. If the transcript is still out of reach, write a tight digest of the session and pass that instead.

## 2. Spawn three reviewers in parallel

Spawn three background subagents in one batch, one per lens. Pass each template verbatim with the transcript path or digest substituted where marked.

| Lens | Prompt template |
|---|---|
| Judgment | `references/judgment-reviewer.md` |
| Tooling | `references/tooling-reviewer.md` |
| Divergent | `references/divergent-reviewer.md` |

If your agent lets you pick models, give the tooling lens a different model from the other two, from the same provider, so one reviewer reasons differently. If your agent has no subagents, run the three lenses yourself one after another, each as a separate pass over the transcript.

Keep working on the user's task while they run, if there is one.

## 3. Synthesize

One more subagent, with `references/synthesizer.md` verbatim and each reviewer's full output inlined where marked. It returns an Accepted, Rejected, and Backlog list.

Then check the Accepted list yourself: an item a hook, script, lint rule, or permission rule would enforce more reliably than prose moves to a `settings` or `structural` routing.

## 4. Present and wait

Show the Accepted, Rejected, and Backlog output, numbered, and wait for the user to pick. They may approve a subset or redirect a routing. Config changes shape every future session, so nothing is applied without a yes.

## 5. Apply

Find the real file before editing anything:

- Resolve symlinks with `readlink -f`. A symlinked CLAUDE.md or settings file is edited at its target, which usually lives in a dotfiles repo.
- Never edit an installed copy of a plugin or skill that your agent manages, such as a plugin cache. It is overwritten on update. Find the source checkout of that plugin's repo and edit there.
- A skill from a repo the user owns is edited in that repo, on a branch, following its own AGENTS.md or CLAUDE.md.

Then follow each approved row's routing:

- `edit skill: <skill> <section>`: make the edit.
- `tune description: <skill>`: the skill existed and did not fire when it should have. Add the case it missed to its description, as a situation, not a phrase to match.
- `new skill: <name>`: create the skill.
- `instructions: <file> <section>`: add or tighten a line in the agent instruction file the routing names (global, machine-local, or project: CLAUDE.md, AGENTS.md, or your agent's equivalent). One rule, one place. Replace a weaker existing line instead of adding a second.
- `settings: <file>`: a hook, permission, or env change in your agent's config file. Read the agent's docs for the format before editing.
- `structural: <mechanism>`: a script, lint rule, or check. Build it if small, otherwise it goes to Backlog.

Validate what you touched when the repo has a validator, such as a plugin manifest validator.

## 6. Summarize

Short list, no preamble:

- Applied: `<file>`, what changed, one line each.
- New skills: `<path>`, one line each.
- Backlog: one line each. Offer to append them to a working file named `reflect-backlog.md`.
- Dropped: one line per rejected finding, with the synthesizer's reason.

Then pick the interrupted task back up where it stopped.
