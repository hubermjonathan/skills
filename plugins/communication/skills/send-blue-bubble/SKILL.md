---
name: send-blue-bubble
description: >
  Text the user, or people or group chats they name, with a blue bubble
  (iMessage), optionally with images or other files. Use when asked to text or
  iMessage me, someone, or a group, such as "text me when you finish", "text me
  and Jac the budget update", "text the budget updates group", or "text me the
  screenshots".
---

# Send a blue bubble

Texts come from the agent's own iMessage account. People read them on a phone with no other context, and nothing reads their replies.

1. Text only the people and group chats the user names in the request or in their instructions. "Text me" means only `me`.
2. Pick how the text goes out from the user's words:
   - **One person, or several together**, such as "text me and Jac": one run, naming each person. Several names send one group text.
   - **Several people separately**, such as "text me and Jac separately", "text each of them", or a workflow that texts one person and then another: one run per person.
   - **A group chat by its name**, such as "text the budget updates group": one run with `--group`.
3. Match the user's words to the script's names. `--list` prints the people's names and `--groups` prints the group chats' names, never handles:

       <this skill's directory>/scripts/send.sh --list
       <this skill's directory>/scripts/send.sh --groups

   If a person or group isn't listed, tell the user, and send nothing. A person needs adding to `IMESSAGE_HANDLES`. A group needs starting and naming from a phone.
4. Invoke the `brief` skill for the text, with a recipient reading on a phone as the reader, capped at a few lines: what happened, the one link or ID they need, and what you need from them, if anything.
5. Send it with a quoted heredoc, so the shell expands nothing inside the message:

       <this skill's directory>/scripts/send.sh me jac <<'MSG'
       Budget update: Q3 spend is 4% under plan. Details: https://example.com/budget
       MSG

       <this skill's directory>/scripts/send.sh --group "Budget updates" <<'MSG'
       Budget update: Q3 spend is 4% under plan. Details: https://example.com/budget
       MSG

   To send images or other files, such as screenshots the user asked for, put one `--attach <file>` before the recipients for each file. The text goes first as their caption, then each file in order:

       <this skill's directory>/scripts/send.sh --attach floor.png --attach run.png me <<'MSG'
       The Floor, then the Run screen.
       MSG

   It prints `sent` once the text and every file have gone out. On failure it prints the reason to stderr, with the fix when the user has to make one, and exits nonzero.
6. If the send fails, tell the user the script's reason in the session. When it names a fix for the user, send again once they've made it.

## Setup

- macOS, with Messages signed in to the agent's own Apple ID.
- `IMESSAGE_HANDLES` in the shell environment, kept with the user's secrets and never in a repo: space-separated `name=handle` pairs, where `me` is the user and each handle is a phone number in E.164 form or an Apple ID email.

      export IMESSAGE_HANDLES='me=+11234567890 jac=+10987654321'

- Automation permission for Messages. macOS asks once, on the first send. Change it later in System Settings > Privacy & Security > Automation.
