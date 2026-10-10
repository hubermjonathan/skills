---
name: babysit-pr
description: >
  Drive a pull request to mergeable: green checks, every comment answered, required
  approval in. Use when asked to babysit or watch a PR, get its checks passing, or
  get it ready to merge.
---

## Start

1. Start the watcher as a background process and leave it running:

       <this skill's directory>/scripts/pr-watch.sh <pr> [--repo <owner/name>]

   It prints one JSON line per change and never a heartbeat. Handle each line as it arrives. The first poll reports the current check results but no comments, so comment history reaches you only through step 2. Set `WATCH_INTERVAL` to change the 60 second poll.
2. Right after, handle what is already on the PR: invoke the `address-feedback` skill. Start the watcher before it so there is no gap between them.
3. If the PR conflicts with its base, merge the latest base in (`git fetch`, then `git merge origin/<base>`, usually `master` or `main`), resolve the conflicts, and push. Invoke the `push-pr` skill for the push.

## Per event

- `check_failed`: confirm it on the current head with `gh pr checks <n>` first, since the watcher can report a superseded run. Then read the failing log (`gh run view <run-id> --log-failed`). Fix it if this diff caused it. If not, say so in a PR comment and keep going.
- `check_passed`: note it.
- `review_comment`: invoke the `address-feedback` skill.
- `review_decision`: on `CHANGES_REQUESTED`, invoke the `address-feedback` skill. `APPROVED` satisfies the review requirement.
- `labeled`: `ready-for-review` means the author has shared the walkthrough and handed the PR to reviewers. Delete the walkthrough's share note: invoke the `pr-walkthrough` skill for it.
- `merge_blocked`: on `conflict`, merge the latest base in as in step 3, resolve, and push. On `behind_base`, merge the base in only if branch protection requires an up-to-date branch. Tell the user if a conflict needs their decision.
- `pr_merged` or `pr_closed`: stop.
- `watcher_died`: restart it once and say so. If it dies again, stop and report.

## Done

Tell the user the PR is ready when all of these hold:

1. no failing checks
2. every comment answered or declined, and recorded in `<pr-number>-comments.md`
3. `reviewDecision` is `APPROVED`, or the base branch requires no review (empty decision and `mergeStateStatus` not `BLOCKED`)

Then keep watching for new comments until the user says to stop. Never merge, enable auto-merge, or force-push unless the user asks.
