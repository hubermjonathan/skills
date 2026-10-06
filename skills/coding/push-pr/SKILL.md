---
name: push-pr
description: >
  Push new commits to an open pull request and keep the PR honest: base up to date,
  version bump still right, title and body still true. Use when pushing to a branch
  that has an open PR, updating a PR, or getting a PR ready to merge again after new
  commits or a base change.
---

## Before pushing

1. Find the PR and its head: `gh pr view --json number,headRefName,baseRefName,isDraft,reviewDecision,title,body`. Push to that head branch, which may not be your local branch name, such as a promotion PR's branch in an infra repo.
2. Update from the base when it conflicts or the repo requires an up-to-date branch: `git fetch`, then `git merge origin/<base>`. Merge rather than rebase, so no force-push is needed on a reviewed PR. Rebase only when the user asks. Resolve conflicts by keeping both sides' intent, and never abort.
3. Recheck the version bump. If the base has moved past the branch's version, or a conflict landed in a version file, re-bump once relative to the new base. Invoke the `open-pr` skill for the bump rules.
4. If this push answers review comments, reply to them first. Invoke the `comment-pr` skill.
5. Remove debug output and stray files the new commits added. For comments and docs, invoke the `kill-comments` skill.
6. Run the narrowest build, lint, and tests that cover what changed since the last push.
7. Check what will ship, not the working tree: `git diff --cached` before committing, and `git diff origin/<head>...HEAD` before pushing. A stray unstaged edit means the commit does not hold what you just checked.

## Pushing

- Add commits once anyone has reviewed. Rewrite history only when the user asks.
- After a rebase the user asked for, push with `git push --force-with-lease`, never `--force`.
- If the PR was approved, tell the user a new push may dismiss the approval.

## After pushing

1. Reread the title and body against the full diff, `git diff origin/<base>...HEAD`. Fix anything no longer true without asking: a reverted fix still claimed, a new change not mentioned, a scope that grew or shrank, a stale version in a bullet. Keep the format from the "open-pr" skill. Apply with `gh pr edit <n> --title ... --body-file ...`.
2. If the user said the PR is ready and it is a draft, run `gh pr ready <n>`.
3. Check CI on the new head with `gh pr checks <n>`. A red right after a push or a base move is not real until the per-check query confirms it on the current head.
4. Report in one or two lines: what was pushed, what changed in the title or body, and check status. If the user wants it driven to mergeable, invoke the `babysit-pr` skill.
