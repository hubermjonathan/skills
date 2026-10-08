---
name: slack
description: >
  Draft and send Slack messages: review asks, status updates, questions to a
  teammate, and ticket links posted into a thread. Use when asked to message a
  person, post in a channel or thread, or draft a Slack message.
---

1. Resolve every target before writing. Look up the channel id with a channel search and each person's user id with a user search. Never post to a channel name you have not resolved, and ask if a search returns more than one match.
2. For a thread, read the whole thread first, not just the linked message.
3. Invoke the `brief` skill for the text, capped at 1 to 3 sentences plus links. Then apply the Slack specifics:
   - links over prose: a review ask is the PR or ticket links and one line of ask
   - mention people with `<@user-id>`
4. Send it. Invoking this skill is the go-ahead. If the user asked only for a draft, show it with its destination (channel or DM, thread or top level) and send nothing.
5. After sending, reply with the message link.
