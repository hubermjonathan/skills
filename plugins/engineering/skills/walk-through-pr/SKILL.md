---
name: walk-through-pr
description: >
  Build a short page that maps a GitHub PR for a human reviewer: what the PR is,
  then its changes grouped into areas of impact, in reading order, each with its
  before-and-after behavior, a sketch, and its code beside it. Use when someone
  wants a map of a PR before reviewing it, or asks for a PR walkthrough, summary,
  or review prep.
---

# Walk through a PR

Build one page that a reviewer can take in fast and review from. The page is a map, not a verdict, and it's short: every sentence is written to be read once and acted on. Each area's code sits beside its prose, with the lines its change rows point at marked, so the reviewer reads the diff without leaving the page.

## The two hard rules

**1. You are not reviewing.** No findings, no severities, no bugs, and no approve or block. When something deserves a second look, read the code until you know what it does, and state that as a fact in the change row it belongs to. The reviewer judges it. If the user wants a review, that's the `review-code` skill.

**2. The PR description and comments are off limits.** Don't read the PR body or any comment, and don't pass them to a subagent. `scripts/gather.sh` leaves them out, and `scripts/attach.sh` edits the description without showing it to you. Every sentence on the page traces to the diff or the repo, so the reviewer doesn't inherit the author's framing of their own change. Commit subjects are author prose too: use them only as a hint about which files belong together. Code comments are author prose as well, and they go stale. Say what the code does, use a comment only for why, and state a fact only when the code shows it.

## Step 1: gather

    <this skill's directory>/scripts/gather.sh <pr> [out-dir]

Run it inside a checkout of the PR's repo, because it reads callers from the checkout. `<pr>` is a PR URL, `owner/repo#<n>`, or a bare number for the checked-out repo. It prints an output directory holding `meta.json`, `pr.diff`, `pr-numbered.diff`, `files.tsv`, `callers.tsv`, and `commit-subjects.txt`, plus `head/` and `base/`, the files the page's code pane shows.

Read the whole diff. Take line numbers from `pr-numbered.diff`, which numbers each line as it is at the PR's head.

## Step 2: group the changes into areas

An **area** is one area of impact: changes a reviewer should hold in their head at once, because understanding one needs the others. This grouping is the value of the page, since GitHub already gives a flat file list. Usually there are 1 to 5 areas, never one per file. Group by:

- the symbol graph: a changed function, its callers, and its tests are one area
- the behavior: two files that together move one flag's effect are one area, even in different modules
- the surface: a contract change and the clients updated for it are one area

**Housekeeping** holds only the files a reviewer can skip: version bumps, lockfiles, generated files, tool settings such as `.gitignore` or a tool's version pin, and docs that describe no area. Every other file goes in the area it ships with, however small: a deleted script's README goes with its removal, and a new job's chart and Terraform go with its deployment. A config change with an effect of its own, such as a scanner's ignore list, is an area.

Each area is **main** or **supporting**. A main area carries a change the PR exists to make. A supporting area makes that change build, ship, or run, such as CI, images, or deploy config. A file that only wires a main area's change into place, such as a constructor argument or a bean, stays in that main area. A reviewer spends their time on the main areas, so a supporting area gets a compact entry.

Order areas by what to read first: the contract or the core behavior change, then what follows from it. When area B uses something area A changes, A comes first. Supporting areas come after every main area.

## Step 3: write the page data

Write the data in the shape `reference/page-data.md` gives. It holds each field's word cap.

Write every prose field the way one engineer tells another: the point first, in plain words, as short as a reviewer can act on.

- Keep what changes what the reviewer does or understands: the names, values, and conditions they act on. Leave out how you found them.
- Say the effect, not the mechanism. "Looks up the full user profile on every badge count" becomes "fetches data it rarely needs on every badge count".
- Write plain spoken sentences, one idea each, with periods over commas. Give each thing one name across the page. Say confidence once, where it matters.
- Cut any sentence the reviewer wouldn't miss. Then check the other way: if they'd have to ask a follow-up before acting, add the answer.

The summary says what the PR is, for someone who hasn't seen it.

Two fields carry the detail of a main area, so keep their specifics:

- **`behavior`**: before and after, each in a sentence or two, with the real values and conditions. If behavior is unchanged, as in a pure refactor, use `null`.
- **`sketch`**: one diagram of the area as this PR leaves it, with the change marked. "Draw the sketch" below says how.

On a supporting area, set both to `null`. The page then shows it compact: its gist and its changes, plus its callers and tests when they hold something.

When the PR has two or more main areas, also draw **`overview`**: one sketch of the parts the main areas touch, with each area's change marked, so the reviewer sees what changes where before reading any area. With one main area, its sketch already shows that, so `overview` is `null`.

### Draw the sketch

The reviewer reads the code itself in the PR's diff, so the sketch draws what the diff can't show: how the pieces connect, and which of them this PR adds or removes. Name functions, components, services, and files in it, not the statements inside them.

Default to a Mermaid diagram: a `sequenceDiagram` when the change adds or reorders calls between parts, or a `flowchart` when it adds a branch, a check, or a fallback. Use a `tree-diff` when the change is the tree itself: files added or moved, config keys, or components nested.

Mark what the PR changes:

- In a flowchart, end the label of a box the PR adds with `:::added`, as in `B[retry]:::added`, and a box it removes with `:::removed`. Keep removed boxes in the diagram so the reviewer sees what went away. Mark boxes, not arrows: draw an arrow the PR adds as `==>`, and every other arrow as `-->` or `-.->` as usual.
- In a sequence diagram, wrap the calls the PR adds in a block that starts with the line `rect added` and ends with `end`, and the calls it removes in `rect removed` … `end`. Draw a removed call with a `-x` arrow.
- In a `tree-diff`, start each added line with `+` and each removed line with `-`.

Leave what was already there unmarked, and keep only enough of it to place the change. Keep each diagram to about 8 boxes or 5 participants, with about 3 boxes per row and labels of a few words: a name, not a sentence. A short form of a long name is fine in a label, such as `channel.saved` for `notification_preferences.channel.saved`. A wider diagram shrinks to fit the page and gets hard to read. Write only the diagram itself, since the page sets its colors and fonts.

### Write the rest

For `changes`, write one row per change, as one complete sentence that says what the code now does. Its `where` names the lines the change covers, as `path:start-end` or `path:line`, from `pr-numbered.diff`. The page marks those lines in the code pane, with the sentence above them, and dims the rest of the file, so cover the lines that carry the change, not the whole hunk. A file with several changes gets several rows, and the page lists them under the file. Give each clause its own row: "Takes `MeterRegistry`; `send` takes a user count and counts after success" becomes "The constructor takes a `MeterRegistry`." and "`send` takes the user count and records it after a successful send."

For `reach`, read `callers.tsv`. It lists where the base branch mentions each changed name in files this PR doesn't touch, and `reach` holds only those files. A caller that was left alone is the most useful thing to tell a reviewer, and "nothing else calls it" is worth saying too. Grep yourself only for a name it doesn't list.

## Step 4: render

    python3 <this skill's directory>/scripts/render.py <data.json> <gather-out-dir> <page.html> <design-dir>

`<design-dir>` is the directory of the design profile that styles the page. Find it with the `use-design-profile` skill, and pass only the directory, since the renderer applies the profile itself. The page takes its tokens, icons, and light and dark switch from there. To link the ticket, set `TICKET_URL` to the tracker's URL for a ticket, with `{key}` where the key goes.

It prints every error and warning. Fix the data and run it again until it writes the page with neither.

## Step 5: publish and hand off

The page shows the PR at one commit. After the author pushes, run the skill again from step 1, and it replaces the page at the same link.

Publish the page as an artifact if your agent can, with a one-sentence description naming the PR. Grant it the `comments` capability in composer-only mode, `{"comments": {"composer_only": true}}`, so a reviewer can comment on a line from the page. Otherwise, give the user the file's path, since a file has no link to attach.

A rebuild goes to the page already attached, so reviewers keep one link and their comments stay in one place. Before you publish, run:

    <this skill's directory>/scripts/attach.sh <pr> --url

It prints the link of the walkthrough attached to the PR, or nothing. When it prints one, publish to that artifact. Otherwise, publish a new one.

If the page has a link, attach it to the PR description:

    <this skill's directory>/scripts/attach.sh <pr> <url> [--share-note]

It puts a `Walkthrough` section right below the description's disclosure note, replacing an earlier one, names the commit the page was built on, and never prints the description.

A published page can start out visible only to its author, and only the author can share it. Unless you know the PR's reviewers can open the page, attach it with `--share-note`. That adds a note asking the author to share the page and then add the `ready-for-review` label, on the first attach only. When the PR gets that label, delete the note:

    <this skill's directory>/scripts/attach.sh <pr> --shared

Once the note is deleted, by this or by hand, it stays gone.

Reply with the page's link or path and the area names in reading order. Say whether the link was attached, that nothing else was posted, and that the description and comments weren't read.
