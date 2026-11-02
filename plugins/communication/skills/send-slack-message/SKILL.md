---
name: send-slack-message
description: >
  Draft and send Slack messages: review asks, status updates, questions to a
  teammate, and ticket links posted into a thread. Use when asked to message a
  person, post in a channel or thread, or draft a Slack message.
---

1. Resolve every target before writing. Look up the channel id with a channel search and each person's user id with a user search. Never post to a channel name you have not resolved, and ask if a search returns more than one match.
2. For a thread, read the whole thread first, not just the linked message.
3. Write the text. When the user or the calling skill gives the exact text, use it word for word. A review ask or a change ticket ask is one line per PR or ticket: a few words on what it does, then its link. Add nothing else: no greeting, no reasoning, and no status such as checks, walkthroughs, or test results. For any other message, invoke the `brief` skill for it, capped at 1 to 3 sentences plus links. Mention people with `<@user-id>` and user groups with `<!subteam^group-id>`.
4. Send it. Invoking this skill is the go-ahead. If the user asked only for a draft, show it with its destination (channel or DM, thread or top level) and send nothing.
5. After sending, reply with the message link.
