---
name: address-feedback
description: >
  Act on a pull request's review feedback: decide what each comment needs, make
  and verify the changes, push them, and answer every comment. Use when asked to
  address or fix review feedback, and when a PR gets new review comments or
  changes requested.
---

Feedback is every unanswered comment on the PR, from people and from reviewer bots. Invoke the `comment-pr` skill to read it and for every reply. One run handles all of it, so comments that arrive together need one run.

1. Sort each comment:
   - **Change:** it asks for a change, and the change is right.
   - **Answer:** it asks a question, or the code is already right. The reply answers it, or says why the code stays.
   - **Decline:** the change would be wrong or out of scope. The reply says why.

   Ask the user before acting on a comment that asks for a different design, or that contradicts the ticket or another reviewer.
2. Make the changes: invoke the `write-code` skill. Commit each logical change on its own.
3. Invoke the `verify` skill on the new head. When it fails, fix and run it again. Its evidence replaces the PR's `Evidence` section.
4. Reply to every comment: the change with its short sha, the answer, or the reason for declining.
5. Push: invoke the `push-pr` skill.
6. Append the round to a working file named `<pr-number>-comments.md`: every comment and what it got, a change with its sha, an answer, or a decline with why.

Report one line per comment with what it got, and anything waiting on the user.
