---
name: test-snapshot
description: >
  Prove an open PR works before it merges. Deploy a pre-release build of each
  service it changes to a shared staging environment, run the test plan before and
  after, put staging back on the latest release, and post the evidence on the PR.
  Use when a review-ready PR's change can be checked on staging before merge.
---

Staging is shared. Leave it the way you found it: on the latest release of the default branch.

Take the repo's commands for building a pre-release, promoting a version, and reading a service's latest release from its CLAUDE.md, AGENTS.md, or deploy docs, or from the user's instructions. If none are documented, stop and say so.

You need the PR, the services it changes, and a test plan with before and after expectations. If there is no plan, invoke the `write-test-plan` skill.

## 1. Build the pre-release

Build each service from the PR's head commit with the repo's pre-release command, one service at a time. Build only after the PR's version bump is final, because the pre-release usually takes its version from it. Before you merge the build PR it opens, read its diff. It should change only the version and what the build needs. Restore anything else it changed. Wait for the build to publish.

## 2. Wait for staging to be free

For each service, staging is free when both are true:

- It runs the service's latest release. Read the version from the live deploy target, not only from the infra repo.
- No other pre-release promotion PR for the service is open.

If staging runs another pre-release, someone else is testing. Check again every 10 minutes. Tell the user who owns it (the author of the build behind it) and since when. After 2 hours, stop and ask the user what to do.

If staging runs an older release because a release promotion PR is still open, deploy that release with the `deploy-staging` skill first, so the baseline is the latest release.

## 3. Capture the before state

Run the plan against staging with the `run-test-plan` skill, in the before phase.

## 4. Deploy the pre-release

Take its promotion PRs through the `deploy-staging` skill. Confirm the live version is the pre-release.

## 5. Capture the after state

Run the same plan in the after phase. Read the live version right before and right after the run. If anything replaced the pre-release during the run, the run doesn't count: restore staging and start over at step 2.

## 6. Restore staging

Promote the latest release back with the `deploy-staging` skill. Restore every file the pre-release changed, not only the deployed version. Confirm the live version. Delete the branches the pre-release build created.

Restore staging even when a step fails, before you report the failure.

## 7. Report

Post one comment on the PR with the `comment-pr` skill:

- a table with these columns: step, before (with its version), after (with its version), result
- links to the evidence: logs, queries, and runs
- the commit the evidence covers

If later commits change behavior, the evidence is stale. Run this skill again.

On a failure, post the failed step with its evidence instead of the table, and return it to the caller.
