---
name: open-pr
description: >
  Open a pull request with a short title and a body in a fixed format. Use when
  asked to open a PR or put a change up for review, after finishing a change that
  needs review, or when another skill needs the PR title and body format.
---

The user's instructions win over the defaults below.

1. Remove debug output and stray files from the diff. For comments and docs, invoke the `kill-comments` skill.
2. Bump a version only when the repo, the user, or another skill says to. Then commit and push.
3. Write the title and body in the format below.
4. Open it ready for review with `gh pr create`. Never open a draft.
5. Reply with the PR url.

## Title

`<scope>: <description>`, 50 characters at most. The scope is the service or project touched. Append the ticket key as `(ABC-123)`, which does not count toward the limit. Omit it if there is no ticket.

## Body

Open the body with a note naming who wrote it and for whom, then a blank line:

    > [!NOTE]
    > 🤖 **<your model's name> opened this on behalf of <the user's first name>**

Then the sections, in this order:

    ## Context
    The problem, what was tried before if relevant, and what this change does about it,
    in 1 to 4 plain, non-technical sentences a PM can read.

    ## Why
    The technical reason, short. Evidence when it helps: numbers, error text, a linked
    incident. Link related PRs as `<org>/<repo>#<n>` or `#<n>`.

    ## What
    - One bullet per change, grouped by area of impact, not by file
    - Identifiers in backticks

    ## Follow up
    - Only when something must happen after merge, such as a config change in another
      repo

Rules:

- `Context` is required when the change touches behavior a non-engineer cares about. Skip it for docs-only or purely internal changes.
- `Follow up` is optional. Leave it out rather than writing "none".
- Keep it short. Most bodies fit on one screen. A table or code block goes in only when prose cannot say it as well.
- No testing section, no checklist, no restating the diff line by line.
- Every claim must be true of the code as pushed: what it fixes, what it leaves alone, whether CI is green.
- No ticket link in the body when the title already carries the key.
- If the repo has a PR template, fill it in instead, just as tersely.
