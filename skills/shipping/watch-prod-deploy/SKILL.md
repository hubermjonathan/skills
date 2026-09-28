---
name: watch-prod-deploy
description: >
  Watch a prod rollout in Datadog, version against version, until the new version
  has soaked for 30 minutes. Stops and flags the user on a regression, and on
  success closes the change ticket. Use when the user says "watch the prod
  deploy", "monitor the rollout", or "keep an eye on prod" after a prod deploy.
---

# Watch a prod deploy

Compare the new version against the old one on the same signals the user reads in Datadog: requests, errors, and latency by version on the APM service page, and error logs by version in the log explorer. Keep checking until the rollout finishes and the new version has soaked. Stop early on a regression.

## 1. Frame

Get these from the user or the deploy PR, and confirm them in one line before the first check:

- **Service**: the Datadog `service` tag, such as `comms-notifications`. If unsure, group prod spans by `service` and `version` over the last hour with a filter like `service:*<name>*`, and pick the service whose versions include the new one.
- **Versions**: the new version, and the old one currently in prod.
- **Operation**: the service's entry operation, which the APM service page charts by default. Group the service's prod spans by `operation_name` and take the top server-side one: `servlet.request` for a Java web service, not a client span such as `netty.client.request` or `okhttp.request`.
- **Change ticket**: the ticket to close on success. If the user gave none, search the tracker for a ticket titled `deploy <service> v<version> to prod`, and confirm it with the user.

Use the Datadog tools your agent has (an MCP server, the API, or a CLI). Load any query-syntax guidance they ship before the first query.

## 2. Check

Each check covers the last 10 minutes, split by `version`, both versions side by side.

**APM**, from the trace metrics (unsampled, so counts are real):

    sum:trace.<operation>.hits{service:<service>,env:prod} by {version}.as_count()
    sum:trace.<operation>.errors{service:<service>,env:prod} by {version}.as_count()
    p95:trace.<operation>{service:<service>,env:prod} by {version}

From those, per version: traffic share (its hits over all hits), error rate (errors over hits), and p95 latency.

**Logs**, with the filter `service:<service> env:prod`: count all logs and error logs (`status:error`) per version, and error logs per version per minute for the trend. Error log rate is error logs over all logs for that version. Raw error counts rise as the new version takes more traffic, so compare rates, not counts.

**New errors**: group the new version's error logs by message and list any that the old version did not log in the same window.

Report each check as one short table, one row per version: share, error rate, p95, error log rate. Add a line only when something changed.

## 3. Judge

Flag a regression when the new version has at least 1,000 requests in the window and any of these hold:

- error rate above 1.5 times the old version's, and at least 0.1 percentage points higher
- p95 latency above 1.25 times the old version's, and at least 20 ms slower
- error log rate above 1.5 times the old version's
- an error message the old version never logs, at 10 or more occurrences
- the error log trend for the new version rising for 3 checks in a row
- traffic share not moving for 15 minutes while both versions are live, which means the rollout has stalled

Once the old version has no traffic left, compare against the old version's rates from the hour before the rollout started.

With less than 1,000 requests on the new version, report the numbers and keep watching. Too little traffic is not a pass.

## 4. Stop and flag

On a regression, stop watching and tell the user right away:

- which rule tripped, with both versions' numbers
- the top new error messages, if any
- links to the APM service page and the log explorer, filtered to the service, prod, and both versions

Recommend a rollback when the error rate or new-error rule tripped. Leave the rollback decision and the ticket to the user.

## 5. Wait

Check every 5 minutes. Wait with whatever your agent offers: a scheduled wakeup, or a background `sleep 300` it waits on. Stay quiet between checks unless something changed.

## 6. Finish

The rollout succeeded when the old version has had no traffic for a full check, the new version has served all traffic for at least 30 minutes, and no rule tripped.

Then:

1. Post a short non-technical comment on the change ticket: the version deployed, the soak time, and that errors and latency held steady against the previous version.
2. Close the ticket. Read the ticket's available transitions and take the one that completes it, such as Done, Closed, or Complete. If none clearly does, ask the user which to use.
3. Tell the user in two lines: the result, and the ticket link.
