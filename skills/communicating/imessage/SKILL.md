---
name: imessage
description: >
  Text the user with a blue bubble: an iMessage from a Mac. Use when the user asks
  to be texted.
---

# iMessage

A text is one-way. The user reads it on a phone with no other context and can't reply through it.

1. Text only when the user or their instructions asked for it. They decide when and how often.
2. Write a message that stands alone: what happened, the one link or id they need, and what you need from them, if anything. Keep it to a few lines.
3. Send it with a quoted heredoc, so the shell expands nothing inside the message:

       <this skill's directory>/scripts/send.sh <<'MSG'
       Build on fix-retry failed: 2 tests in RetryPolicyTest. https://github.com/org/repo/actions/runs/123
       MSG

   It prints `sent`. On failure it prints the reason to stderr and exits nonzero.
4. If the send fails, tell the user why in the session. Don't retry in a loop.

## Setup

- macOS, with Messages signed in to iMessage.
- `IMESSAGE_HANDLE` set in the shell environment: the user's phone number in E.164 form (`+11234567890`) or their Apple ID email.
- Automation permission for Messages. macOS asks once, on the first send. Change it later in System Settings > Privacy & Security > Automation.
