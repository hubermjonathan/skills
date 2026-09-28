---
name: create-prod-pr
description: >
  Open the OfferUp prod promotion PR in mono-repo-infra for each service a change
  touched, with `gh ou promote`. Use when the user says "create the prod pr",
  "open the prod prs", "promote to prod", or "make the prod prs".
---

## Per service

1. Find the project directory in `mono-repo-apps`: the folder holding the service's `terraform/published.json`, such as `namespaces/comms/projects/clicktocall`.
2. Get the version that actually shipped to staging from the staging promotion PR title in `mono-repo-infra` (`Promote clicktocall=1.4.1 to staging=clicktocall`). Never read it from local files, which can be ahead of what shipped.
3. Check for an existing prod PR for that service and version: `gh pr list --repo OfferUp/mono-repo-infra --search "Promote <project>=<version> to prod in:title" --state all`. A duplicate prod PR is worse than a missing one, so skip any that exist and show the url.
4. From the project directory, dry run, show the user the command, then run it for real:

       gh ou promote -e prod= -v <version> -i <TICKET-KEY> -d
       gh ou promote -e prod= -v <version> -i <TICKET-KEY>

   Drop `-i` when there is no ticket. Add `-t` (taint) only when the user asks to re-run the terraform pipeline. Run `gh ou promote --help` for anything else.
5. Take the PR url from the output. If it failed, report the last lines of output and move to the next service.

## After the PRs exist

- The terraform plan lands as a PR comment. Read it and flag anything destructive or unexpected, such as a dropped KMS key or a replaced resource.
- Prod needs env-specific values sometimes, such as a terraform variable override. Make the smallest edit on the PR's branch and push.
- If the user asks for a changelog, list what changed in each version between the prod version and the new one (inclusive) in the PR body, written with the `brief` skill as a changelog.
- You authored these PRs, so you cannot approve them, and `auto-merge-disabler` strips auto-merge on `**/prod/**`. They need a teammate's review and a direct merge. Offer the review ask: Invoke the `slack` skill.
- Offer a change ticket per service: Invoke the `create-ticket` skill.

Reply with one line per service: service, version, PR url.

Once a teammate approves a prod PR, invoke the `deploy-prod` skill on it.
