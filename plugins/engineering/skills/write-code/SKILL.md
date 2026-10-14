---
name: write-code
description: >
  How to implement a change: smallest code that solves the problem, repo conventions
  first, one simplification pass before handing off. Use when implementing a plan,
  building a feature, fixing a bug, or making any code change.
---

1. Know the ask. Work from the plan or the user's request. If a decision is open, ask. If several are, invoke the `grill-me` skill.
2. Invoke the `principles` skill and read the files that apply to this change.
3. Read before writing: the repo's CLAUDE.md or AGENTS.md and the code around the change. The repo's conventions win over habits from another repo.
4. When the change is built, invoke the `kill-comments` skill.
5. Simplification pass. Read your complete diff against the base branch in one go. Remove accidental complexity, dead code, and anything the ask does not require. Report what you removed.
6. Run the narrowest build, lint, and tests that cover the change, and fix what fails.

If the plan turns out to be wrong, stop and say so. Do not quietly redesign it and carry on.
