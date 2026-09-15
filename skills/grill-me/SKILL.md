---
name: grill-me
description: >
  Interview the user round by round to stress-test a plan, decision, or idea.
  Use when the user says "grill me", "poke holes in this", "stress-test this",
  "interview me", or invokes /grill-me. Also applies when a plan or decision needs
  its open questions surfaced before any work starts.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, no options here>

🔀 **Options**
**a)** <option> - <one line on what it means or costs>
**b)** <option> - <one line on what it means or costs>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, no options here>

🔀 **Options**
**a)** <option> - <one line on what it means or costs>
**b)** <option> - <one line on what it means or costs>

➡️ <your recommended answer>
```

Some questions are genuinely open ended, with no set of choices to pick from. Ask those without an options block rather than inventing choices to fill it.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
