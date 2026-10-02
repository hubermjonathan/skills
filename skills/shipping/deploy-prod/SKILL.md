---
name: deploy-prod
description: >
  Take an approved prod promotion PR to prod: merge it, watch the GitHub Actions the
  merge starts, then hand off to the `monitor-prod` skill. Stops and flags the user
  on a failed check or run. Use when an approved prod promotion PR needs merging and
  deploying.
---

# Deploy to prod

The entry point is a prod promotion PR. Invoking this skill on it is the user's go-ahead to merge it. Everything after the merge is watching, and any failure stops and goes back to the user.

## 1. Frame

From the PR, get and confirm in one line:

- **Service and version**, from the title (`Promote clicktocall=1.4.4 to prod=clicktocall`).
- **The change ticket**: from the PR, or search the tracker for `deploy <service> v<version> to prod`.

## 2. Merge

Check before merging, and stop and report if any fails:

- the PR is approved (`reviewDecision` is `APPROVED`)
- every check on the current head is green (`gh pr checks <n>`)
- the plan output the checks post, such as a terraform plan comment, has nothing destructive or unexpected: no destroyed or replaced resources, no dropped keys or permissions

Then merge with a method the repo allows (`gh pr merge <n> --squash`, or `--merge` when squash is off) and record the merge commit.

## 3. Watch the Actions

The merge dispatches deploy workflows, such as a terraform apply or an ArgoCD pipeline. Find them by the merge commit:

    gh run list --repo <repo> --commit <merge-sha> --json databaseId,name,status,conclusion

They can take a few minutes to appear. Look again every minute for up to 10 minutes, and flag the user if none show up.

Watch each run with `gh run watch <id> --exit-status` as a background process. On a failure, read `gh run view <id> --log-failed`, stop, and report the cause. If the run failed after it started applying, recommend a rollback.

If the merge opens a follow-up PR, such as an ArgoCD hop, find it the way the `deploy-staging` skill finds promotion PRs. Review its diff, approve it with a submitted review, merge it, and watch its Actions the same way.

## 4. Monitor

Once every run has passed, invoke the `monitor-prod` skill with the PR, the service, the new version, and the change ticket from step 1.
