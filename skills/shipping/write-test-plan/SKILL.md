---
name: write-test-plan
description: >
  Write a test plan an agent can run against a deployed environment, before and
  after a change, to prove the change works. Use when a change needs a test plan
  for staging or another environment, or a plan a later session can run.
---

Write the plan for the code as it stands now, after any review fixes, not as the plan intended it.

1. Read the ticket, the current diff, and how the change reaches its environment: which services, versions, flags, and config.
2. Make every step one an agent can do and check: a CLI call, an API request, a database query, a log search, or a metric. Use a user step only when nothing else can observe the result, such as a notification on a physical device, and say why.
3. Give each step one action and two expectations:
   - **Before:** what the environment does now, on the latest release.
   - **After:** what it does with the change deployed.

   Running the plan before and after the deploy then shows the change and nothing else.
4. Write it to `.scratch/<ticket-key>-test-plan.md` with these sections:
   - **Setup:** accounts, data, config, and ids to prepare, with exact commands and queries. List what only the user can do, such as a login, first.
   - **Preconditions:** what must be true before step 1, and how to check each one.
   - **Steps:** numbered. Each has the action, the before and after expectations, and the evidence to capture.
   - **Negative cases:** nearby behavior that must not change. Before and after must match.
   - **Cleanup:** what to undo afterwards.
5. Start with the happy path. Add edge cases only when the user asks or the ticket calls for them.
6. The plan must stand alone. A new session reading only this file must be able to run it, so include ids, table names, environments, and commands. Leave out secrets.

Reply with the file path.
