---
name: monitor-prod
description: >
  Watch a prod rollout in Datadog, version against version, until the new version
  has soaked for 30 minutes. Stops and flags the user on a regression, and on
  success closes the change ticket. Use when the user says "monitor the prod
  deploy", "watch the rollout", or "keep an eye on prod", or after the
  `deploy-prod` skill finishes its merge.
---

# Monitor a prod rollout

Compare the new version against the old one on the signals the user reads in Datadog: requests, errors, and latency by version on the APM service page, and logs by version in the log explorer. Keep checking until the rollout finishes and the new version has soaked. Stop early on a regression.

## 1. Frame

Start from whatever the user or the calling skill hands over: a prod PR, a change ticket, or a service and version. Work out the rest, and confirm it in one line before the first check:

- **The Datadog service**: the `service` tag, which can differ from the project name (`comms-notifications`, not `notifications`). If unsure, group prod spans by `service` and `version` over the last hour with a filter like `service:*<name>*`.
- **The new version**: from the PR title (`Promote clicktocall=1.4.4 to prod=clicktocall`), the ticket title, or the user.
- **The old version**: the one serving prod traffic before the new one.
- **The operation**: the service's entry operation, which the APM service page charts by default. Group the service's prod spans by `operation_name` and take the top server-side one, such as `servlet.request` for a Java web service, not a client span like `netty.client.request`.
- **The change ticket**: from the caller, or search the tracker for `deploy <service> v<version> to prod`.

Use the Datadog tools your agent has (an MCP server, the API, or a CLI), and load any query-syntax guidance they ship before the first query.

## 2. Wait for the rollout to start

Check APM for the new version on the service in prod every 2 minutes. When it shows traffic, the rollout has started: note the time and record the baseline (step 4). If it is already live, find the time it first took traffic and start checking now. If it has not appeared after 20 minutes, stop and flag the user.

## 3. Check

Each check covers the last 10 minutes, split by `version`, with both versions side by side. Use the Datadog tools your agent has (an MCP server, the API, or a CLI), and load any query-syntax guidance they ship before the first query.

**APM**, from the trace metrics, which are unsampled, so counts are real:

    sum:trace.<operation>.hits{service:<service>,env:prod} by {version}.as_count()
    sum:trace.<operation>.errors{service:<service>,env:prod} by {version}.as_count()
    p95:trace.<operation>{service:<service>,env:prod} by {version}

From those, per version: traffic share (its hits over all hits), error rate (errors over hits), and p95 latency.

**Logs**, the same view the user reads in the log explorer: filter `env:prod service:<service>`, count all logs, grouped by version, in 2 minute buckets. Services log mostly problems, so total log volume is the error signal. As the rollout proceeds, one version's bars shrink and the other's grow, and the stacked total per bucket should stay level. Also split the new version's logs by `status` and by message, and list any error message the old version did not log in the same window.

Report each check as one short table, one row per version: share, error rate, p95, logs per 2 minutes. Add a line only when something changed.

## 4. Judge

Record the baseline from the hour before the new version first took traffic: the old version's error rate, p95, and logs per 2 minute bucket.

Flag a regression when the new version has at least 1,000 requests in the window and any of these hold:

- its error rate is above 1.5 times the old version's, and at least 0.1 percentage points higher
- its p95 latency is above 1.25 times the old version's, and at least 20 ms slower
- total logs per 2 minute bucket, both versions stacked, are above 1.5 times the baseline for 3 checks in a row
- its logs per request are above 1.5 times the old version's
- an error message the old version never logs appears 10 or more times
- traffic share has not moved for 15 minutes while both versions are live, so the rollout has stalled

Once the old version has no traffic left, compare against the baseline.

With fewer than 1,000 requests on the new version, report the numbers and keep watching. Too little traffic is not a pass.

## 5. Stop and flag

On a failure or regression, stop and tell the user right away:

- which rule tripped, with both versions' numbers
- the top new error messages, if any
- links to the APM service page and the log explorer filtered to the service, prod, and both versions

Recommend a rollback when the error rate or new-error rule tripped. The rollback and the ticket stay the user's call.

## 6. Wait between checks

Check every 5 minutes. Wait with whatever your agent offers: a scheduled wakeup, or a background `sleep 300` it waits on. Stay quiet between checks unless something changed.

## 7. Finish

The deploy succeeded when the old version has had no traffic for a full check, the new version has served all traffic for at least 30 minutes, and nothing tripped.

Then:

1. Post a short non-technical comment on the change ticket: the version deployed, the soak time, and that errors and latency held steady against the previous version.
2. Close the ticket. Read the ticket's available transitions and take the one that completes it, such as Done, Closed, or Complete. If none clearly does, ask the user which to use.
3. Tell the user in two lines: the result, and the ticket link.
