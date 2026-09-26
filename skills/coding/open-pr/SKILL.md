---
name: open-pr
description: >
  Open a pull request with a short title and a body in a fixed format. Use when the
  user says "open a pr", "make a pr", "create a pr", "put this up for review", after
  finishing a change that needs review, or when another skill needs the PR title and
  body format.
---

The user's instructions on titles and bodies win over the defaults below.

1. Bump versions (see below), then commit and push. Invoke the `git` skill before committing.
2. Remove debug output and stray files from the diff. For comments and docs, invoke the `kill-comments` skill.
3. Write the title and body in the format below.
4. Open as a draft (`gh pr create --draft`) unless the user says it is ready.
5. Reply with the PR url.

## Title

`<scope>: <description>`, lowercase, 50 characters at most. The scope is the service or project touched. Append the ticket key as `(ABC-123)`, which does not count toward the limit. Omit it if there is no ticket.

## Body

All lowercase prose, `##` headers in lowercase, sections in this order:

    ## context
    1 to 4 non-technical sentences: the problem in plain words, what was tried before if
    relevant, and what this change does about it. readable by a pm.

    ## why
    the technical reason, short. evidence when it helps: numbers, error text, a linked
    incident. link related prs as `OfferUp/<repo>#<n>` or `#<n>`.

    ## what
    - one bullet per change, grouped by area of impact, not by file
    - identifiers in backticks
    - a version bump is one bullet here: "bump <service> to <version>"

    ## follow up
    - only when something must happen after merge, such as an apply or a config change
      in another repo

Rules:

- `context` is required when the change touches behavior a non-engineer cares about. Skip it for docs-only or purely internal changes.
- `follow up` is optional. Leave it out rather than writing "none".
- Keep it short. Most bodies fit on one screen. A table or code block goes in only when prose cannot say it as well.
- No testing section, no versions section, no checklist, no restating the diff line by line.
- Every claim must be true of the code as pushed: what it fixes, what it leaves alone, whether CI is green.
- No ticket link in the body when the title already carries the key.
- If the repo has a PR template, fill it in instead, just as tersely.
- Do not label the PR as AI-generated unless the user wants that.

## Version bumps

Bump once per PR, measured against the base branch. If the branch already carries a bump, keep it and never bump again: `1.1.3` becomes `1.2.0` in one PR, never `1.2.1`. Use a minor bump for features and a patch bump for fixes, unless the repo says otherwise.

In `mono-repo-apps`:

- Bump every service the diff touches. The version lives in that service's `terraform/published.json`.
- The graphql project is the exception: run `yarn changeset` instead of editing `published.json`.
- Docs-only changes get no bump. Say so in one line of the body.

In any other repo, follow its CLAUDE.md, AGENTS.md, or contributing guide. If it documents no versioning, bump nothing.
