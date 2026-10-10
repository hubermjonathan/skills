---
name: kill-comments
description: >
  Delete code comments and "what" docs so the code is the only source of truth for
  what it does, and docs carry only the why. Use after writing or changing code,
  before opening or pushing to a PR, or when asked to remove code comments or trim
  docs down to the why.
---

The code says what. Docs say why. A comment that restates the code is a second copy that drifts, and a comment that explains confusing code is an apology for code that should be clearer.

## Scope

- Default: every comment on a line the current diff adds or touches, against `origin/<base>`, plus any doc file the diff changes.
- Given a path or a PR: that scope instead, whole files included.
- Nothing outside the scope. Unrelated files stay untouched so the PR stays small.

## What survives

Only these, and only when you are sure one applies. In doubt, the comment dies.

1. License and legal headers.
2. Tool directives the build reads: `//go:build`, `// prettier-ignore`, `# type: ignore[...]`, `@SuppressWarnings`, `noqa`, `eslint-disable`, and the like. A suppression survives only if its rule is style-only or wrong here. If the rule guards correctness or safety, delete the suppression and flag the code under it.
3. Behavior forced by something outside our control: a vendor quirk, a protocol requirement, a platform bug. Before keeping one, prove the claim is still true today, by reading the dependency's docs or code.
4. A link to an issue, RFC, or vendor doc that explains a constraint the code cannot express.
5. Doc comments that define the contract of an API consumed outside this repo: a published library or a client other teams import. Internal services, handlers, and private helpers are not that.
6. Doc comments the repo's lint config requires. Keep them to the minimum the rule accepts.

## What dies

Everything else, including:

- narration of what the next lines do
- comments that repeat a name, a type, or a signature
- commented-out code
- section banners and dividers
- TODOs, FIXMEs, and "temporary" notes. The tracker holds work, not the code
- change history: "added for ABC-123", "fixed the bug where", author tags, dates
- "important", "do not remove", "fine for now", and other warnings with no proven reason behind them
- a long justification of a workaround in our own code

## Surprises in our own code

When a comment exists because our own code is confusing, delete the comment and flag the exact symbol as `RESHAPE`, with one line on the fix that would make the comment unnecessary: a better name, an extracted function, a type, a constant. Do not make that change yourself. This skill edits comments and docs, never code.

## Docs

Apply the same rule to READMEs, docstrings, and markdown docs in scope.

Delete the "what":

- lists of functions, endpoints, fields, or config keys that the code or its schema already shows
- step-by-step walkthroughs of what the code does
- parameter and return descriptions that repeat the types

Keep the "why":

- decisions and the reasons behind them
- constraints and tradeoffs, and approaches that were tried and rejected
- how to run, deploy, or operate the thing, which the code cannot tell you

Flag any doc sentence that contradicts the code as `STALE`, with the file and line of the code it contradicts.

## Report

- files touched and comments deleted per file
- each `RESHAPE` and `STALE` flag in one line with `file:line`
- each comment kept, with the survival rule that saved it
