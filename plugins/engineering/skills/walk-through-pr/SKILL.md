---
name: walk-through-pr
description: >
  Build a short page that maps a GitHub PR for a human reviewer: what the PR is,
  then its changes grouped into areas of impact, in reading order, each with its
  before-and-after behavior and a sketch. Use when someone wants a map of a PR
  before reviewing it, or asks for a PR walkthrough, summary, or review prep.
---

# Walk through a PR

Build one page that a reviewer can take in fast. The page is a map, not a verdict, and it's short: every sentence is written to be read once and acted on.

## The two hard rules

**1. You are not reviewing.** No findings, no severities, no bugs, and no approve or block. Where something is worth a second look, ask it as a question anchored on a `file:line`. If the user wants a review, that's the `review-code` skill.

**2. The PR description and comments are off limits.** Don't read the PR body or any comment, and don't pass them to a subagent. `scripts/gather.sh` leaves them out, and `scripts/attach.sh` edits the description without showing it to you. Every sentence on the page traces to the diff or the repo, so the reviewer doesn't inherit the author's framing of their own change. Commit subjects are author prose too: use them only as a hint about which files belong together.

## Step 1: gather

    <this skill's directory>/scripts/gather.sh <pr> [out-dir]

Run it inside a checkout of the PR's repo, because it reads callers from the checkout. `<pr>` is a PR URL, `owner/repo#<n>`, or a bare number for the checked-out repo. It prints an output directory holding `meta.json`, `pr.diff`, `pr-numbered.diff`, `files.tsv`, `callers.tsv`, and `commit-subjects.txt`.

Read the whole diff. Take line numbers from `pr-numbered.diff`, which numbers each line as it is at the PR's head.

## Step 2: group the changes into areas

An **area** is one area of impact: changes a reviewer should hold in their head at once, because understanding one needs the others. This grouping is the value of the page, since GitHub already gives a flat file list. Usually there are 1 to 5 areas, never one per file. Group by:

- the symbol graph: a changed function, its callers, and its tests are one area
- the behavior: two files that together move one flag's effect are one area, even in different modules
- the surface: a contract change and the clients updated for it are one area

Release plumbing, docs, lockfiles, and generated files go in **housekeeping**. A config change with an effect of its own, such as a scanner's ignore list, is an area.

Order areas by what to read first: the contract or the core behavior change, then what follows from it. When area B uses something area A changes, A comes first.

## Step 3: write the page data

Write the data in the shape `reference/page-data.md` gives. It holds each field's word cap.

Write every prose field the way one engineer tells another: the point first, in plain words, as short as a reviewer can act on.

- Keep what changes what the reviewer does or understands: the names, values, and conditions they act on. Leave out how you found them.
- Say the effect, not the mechanism. "Looks up the full user profile on every badge count" becomes "fetches data it rarely needs on every badge count".
- Write plain spoken sentences, one idea each, with periods over commas. Give each thing one name across the page. Say confidence once, where it matters.
- Cut any sentence the reviewer wouldn't miss. Then check the other way: if they'd have to ask a follow-up before acting, add the answer.

The summary says what the PR is, for someone who hasn't seen it.

Two fields carry the detail, so keep their specifics:

- **`behavior`**: before and after, as two concrete sentences with the real values and conditions. If behavior is unchanged, as in a pure refactor, use `null`.
- **`sketch`**: one diagram of the area as this PR leaves it, with the change marked. "Draw the sketch" below says how.

### Draw the sketch

The reviewer reads the code itself in the PR's diff, so the sketch draws what the diff can't show: how the pieces connect, and which of them this PR adds or removes. Name functions, components, services, and files in it, not the statements inside them.

Default to a Mermaid diagram: a `sequenceDiagram` when the change adds or reorders calls between parts, or a `flowchart` when it adds a branch, a check, or a fallback. Use a `tree-diff` when the change is the tree itself: files added or moved, config keys, or components nested.

Mark what the PR changes:

- In a flowchart, end the label of a box the PR adds with `:::added`, as in `B[retry]:::added`, and a box it removes with `:::removed`. Keep removed boxes in the diagram so the reviewer sees what went away. Mark boxes, not arrows: draw an arrow the PR adds as `==>`, and every other arrow as `-->` or `-.->` as usual.
- In a sequence diagram, wrap the calls the PR adds in a block that starts with the line `rect added` and ends with `end`, and the calls it removes in `rect removed` … `end`. Draw a removed call with a `-x` arrow.
- In a `tree-diff`, start each added line with `+` and each removed line with `-`.

Leave what was already there unmarked, and keep only enough of it to place the change. Keep each diagram to about 8 boxes or 5 participants, with about 3 boxes per row and labels of a few words: a name, not a sentence. A wider diagram shrinks to fit the page and gets hard to read. Write only the diagram itself, since the page sets its colors and fonts.

### Write the rest

For `changes`, write one row per file. When a file has several changes, name them together in one phrase, such as "Adds the fallback constants and passes both values to the request".

For `reach`, read `callers.tsv`. It lists where the base branch mentions each changed name in files this PR doesn't touch, and `reach` holds only those files. A caller that was left alone is the most useful thing to tell a reviewer, and "nothing else calls it" is worth saying too. Grep yourself only for a name it doesn't list.

For `questions`, ask what a reviewer can settle by reading, and mark `ask_author` on what only the author can answer.

## Step 4: render

    python3 <this skill's directory>/scripts/render.py <data.json> <gather-out-dir> <page.html> <design-dir>

`<design-dir>` is the directory of the design profile that styles the page. Find it with the `use-design-profile` skill, and pass only the directory, since the renderer applies the profile itself. The page takes its tokens, icons, and light and dark switch from there. To link the ticket, set `TICKET_URL` to the tracker's URL for a ticket, with `{key}` where the key goes.

It prints every error and warning. Fix the data and run it again until it writes the page with neither.

## Step 5: publish and hand off

Publish the page as an artifact if your agent can, with a one-sentence description naming the PR. Otherwise, give the user the file's path, since a file has no link to attach.

If the page has a link, attach it to the PR description:

    <this skill's directory>/scripts/attach.sh <pr> <url> [--share-note]

It puts a `Walkthrough` section right below the description's disclosure note, replacing an earlier one, names the commit the page was built on, and never prints the description.

A published page can start out visible only to its author, and only the author can share it. Unless you know the PR's reviewers can open the page, attach it with `--share-note`. That adds a note asking the author to share the page and then add the `ready-for-review` label, on the first attach only. When the PR gets that label, delete the note:

    <this skill's directory>/scripts/attach.sh <pr> --shared

Once the note is deleted, by this or by hand, it stays gone.

Reply with the page's link or path, the area names in reading order, and the number of questions marked for the author. Say whether the link was attached, that nothing else was posted, and that the description and comments weren't read.
