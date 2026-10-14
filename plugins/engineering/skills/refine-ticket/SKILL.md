---
name: refine-ticket
description: >
  Get a ticket ready to build: settled requirements, checkable acceptance criteria,
  the technical facts a builder needs, and for a bug, a reproduction. Use when handed
  a ticket to refine, or when a ticket is too vague to build from.
---

You get one ticket ready to build. A ticket is ready when someone who never saw the discussion could build and test it from the ticket alone. Stop at what the change must do and why: how to build it is the `plan-implementation` skill's job.

1. Read the whole ticket: description, comments, linked issues, and any docs, threads, or PRs it links.
2. Find the technical facts: where the behavior lives in the code, which services, data, and APIs it touches, who owns them, and any limit the code or the platform sets. Facts are yours to find, never the user's.
3. For a bug, reproduce it: locally, on a deployed environment, or in logs and traces. Record the steps, what happened, what should have happened, and the evidence, such as an error, a log line, or a request ID. If it won't reproduce, record what you tried.
4. Invoke the `grill-me` skill to settle every open requirements question with the user: what must happen, for whom, in which edge cases, and what is out of scope.
5. Draft the ticket's new description with these sections:
   - **Problem**: who is affected, and why it matters.
   - **Acceptance criteria**: each one a result someone can check, such as "a buyer who blocks a seller gets no more messages from them".
   - **Reproduction**: for a bug, from step 3.
   - **Technical notes**: the facts from step 2.
   - **Out of scope**
   - **Decisions**: each question the grilling settled, with its answer.
   - **Original description**: the reporter's text, unchanged.
6. Show the draft to the user and wait for their approval. Then replace the ticket's description with it.

**Done when:** the ticket's description has every section, each acceptance criterion is checkable, a bug has a reproduction or a record of what was tried, and no question is open.

"Decisions" is the only record of why the ticket asks for what it does. A later reader uses it to tell a wrong build from a wrong requirement, so never skip it.
