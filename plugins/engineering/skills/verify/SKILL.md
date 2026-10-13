---
name: verify
description: >
  Prove a change works before anyone reviews it: it builds, passes the checks CI
  will run, and does what its ticket and PR say, then write the evidence for the
  PR body. Use before opening or pushing to a PR, after changing code to address
  feedback, and when asked to verify, test, or prove a change.
---

# Verify

Prove the change works, and write the evidence that shows it. A claim with no proof is a finding, not a pass.

## Run it blind

Spawn a background subagent for the steps below, so the agent that wrote the change doesn't grade it. Give it the branch, the base, the ticket, and the claims to prove, and nothing of the session's reasoning. The claims are the ticket's asks, plus the PR body's `Why` and `Change` when there is a body. If your agent has no subagents, run the steps yourself and say so in the report.

The verifier never edits the change. It runs, records, and reports. Fixing is the caller's job, and the caller runs this skill again after a fix.

Verify a commit, not a working tree. If there are uncommitted changes, stop and ask the caller to commit them, since the evidence names the commit it ran on.

## 1. Builds and passes CI

Run locally every check CI will run on this diff. Find them in the repo's CI config: the workflows and commands that trigger on a PR touching these files. A repo can have its own verify skill that says exactly how.

A check that needs CI's own setup, such as its credentials or runner image, and can't run here is "couldn't run", with its error. That isn't a failure of the change.

**Done when:** every check has passed, failed, or couldn't run on the current commit, with its output recorded.

## 2. Does what it says

Prove each claim one of these ways:

- **A test that fails on the base and passes on the head.** In a temporary worktree at the base, add only the diff's test files, and run them. They fail there and pass on the head. A test that passes on both proves nothing about the claim.
- **A step of the change's test plan**, run before and after, if there is a plan.
- **A probe:** a throwaway script outside the repo that exercises the change and prints the result.

**Done when:** every claim is proven or listed as unproven.

## 3. Works deployed

When the repo can deploy a change to a shared test environment before merge, its verify skill says how and when. Run that. Otherwise skip this step and say why.

## 4. Evidence

When every check passes and every claim is proven, write the PR body's `Evidence` section in the format the `open-pr` skill sets: the commit it ran on, then the real output for each check and claim, trimmed to the lines that show the result. If the PR is open, replace its `Evidence` section with it. Otherwise return it to the caller.

## Report

One line per check and claim: passed, failed, couldn't run, or unproven. Give the output for anything that didn't pass. The caller decides what to fix.
