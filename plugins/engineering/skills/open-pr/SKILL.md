---
name: open-pr
description: >
  Open a pull request with a short title and a body in a fixed format. Use when
  asked to open a PR or put a change up for review, after finishing a change that
  needs review, or when another skill needs the PR title and body format.
---

The user's instructions win over the defaults below.

1. Remove debug output and stray files from the diff. For comments and docs, invoke the `kill-comments` skill.
2. Bump a version only when the repo, the user, or another skill says to.
3. Commit and push.
4. Invoke the `verify` skill for the `Checks and claims` evidence, unless the caller already has evidence for the head commit.
5. Write the title and body in the format below.
6. Open it ready for review with `gh pr create`. Never open a draft.
7. Reply with the PR url.

## Title

Invoke the `git` skill, and write the title in its commit subject format. Append the ticket key as `(ABC-123)`, which does not count toward the 50 characters. Omit it if there is no ticket.

## Body

If the repo has a PR template, fill it in place of the sections below, just as tersely.

Open the body with a note naming who wrote it and for whom, then a blank line:

    > [!NOTE]
    > 🤖 **<your model's name> opened this on behalf of <the user's first name>**

Then the sections, in this order:

    ## Why
    The problem, and what this change does about it, in 1 to 3 plain sentences a PM
    can read. Evidence when it helps: numbers, error text, a linked incident. Link
    related PRs as `<org>/<repo>#<n>` or `#<n>`.

    ## Change
    The smallest visual of the change. Then up to 3 bullets for what the visual
    doesn't show, such as a version bump. Identifiers in backticks.

    ## Evidence
    ### Checks and claims
    Ran on `<short sha>`.
    - **Before:** the failing test, error output, or screenshot
    - **After:** the passing test, output, or screenshot

    ## Risk
    - **Rollback:** whether a revert undoes it. If not, what a revert can't undo: a
      migration, a data change, or a published contract
    - **Blast radius:** who's affected if it's wrong, outside this diff: callers,
      services, or clients

    ## Follow up
    - Only when something must happen after merge, such as a config change in another
      repo

Rules:

- For `Change`, invoke the `show-me` skill and pick the smallest visual of the diff, such as a diff-shaped call tree or pseudocode.
- `Checks and claims` under `Evidence` comes from step 4. A skill that tests the change deployed adds its own part below it, such as `Staging`, with its own `Ran on` line. Each skill replaces only its own part. It embeds the real output of what was run, in a code block, trimmed to the lines that show the result, and names the commit it ran on. Never restate a result in your own words. A test plan's results can be a table of step, before, after, and result instead of the two bullets. A screenshot goes in only as an image URL you already have, since GitHub's API can't upload one. If nothing was run, write "Not run" and why.
- For a docs-only change, `Why` is one sentence, and `Evidence` and `Risk` are left out.
- `Follow up` is optional. Leave it out rather than writing "none".
- The `walk-through-pr` skill adds a `Walkthrough` section right below the note later. Other skills leave it there.
- Keep it short. Most bodies fit on one screen. Outside `Change`, a table or code block goes in only when prose cannot say it as well.
- No checklist, and no restating the diff line by line.
- Every claim must be true of the code as pushed: what it fixes, what it leaves alone, whether CI is green.
- No ticket link in the body when the title already carries the key.
