---
name: principles
description: >
  Engineering principles for any change, whether code, config, docs, or a skill:
  generic over one-off, smallest change, subtract first, fix root causes, prove it
  works, low reader load, encode repeated fixes in tooling. Use before shaping a
  solution, when debugging, or when another skill needs them.
---

# Principles

Six principles for any change, whether code, config, docs, or a skill. Read the file for each one that applies to the change in front of you, before you make it.

| Principle | Read it when | File |
|---|---|---|
| Laziness protocol | always, before any change | `laziness-protocol.md` |
| Subtract before you add | adding to, refactoring, or rewriting something that exists | `subtract-before-you-add.md` |
| Fix root causes | debugging, or fixing a bug or a failing check | `fix-root-causes.md` |
| Prove it works | before calling any change done | `prove-it-works.md` |
| Minimize reader load | adding a layer, a wrapper, or a piece of state, or reviewing code that is hard to trace | `minimize-reader-load.md` |
| Encode lessons in structure | writing the same instruction or fix a second time | `encode-lessons-in-structure.md` |
