---
name: comment-pr
description: >
  Read and reply to pull request comments in the right place. Use when replying to
  or addressing review comments, posting a comment on a PR, or when another skill
  needs to read a PR's feedback.
---

## Where comments live

GitHub keeps PR feedback in three places, and a review that puts everything inline has an empty body. Read all three:

    gh pr view <n> --json comments,reviews \
      -q '[.comments[], .reviews[]] | .[] | "\(.author.login) \(.state // "comment"): \(.body)"'

    gh api /repos/<owner>/<repo>/pulls/<n>/comments --paginate \
      -q '.[] | "\(.id) \(.user.login) \(.path):\(.line // .original_line): \(.body)"'

Automated reviewer bots count as reviewers. Their comments are review comments.

## Replying

- A line comment gets its reply in its own thread:
  `gh api -X POST /repos/<owner>/<repo>/pulls/<n>/comments/<comment-id>/replies -f body='...'`
- Issue-level and review-level feedback gets `gh pr comment <n> --body '...'`.
- Reply first, then push the fix. A reviewer who sees a push land before an answer assumes they were ignored.
- Say what you changed, or decline with a reason. Never leave a comment unanswered.
- A comment already answered by you is settled. Do not re-open it.
- Invoke the `brief` skill for each reply, with the commenter as the reader, capped at 1 to 2 sentences.
- Open every comment with a note naming who wrote it and for whom, then a blank line:

      > [!NOTE]
      > 🤖 **<your model's name> responding on behalf of <the user's first name>**

  Take the name from the user's instructions. Watchers use this note to tell your comments from a human's.
- Approving or requesting changes is a review, not a comment. Do neither unless asked.
- If the user asked for a draft, output the text and post nothing.
