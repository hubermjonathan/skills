---
name: send-blue-bubble
description: >
  Text the user, or people they name, with a blue bubble (iMessage), one to one
  or as a group text. Use when asked to text, message, or iMessage me or someone,
  such as "text me when you finish" or "text me and Jack the budget update".
---

# Send a blue bubble

Texts come from the agent's own iMessage account. People read them on a phone with no other context, and nothing reads their replies.

1. Text only the people the user names in the request or in their instructions. "Text me" means only `me`.
2. Match each person to a name in `IMESSAGE_HANDLES`. The script lists the names, never the handles:

       <this skill's directory>/scripts/send.sh --list

   If someone isn't on the list, tell the user they need adding, and send nothing.
3. Invoke the `brief` skill for the text, with a recipient reading on a phone as the reader, capped at a few lines: what happened, the one link or ID they need, and what you need from them, if anything.
4. Send it with a quoted heredoc, so the shell expands nothing inside the message. Name every recipient:

       <this skill's directory>/scripts/send.sh me jack <<'MSG'
       Budget update: Q3 spend is 4% under plan. Details: https://example.com/budget
       MSG

   One name sends a one-to-one text. Two or more send one group text, to the group chat that has exactly those people. It prints `sent`. On failure it prints the reason to stderr and exits nonzero.

   Messages can't start a group from a script. If no group chat has exactly those people, the script exits 3 and sends nothing. Ask the user to start the group once from their phone, with the agent's account and those people, then send again.
5. If the send fails, tell the user why in the session. Don't retry in a loop.

## Setup

- macOS, with Messages signed in to the agent's own Apple ID.
- `IMESSAGE_HANDLES` in the shell environment, kept with the user's secrets and never in a repo: space-separated `name=handle` pairs, where `me` is the user and each handle is a phone number in E.164 form or an Apple ID email.

      export IMESSAGE_HANDLES='me=+11234567890 jack=+10987654321'

- Automation permission for Messages. macOS asks once, on the first send. Change it later in System Settings > Privacy & Security > Automation.
