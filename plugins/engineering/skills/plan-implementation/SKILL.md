---
name: plan-implementation
description: >
  Plan how to build a ready ticket before any code is written: the approach, what
  it touches, and the check that proves each acceptance criterion. Use when starting
  work on a ticket, or when asked how a change should be built.
---

You plan how to build one ticket. The `write-code` skill builds from your plan, so you write no code here.

1. Read the whole ticket. If it isn't ready to build, as the `refine-ticket` skill defines, invoke that skill first.
2. Read the code the change touches: the files, their callers and tests, and the repo's agent instruction file, such as `AGENTS.md`.
3. Choose the approach: the smallest change that meets every acceptance criterion, as the `principles` skill describes. When the ticket and the code leave a real choice between approaches, bring the user the options and your pick, and wait for their answer.
4. Write the plan to a working file named `<ticket-key>-plan.md`, with these sections:
   - **Approach**: what changes, in a few sentences.
   - **Files and surfaces**: each file, endpoint, schema, or config the change touches, and what changes there.
   - **Tests**: for each acceptance criterion, the test or check that proves it.
   - **Out of scope**
   - **Open questions resolved**: each choice from step 3, with its answer and why.
5. Reply with the plan's path and its approach in one or two sentences, then stop.

**Done when:** every acceptance criterion maps to a change in "Files and surfaces" and to a check in "Tests".

"Open questions resolved" is the only record of why the plan is what it is. A later reader uses it to tell a wrong fix from a wrong design, so never skip it.
