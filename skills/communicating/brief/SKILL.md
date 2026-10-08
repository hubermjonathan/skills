---
name: brief
description: >
  Turn an investigation, the session so far, or a block of text into a short, plain,
  non-technical version for a person to read in Slack, Jira, or a PR. Use when asked
  for a short, concise, or non-technical version of something, a summary for a
  person or channel, or text under a length limit, and when another skill needs text
  written for someone outside the work.
---

# Brief

Say it the way one person tells another: the point, in plain words, as short as the reader can act on.

## Inputs

Work these out from the request. Ask only when the source is unclear.

- **Source.** What to translate. Default: the work so far in this session. It can also be the last reply, a pasted block, or a file.
- **Reader.** Who reads it. Default: a teammate who was not part of the work and may not be an engineer, such as a PM or an analyst. A named person or channel sets the reader.
- **Destination.** Where it goes, which sets the length default below.
- **Cap.** A limit the user gives ("under 10 words", "one sentence") is hard. Count.

| Destination | Default length |
|---|---|
| Slack message | 1 to 3 sentences, plus links |
| Jira comment | 2 to 4 sentences |
| Jira description | 1 to 2 sentences |
| PR comment | 1 to 2 sentences |
| Changelog | one line per change |
| Chat, no destination | as short as the question allows |

## Steps

1. **Find the point.** The one thing the reader needs: the result, the decision, the ask, or the state of things. It goes first.
2. **Keep what changes what the reader does or understands.** Cut how the answer was found: the steps, the tools, the queries, the files read, the dead ends. Keep the numbers, names, dates, ids, and links the reader acts on.
3. **Say the effect, not the mechanism.** "The notifications service was looking up the full user profile on every badge count" becomes "each notification was fetching data it rarely needs". A technical term stays only when the reader uses it too. Otherwise, say what it means for them.
4. **Write it.** Plain spoken sentences, periods over commas, one idea per sentence. Give each thing one name. Say confidence once, where it matters ("confirmed", "likely"), not as stacked hedges.
5. **Cut again.** Delete any sentence the reader would not miss. Then check the other way: if the reader would have to ask a follow-up before acting, add the answer.

## Output

Only the text, ready to paste. No preamble, no "Here's a summary", no headers, no sign-off, and no alternatives unless asked. Use a list only for items that are truly separate, such as steps or a set of links.

If the user said to send or post it, invoke the `slack` skill for Slack or the `comment-pr` skill for a PR. Post to Jira with the tracker tools.
