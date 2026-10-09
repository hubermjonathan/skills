---
name: pause
description: Hold off on every change while you look into something, until the user settles it.
disable-model-invocation: true
---

# Pause

The user wants answers before anything changes. Find, explain, and recommend, but change nothing until they settle what they paused on: the topic they named with this skill, or the question on the table when they invoked it.

## While paused

- Read, search, run read-only commands, and look things up in any connected tool.
- Change nothing: no file edits, commits, pushes, branches, pull requests, or review comments, and no tickets, messages, or other posts. That holds even for a change that looks obviously right.
- If a change was in progress when the pause started, stop after the current step. Say what is done and what is not.

## End every reply the same way

When the user has a choice to make, give the options and your pick. Then close with one line that names what you're holding and the decision that releases it:

> Paused on <topic>. Nothing changes until you <the decision>.

## When it ends

The pause ends when the user decides: they pick an option, approve a change, or say to go ahead. A question, a correction, or a request for more detail is not a decision. Answer it and keep holding.

Apply what they decided and nothing more. If they settle only part of it, the rest stays paused.

If the conversation is summarized while paused, the summary keeps the pause and its topic.
