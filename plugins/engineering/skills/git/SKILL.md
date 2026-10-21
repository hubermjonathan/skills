---
name: git
description: >
  Branch, worktree, commit, and cleanup conventions. Use when making a branch or
  worktree, committing, pushing, merging a PR or learning that one merged, or cleaning
  up local branches and worktrees.
---

The user's instructions on naming win over everything below. These are the defaults.

## Names

- Worktree: `<1-5-word-kebab-task-desc>`.
- Branch: `jon/<1-5-word-kebab-task-desc>`, or `jon/<worktree-name>` inside a worktree.
- Commit: `<scope>: <description>`, with a subject line of 50 characters at most. The scope is the service, project, or area touched. No body unless the user asks.

## Branches and worktrees

- Never commit on the default branch. Branch first.
- Base new work on a fresh default branch: `git fetch` first and branch from `origin/<default>`, not a stale local copy.
- Create the branch with `--no-track`, as in `git switch -c <branch> --no-track origin/<default>`, and set its upstream on the first push with `git push -u origin <branch>`.

## Commits

- One logical change per commit.
- Check `git status` and stage explicit paths. Never commit working files, local settings, or build output.
- If a pre-commit hook fails, such as a secret scanner, fix the cause. Never pass `--no-verify`.
- Push only when the user asks or the calling skill needs it.
- Once a PR is open, add commits instead of rewriting history, and bring in the base with `git fetch` and `git merge origin/<base>` rather than a rebase. Rebase only when the user asks, then push with `--force-with-lease`, never `--force`.

## Cleanup

1. `git fetch --prune`.
2. List worktrees and local branches. Mark for removal: branches merged or gone upstream, and worktrees whose branch is merged.
3. Anything with uncommitted changes or unpushed commits is listed, not removed.
4. Show the list and remove after the user confirms, or directly if they said to clean up everything: `git worktree remove`, then `git branch -D`.

## After a PR merges

Clean up a PR's branch as soon as you merge the PR or learn that the user merged it. The merge is the user's approval, so go ahead without asking.

1. `git fetch --prune`. If the remote branch is still there, delete it with `git push origin --delete <branch>`.
2. Remove the PR's worktree and local branch as in step 4 of Cleanup. Step 3 still applies.
