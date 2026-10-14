---
name: audit-skills
description: Measure from past session transcripts how often each skill loads when the work calls for it, then propose fixes for the ones that miss.
disable-model-invocation: true
---

# Audit skills

A skill earns its place only if it loads when the work calls for it. This audit reads past session transcripts, counts how often each expected skill loaded, and turns the misses into proposed fixes. It changes nothing until the user picks.

It needs weeks of real sessions to say anything. A rule that fired fewer than about ten times gives noise, so report its count, not a percentage.

## 1. Pick the window

Start the window on the day the skills under audit took their current form, such as the merge of the PR that last changed them or the last plugin update. Earlier sessions ran older text and blur the result.

## 2. Extract the events

Invoke the `find-transcript` skill for the list of session stores. Then run `TRANSCRIPT_DIRS=<that list> scripts/skill-audit.py extract --since <YYYY-MM-DD> --out <path>/events.tsv`, relative to this skill's directory.

Each row is one event in one session:

- `tool`: a tool call, with the first 300 characters of its arguments
- `skill`: a skill load. The detail says how: `tool` when the agent invoked it, `slash` when the user typed it, `read` when the agent read its `SKILL.md`.
- `listed`: a skill the agent was told is installed

## 3. Write the expectations

Read every skill under audit and write `expectations.json`, a list of rules of two kinds.

A **tool rule** says a tool call needs a skill loaded first:

```json
{"tool": "<shell tool name>", "match": "git commit", "expect": "git"}
```

`tool` is a regex on the tool name and `match` a regex on its arguments. Take the tool names from the `name` column of the `tool` rows in `events.tsv`, since each agent names its tools differently. The rule hits when `expect` loaded at any point earlier in the session. Write one for each action a skill's description claims, using the tool calls that action leaves behind.

A **follow rule** says one skill needs to load another:

```json
{"after": "slack", "expect": "brief"}
```

It hits when `expect` loads within `--window` events after `after`, 40 by default. Write one for each skill that a skill tells the agent to invoke.

A name without a plugin prefix matches any plugin's skill of that name: `git` matches `skills:git`. Put the prefix in `expect` to pin one plugin.

## 4. Run the check

Run `scripts/skill-audit.py check expectations.json events.tsv`. It prints how many sessions loaded each skill, then each rule's hits out of firings, with up to five misses as `session timestamp`.

- A firing in a session where the expected skill was not installed is counted apart, not as a miss.
- Sessions run from a temp directory are skipped as tests. Pass `--skip-cwd <regex>` to change the pattern, or `--skip-cwd ''` to keep them.
- The loaded list includes the agent's built-in commands, such as `clear` or `mcp`. Ignore those.

## 5. Read the misses

A rate does not say what to fix. For each rule under about 80%, find each miss's transcript by its session id in the session store, read it around the timestamp, and sort the miss into one kind:

- **Should have fired.** The work matched, and the skill would have changed the result. These are the findings.
- **Rule too broad.** The tool call matched, but the work was not what the skill is for, such as a commit inside a test fixture. Tighten the rule and rerun the check.
- **Done right without it.** The agent followed the skill's rules anyway, often because the user's instructions repeat them.

A subagent's session is its own transcript, so a skill its parent loaded does not count for it. With many misses, spawn one background subagent per rule, each with the rule, its misses, and the session store path.

## 6. Test the fixes

For each group of "should have fired" misses, pick a fix, strongest first:

- **Make the call explicit.** The calling skill names the skill as a step: "Invoke the `brief` skill for the text, capped at 1 to 3 sentences plus links." A hint, a description match, or a call with an escape clause ("unless...") loads far less often.
- **Tune the description.** Add the case the misses share to the expected skill's description, as a situation, not a phrase to match.
- **Drop the expectation.** When the misses were done right without the skill, the call or the skill can go.

Test each wording before proposing it. Copy the skills, make the edit in the copy, and run your agent non-interactively with the copy loaded, on a prompt like the misses, at least three times per wording. Count the loads from each run's output. Test the current wording the same way, so the two counts compare.

## 7. Report and wait

Show one table: each rule, its hits out of firings, its misses by kind, and the fix with its test counts. Change nothing until the user picks the fixes to apply.
