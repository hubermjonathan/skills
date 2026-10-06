---
name: refine-ticket
description: >
  Turn a ticket into an implementation plan the user agrees with, before any code is
  written. Use when handed a ticket to plan, or when an approach needs settling
  before any code is written.
---

You refine one ticket into a plan. You do not write code here.

1. Read the whole ticket: description, comments, linked issues, and any docs, threads, or PRs it links.
2. Read the code the change touches. Facts about the codebase are yours to find, never the user's.
3. Invoke the `grill-me` skill to settle every open decision with the user.
4. Record what the grilling settles in two places:
   - Answers to requirements questions go on the ticket as comments, because the PM and the reporter read the ticket, not your files. Post them once the user approves the plan.
   - Every decision goes in the plan as a question and its answer.
5. Write the plan to a working file named `<ticket-key>-plan.md`, with these sections: Problem, Approach, Files and surfaces, Out of scope, Open questions resolved.

Then stop and wait for the user to approve it. Do not start implementing.

"Open questions resolved" is the only record of why the plan is what it is. A later attempt uses it to tell a wrong fix from a wrong design, so never skip it.
