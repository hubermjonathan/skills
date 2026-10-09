---
name: push-pr
description: >
  Push new commits to an open pull request and keep the PR honest: base up to date,
  title and body still true. Use when pushing to a branch that has an open PR, or
  when a PR's title or body needs to catch up with new commits or a base change.
---

## Before pushing

1. Find the PR and its head: `gh pr view --json number,headRefName,baseRefName,isDraft,reviewDecision,title,body`. Push to that head branch, which may not be your local branch name.
2. Update from the base when it conflicts or the repo requires an up-to-date branch: `git fetch`, then `git merge origin/<base>`. Merge rather than rebase, so no force-push is needed on a reviewed PR. Rebase only when the user asks. Resolve conflicts by keeping both sides' intent, and never abort.
3. If this push answers review comments, reply to them first. Invoke the `comment-pr` skill.
4. Remove debug output and stray files the new commits added. For comments and docs, invoke the `kill-comments` skill.
5. Run the narrowest build, lint, and tests that cover what changed since the last push.
6. Check what will ship, not the working tree: `git diff --cached` before committing, and `git diff origin/<head>...HEAD` before pushing. A stray unstaged edit means the commit does not hold what you just checked.

## Pushing

- Add commits once anyone has reviewed. Rewrite history only when the user asks.
- After a rebase the user asked for, push with `git push --force-with-lease`, never `--force`.
- If the PR was approved, tell the user a new push may dismiss the approval.

## After pushing

1. Reread the title and body against the full diff, `git diff origin/<base>...HEAD`. Fix anything no longer true without asking: a reverted fix still claimed, a new change not mentioned, a scope that grew or shrank, a stale version in a bullet. Keep the format from the "open-pr" skill, including the note at the top. If the body has no note, add it. Keep the walkthrough block above the note, between its `<!-- pr-walkthrough -->` markers, as it is. Apply with `gh pr edit <n> --title ... --body-file ...`.
2. Mark what the push made stale. Never edit evidence or the walkthrough yourself: only the run that made them replaces them. When the new head is past the commit that `Evidence` ran on, put this right under the `## Evidence` heading, replacing any earlier one:

       > [!WARNING]
       > Ran on `<sha>`. <n> commits landed since.

   Do the same for the walkthrough block: inside its markers, after a blank line, with "Built on" in place of "Ran on". Apply with `gh pr edit <n> --body-file ...`.
3. If the PR is a draft, run `gh pr ready <n>`.
4. Check CI on the new head with `gh pr checks <n>`. A red right after a push or a base move is not real until the per-check query confirms it on the current head.
5. Report in one or two lines: what was pushed, what changed in the title or body, what's marked stale, and check status.
