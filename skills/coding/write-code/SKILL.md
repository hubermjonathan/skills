---
name: write-code
description: >
  How to implement a change: smallest code that solves the problem, repo conventions
  first, one simplification pass before handing off. Use when implementing a plan,
  building a feature, fixing a bug, or when the user says "implement this", "build
  it", "make the change", or "fix it".
---

Core principle: as little code as required to solve the problem.

1. Know the ask. Work from the plan or the user's request. If a decision is open, ask. If several are, call the Skill tool with "grill-me".
2. Read before writing: the repo's CLAUDE.md or AGENTS.md and the code around the change. The repo's conventions win over habits from another repo, including how it versions releases and writes changelogs.
3. Build only what was asked. No speculative abstractions, config knobs, flags, or cleanup outside the change.
4. Add no code comments unless the user asks. The code is the source of truth. When the change is built, call the Skill tool with "kill-comments".
5. Run the narrowest build, lint, and tests that cover the change, and fix what fails.
6. Simplification pass. Read your complete diff against the base branch in one go. Remove accidental complexity, dead code, and anything the ask does not require. Report what you removed.

If the plan turns out to be wrong, stop and say so. Do not quietly redesign it and carry on.

When the user wants it committed, call the Skill tool with "git".
