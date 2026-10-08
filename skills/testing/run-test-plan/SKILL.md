---
name: run-test-plan
description: >
  Run a test plan against a deployed environment and record evidence for every
  step. Use when a change needs checking on staging or another environment, when
  handed a test plan to run, or when another skill needs before and after results.
---

You run the plan. The user does only what you can't, such as a login or a check on a physical device.

1. With no plan, invoke the `write-test-plan` skill first. Read the plan and do its setup. Collect every step that needs the user, ask for all of them at once, and wait for their word. Never assume an earlier session did the setup.
2. Check each precondition. Read the version the environment runs from the live deploy target, not only from config, and record it.
3. Run the steps in order. For each step, run it, capture the evidence (the command and the part of its output that proves the result), and compare the result with the expectation. Append the result to `<plan-name>-results.md` next to the plan as soon as you have it, with the phase and the version. The file is append-only across runs, so an interrupted run loses nothing.
4. The caller names the phase:
   - **Before:** compare each step with its before expectation.
   - **After:** compare each step with its after expectation.
   - Negative cases must hold in both phases.
5. When a step fails, record the symptom, the expected result, and the evidence. Skip later steps that depend on it, and run the rest.
6. Return the results file path and one line per step: pass or fail, with the before and after values when both phases ran.

Post results to a ticket or PR only when the caller asks.
