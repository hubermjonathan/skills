---
name: slack
description: >
  Draft and send Slack messages: review asks, status updates, questions to a
  teammate, and ticket links posted into a thread. Use when the user says "send on
  slack", "message <person>", "post in <channel>", or "draft a slack message".
---

1. Resolve every target before writing. Look up the channel id with a channel search and each person's user id with a user search. Never post to a channel name you have not resolved, and ask if a search returns more than one match.
2. For a thread, read the whole thread first, not just the linked message.
3. Write it short:
   - links over prose: a review ask is the PR or ticket links and one line of ask
   - non-technical unless every reader is an engineer on the work
   - mention people with `<@user-id>`
   - no headers, no bullet walls, no sign-off
4. Show the draft with its destination (channel or DM, thread or top level). Send only after the user confirms, unless they already said to send it.
5. After sending, reply with the message link.

Editing a sent message counts as sending: show the new text first.
