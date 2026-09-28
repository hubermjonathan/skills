---
name: deploy-prod
description: >
  Take an approved prod promotion PR to a verified prod deploy: merge it, watch the
  GitHub Actions the merge starts, then watch the rollout in Datadog version
  against version until the new version has soaked for 30 minutes. Stops and flags
  the user on a failure or regression, and on success closes the change ticket.
  Use when the user says "deploy this prod pr", "ship it to prod", "merge the prod
  pr and watch it", or "monitor the prod deploy".
---

# Deploy to prod

The entry point is a prod promotion PR. Invoking this skill on it is the user's go-ahead to merge it. Everything after the merge is watching, and any failure stops the run and goes back to the user.

## 1. Frame

From the PR, get and confirm in one line:

- **Service and version**, from the title (`Promote clicktocall=1.4.4 to prod=clicktocall`).
- **The Datadog service**: the `service` tag, which can differ from the project name (`comms-notifications`, not `notifications`). If unsure, group prod spans by `service` and `version` over the last hour with a filter like `service:*<name>*`, and pick the one running the old version.
- **The old version**: the one currently serving prod traffic.
- **The operation**: the service's entry operation, which the APM service page charts by default. Group the service's prod spans by `operation_name` and take the top server-side one, such as `servlet.request` for a Java web service, not a client span like `netty.client.request`.
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

Watch each run with `gh run watch <id> --exit-status` as a background process. On a failure, read `gh run view <id> --log-failed`, stop, and report the cause.

If the merge opens a follow-up PR, such as an ArgoCD hop, find it the way the `deploy-staging` skill finds promotion PRs. Review its diff, approve it with a submitted review, merge it, and watch its Actions the same way.

## 4. Wait for the rollout to start

Once the Actions pass, check APM for the new version on the service in prod every 2 minutes. When it shows traffic, the rollout has started: note the time and move on. If it has not appeared 20 minutes after the last run finished, stop and flag the user.

## 5. Check

Each check covers the last 10 minutes, split by `version`, with both versions side by side. Use the Datadog tools your agent has (an MCP server, the API, or a CLI), and load any query-syntax guidance they ship before the first query.

**APM**, from the trace metrics, which are unsampled, so counts are real:

    sum:trace.<operation>.hits{service:<service>,env:prod} by {version}.as_count()
    sum:trace.<operation>.errors{service:<service>,env:prod} by {version}.as_count()
    p95:trace.<operation>{service:<service>,env:prod} by {version}

From those, per version: traffic share (its hits over all hits), error rate (errors over hits), and p95 latency.

**Logs**, the same view the user reads in the log explorer: filter `env:prod service:<service>`, count all logs, grouped by version, in 2 minute buckets. Services log mostly problems, so total log volume is the error signal. As the rollout proceeds, one version's bars shrink and the other's grow, and the stacked total per bucket should stay level. Also split the new version's logs by `status` and by message, and list any error message the old version did not log in the same window.

Report each check as one short table, one row per version: share, error rate, p95, logs per 2 minutes. Add a line only when something changed.

## 6. Judge

Before the rollout started, record the baseline: the old version's error rate, p95, and logs per 2 minute bucket over the prior hour.

Flag a regression when the new version has at least 1,000 requests in the window and any of these hold:

- its error rate is above 1.5 times the old version's, and at least 0.1 percentage points higher
- its p95 latency is above 1.25 times the old version's, and at least 20 ms slower
- total logs per 2 minute bucket, both versions stacked, are above 1.5 times the baseline for 3 checks in a row
- its logs per request are above 1.5 times the old version's
- an error message the old version never logs appears 10 or more times
- traffic share has not moved for 15 minutes while both versions are live, so the rollout has stalled

Once the old version has no traffic left, compare against the baseline.

With fewer than 1,000 requests on the new version, report the numbers and keep watching. Too little traffic is not a pass.

## 7. Stop and flag

On a failure or regression, stop and tell the user right away:

- which step or rule failed, with both versions' numbers
- the top new error messages, if any
- links to the failing run, or to the APM service page and the log explorer filtered to the service, prod, and both versions

Recommend a rollback when a run failed after applying, or when the error rate or new-error rule tripped. The rollback and the ticket stay the user's call.

## 8. Wait between checks

Check every 5 minutes. Wait with whatever your agent offers: a scheduled wakeup, or a background `sleep 300` it waits on. Stay quiet between checks unless something changed.

## 9. Finish

The deploy succeeded when the old version has had no traffic for a full check, the new version has served all traffic for at least 30 minutes, and nothing tripped.

Then:

1. Post a short non-technical comment on the change ticket: the version deployed, the soak time, and that errors and latency held steady against the previous version.
2. Close the ticket. Read the ticket's available transitions and take the one that completes it, such as Done, Closed, or Complete. If none clearly does, ask the user which to use.
3. Tell the user in two lines: the result, and the ticket link.
