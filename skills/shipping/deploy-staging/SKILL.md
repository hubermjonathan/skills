---
name: deploy-staging
description: >
  Get a merged change onto staging through CI-generated promotion PRs in an infra
  repo. Use when the user says "deploy to staging", "watch the staging deploy",
  "watch for the follow-up prs", or "monitor until it hits staging".
---

Merging a code PR makes CI open a promotion PR per service in the infra repo. That can take 15 minutes. Some chains have a second hop: a terraform promotion PR whose merge opens an ArgoCD or EC2 follow-up. Take the repo names, bot accounts, and deploy tooling from the user's instructions or the repo's CLAUDE.md.

## Find the promotion PRs

Walk GitHub cross-references out from the code PR, then out from each merged promotion PR, until nothing new appears:

    gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){timelineItems(itemTypes:[CROSS_REFERENCED_EVENT],first:50){nodes{... on CrossReferencedEvent{source{... on PullRequest{number url title state repository{nameWithOwner}}}}}}}}}' -F o=<owner> -F r=<repo> -F n=<pr>

If nothing has appeared yet, wait and look again. Never guess the chain shape.

## Per promotion PR

1. Read the diff. It is usually a generated version bump.
2. Decide whether it needs an env-specific change, such as a staging terraform variable override. Most do not. If one does, check out the PR branch in an infra worktree, make the smallest edit, and push to that branch.
3. Watch it under the Monitor tool with `../../coding/babysit-pr/scripts/pr-watch.sh <pr> --repo <infra-repo>`, relative to this skill's directory.
4. Read the plan output the PR's checks post (for example a terraform plan comment). Flag anything destructive or unexpected to the user before approval.
5. Approval must be a submitted review (`gh pr review <n> --approve`), not a comment. Bot-authored promotion PRs are often excluded from auto-approvers, and a comment never satisfies branch protection. Approve and merge only when the user said to do it on their behalf.
6. After a merge, look for the next hop again.

## Done

Staging is done when every service has at least one promotion PR and none are unmerged. Then watch the rollout (the deploy workflow run, or the ArgoCD version) and report success or failure with the cause. For a failed run, read `gh run view <run-id> --log-failed`.

If a watcher exits, restart it once and say so. Never wait quietly on a watcher that has stopped.
