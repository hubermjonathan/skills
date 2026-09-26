---
name: principles
description: >
  Code-level engineering principles: smallest change, subtract first, fix root
  causes, prove it works, low reader load, encode repeated fixes in tooling. Use
  when writing, refactoring, or debugging code, or when another skill needs them.
---

# Principles

Six principles for writing code. Read the file for each one that applies to the change in front of you, before you write it.

| Principle | Read it when | File |
|---|---|---|
| Laziness protocol | always, before writing any code | `laziness-protocol.md` |
| Subtract before you add | adding to, refactoring, or rewriting existing code | `subtract-before-you-add.md` |
| Fix root causes | debugging, or fixing a bug or a failing check | `fix-root-causes.md` |
| Prove it works | before calling any change done | `prove-it-works.md` |
| Minimize reader load | adding a layer, a wrapper, or a piece of state, or reviewing code that is hard to trace | `minimize-reader-load.md` |
| Encode lessons in structure | writing the same instruction or fix a second time | `encode-lessons-in-structure.md` |

Adapted from the principle skills in [cursor/plugins pstack](https://github.com/cursor/plugins/tree/main/pstack), MIT licensed. See `LICENSE`.
