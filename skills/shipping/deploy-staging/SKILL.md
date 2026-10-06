---
name: deploy-staging
description: >
  Take a build's promotion PRs in an infra repo to merged and rolled out on staging,
  approving and merging each one once it's ready. Use when a merged change or a
  pre-release build needs to reach staging, or when asked to watch or finish a
  staging deploy.
---

A promotion PR moves one service's version into staging. CI opens most of them after a build merges, and some merges open a follow-up PR, such as a terraform apply that opens a PR with its outputs. Take the infra repo, bot accounts, team, and deploy commands from the user's instructions or the repo's CLAUDE.md or AGENTS.md.

Running this skill is the go-ahead to merge every promotion PR that passes the checks below. Never merge one that fails them.

## Find the promotion PRs

Start from the PR whose merge produced the build: the code PR for a release, or the build PR for a pre-release. Walk GitHub cross-references out from it, then out from each merged promotion PR, until nothing new appears:

    gh api graphql -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){timelineItems(itemTypes:[CROSS_REFERENCED_EVENT],first:50){nodes{... on CrossReferencedEvent{source{... on PullRequest{number url title state repository{nameWithOwner}}}}}}}}}' -F o=<owner> -F r=<repo> -F n=<pr>

CI can take 15 minutes to open a PR. If nothing has appeared, wait and look again. Never guess the chain shape. If the repo's docs say CI skips a hop, as some chains do for pre-release versions, open that PR yourself with the repo's promotion command.

Watch each promotion PR by running `../../coding/babysit-pr/scripts/pr-watch.sh <pr> --repo <infra-repo>` (relative to this skill's directory) as a background process, and handle each line it prints. If a watcher exits, restart it once and say so. Never wait quietly on a watcher that has stopped.

## Check that it's ready

A promotion PR is ready to merge when all of these are true:

1. Its checks pass.
2. The plan output on the PR shows only what this change should change. A terraform plan has no unexpected destroy or replace. An ArgoCD diff is limited to the version and the config this change needs. Stop and show the user anything else.
3. Staging has what the change needs to run. Read the original code PR's deploy config, such as its `terraform/` and `helm/` directories, and look for:
   - a new required config key. With no staging value, the app fails on start.
   - a value that must differ between staging and prod.
   - infra the deploy doesn't create, such as a secret or a manual setup step.

   Add a missing config value to the staging values in the infra repo, on the PR where the repo's docs say it goes, and tell the user what you added. For missing infra, stop and tell the user what's needed.
4. No environment lockdown or freeze is blocking merges. If one is, stop and tell the user.

## Approve and merge

Who approves depends on who opened the PR:

- **CI or a bot opened it:** approve it with a submitted review (`gh pr review <n> --approve`), then merge it. A comment never counts as an approval.
- **You opened it, in a path your team owns:** the repo's auto-approver approves it. CODEOWNERS shows who owns the path, and the user's instructions name their team. Merge it once it's approved. If no approval arrives within 10 minutes, tell the user.
- **You opened it, in a path another team owns:** request a review from that path's owners (`gh pr edit <n> --add-reviewer <owner>`), and tell the user who you asked. Merge it once it's approved.

After each merge, look for the next hop and take it through the same checks.

## Done

Staging is done when every service runs the target version. Read the version from the live deploy target, such as the running instances or the ArgoCD app. A failed deploy can roll back while the infra repo still shows the new version. For a failed run, read `gh run view <run-id> --log-failed` and report the cause.
