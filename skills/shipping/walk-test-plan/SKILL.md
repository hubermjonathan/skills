---
name: walk-test-plan
description: >
  Walk the user through a test plan one step at a time, doing the steps it can
  itself and recording each result as it goes. Use when the user says "walk me
  through the test plan", "let's run the test plan", or points at a test plan file.
---

1. Read the plan. If it has a setup section, prompt the user through their part and do yours. Never assume setup was done in an earlier session. Verify every precondition before step 1.
2. Take one step at a time.
   - Agent step: do it, check the expectation, and report the result in a line.
   - User step: tell the user exactly what to do and what to look for, then ask pass, fail, or skip.
   - When the user must trigger something, say so and wait for their word before checking.
3. Append each result to `<plan-name>-results.md` next to the plan as soon as you have it, never batched at the end. An interrupted session must not lose the walkthrough. The file is append-only across attempts.
4. On a fail, stop walking. Invoke the `grill-me` skill to pin down symptom, repro, and expectation. Then write `<plan-name>-failure-<n>.md` with sections Symptom, Repro, Expected, Conclusion, Recommended next step. The next step is a code fix if the implementation is wrong, or a new plan if it solved the wrong problem. Let the user choose.
5. On a full pass, write what changed per service with the `brief` skill, for someone approving a prod change without knowing the codebase. They become the change impact text on the change tickets.

Stop and report either way. Posting the outcome to the ticket or PR happens only when the user asks.
