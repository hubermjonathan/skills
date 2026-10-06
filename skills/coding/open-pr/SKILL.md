---
name: open-pr
description: >
  Open a pull request with a short title and a body in a fixed format. Use when
  asked to open a PR or put a change up for review, after finishing a change that
  needs review, or when another skill needs the PR title and body format.
---

Invoke the `company-conventions` skill first, if one is installed, for the company's pull request conventions, such as version bumps. Those conventions and the user's instructions win over the defaults below.

1. Bump versions (see below), then commit and push. Invoke the `git` skill before committing.
2. Remove debug output and stray files from the diff. For comments and docs, invoke the `kill-comments` skill.
3. Write the title and body in the format below.
4. Open as a draft (`gh pr create --draft`) unless the user says it is ready.
5. Reply with the PR url.

## Title

`<scope>: <description>`, 50 characters at most. The scope is the service or project touched. Append the ticket key as `(ABC-123)`, which does not count toward the limit. Omit it if there is no ticket.

## Body

Sections in this order:

    ## Context
    The problem, what was tried before if relevant, and what this change does about it,
    written with the `brief` skill for a PM, 1 to 4 sentences.

    ## Why
    The technical reason, short. Evidence when it helps: numbers, error text, a linked
    incident. Link related PRs as `<org>/<repo>#<n>` or `#<n>`.

    ## What
    - One bullet per change, grouped by area of impact, not by file
    - Identifiers in backticks
    - A version bump is one bullet here: "Bump <service> to <version>"

    ## Follow up
    - Only when something must happen after merge, such as an apply or a config change
      in another repo

Rules:

- `Context` is required when the change touches behavior a non-engineer cares about. Skip it for docs-only or purely internal changes.
- `Follow up` is optional. Leave it out rather than writing "none".
- Keep it short. Most bodies fit on one screen. A table or code block goes in only when prose cannot say it as well.
- No testing section, no versions section, no checklist, no restating the diff line by line.
- Every claim must be true of the code as pushed: what it fixes, what it leaves alone, whether CI is green.
- No ticket link in the body when the title already carries the key.
- If the repo has a PR template, fill it in instead, just as tersely.

## Version bumps

Bump once per PR, measured against the base branch. If the branch already carries a bump, keep it and never bump again: `1.1.3` becomes `1.2.0` in one PR, never `1.2.1`. Use a minor bump for features and a patch bump for fixes, unless the repo says otherwise.

Take the repo's versioning rules from the company conventions, the repo's CLAUDE.md, AGENTS.md, or contributing guide, or the user's instructions. If none document versioning, bump nothing.
