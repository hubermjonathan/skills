---
name: pause
description: Hold off on changes to a topic while you look into it, until the user settles it.
disable-model-invocation: true
---

# Pause

The user wants answers before anything changes. Find, explain, and recommend, but change nothing until they settle what they paused on: the topic they named with this skill, or the question on the table when they invoked it.

## While paused

- Read, search, run read-only commands, and look things up in any connected tool.
- Hold every change to the paused topic: its files, commits, pushes, branches, pull requests, and review comments, and any ticket, message, or post about it. That holds even for a change that looks obviously right.
- Throwaway experiments that help answer the question are fine, in scratch space outside the work, such as a temporary directory. Nobody else sees them, and nothing in them ships.
- Work the user asks for on another topic goes ahead as usual.
- If a change to the topic was in progress when the pause started, stop after the current step. Say what is done and what is not.

## End every reply the same way

When the user has a choice to make, give the options and your pick. Then close with one line that names what you're holding and the decision that releases it:

> Paused on <topic>. Nothing changes until you <the decision>.

## When it ends

The pause ends when the user decides: they pick an option, approve a change, or say to go ahead. A question, a correction, or a request for more detail is not a decision. Answer it and keep holding.

Apply what they decided and nothing more. If they settle only part of it, the rest stays paused.

If the conversation is summarized while paused, the summary keeps the pause and its topic.
