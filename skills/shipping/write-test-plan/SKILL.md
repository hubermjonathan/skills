---
name: write-test-plan
description: >
  Write a staging test plan for a change that another session can walk the user
  through, doing as much of it as it can alone. Use when a change needs a test plan
  for staging, or a plan a later session can run.
---

Write the plan for the code as it stands now, after any review fixes, not as the plan intended it.

1. Read the ticket, the merged or current diff, and how the change reaches its environment: which services, versions, flags, and config.
2. Mark each step as an agent step (the session can do and check it: CLI, API, database, logs, queries) or a user step (needs a device, a UI, an account login, or a permission the session lacks). Make as many as possible agent steps.
3. Write it to `.scratch/<ticket-key>-test-plan.md` with these sections:
   - **Setup**: accounts, data, config, and ids to prepare, split into what the user does and what the session does. Give exact commands and queries.
   - **Preconditions**: what must be true before step 1, and how the session verifies each one.
   - **Steps**: numbered, one action and one observable expectation each, labeled agent or user.
   - **Negative cases**: what must not happen, and how to check.
   - **Known unaffected**: nearby behavior that should not change.
   - **Cleanup**: what to undo afterward.
4. Start with the happy path. Add edge cases only when the user asks or the ticket calls for them.
5. The plan must stand alone. A new session reading only this file must be able to run it, so include ids, table names, environments, and commands. Leave out secrets.

Reply with the file path.
