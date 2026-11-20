---
name: walk-through-pr
description: >
  Build a page that maps a GitHub PR for its reviewers, with its changes grouped
  into areas of impact and each area's code beside it, and link it from the PR
  description. Use when someone wants a map of a PR before reviewing it, or asks
  for a PR walkthrough or review prep.
---

# Walk through a PR

Build one page that a reviewer can take in fast and review from. The page is a map, not a verdict, and it's short: every sentence is written to be read once and acted on. Each area's code sits beside its prose, with the lines its change rows point at marked, so the reviewer reads the diff without leaving the page.

To only delete the share note, run `<this skill's directory>/scripts/attach.sh <pr> --shared` and stop.

## The two hard rules

**1. You are not reviewing.** No findings, no severities, no bugs, no questions, and no approve or block. When something deserves a second look, read the code until you know what it does, and state that as a fact in the row of the change it bears on, or in a `reach` note when it's about a caller outside the PR. The reviewer judges it. If the user wants a review, that's the `review-code` skill.

**2. The PR description and comments are off limits.** Don't read the PR body or any comment, and don't pass them to a subagent. `scripts/gather.sh` leaves them out, and `scripts/attach.sh` edits the description without showing it to you. Every sentence on the page traces to the diff or the repo, so the reviewer doesn't inherit the author's framing of their own change. Commit subjects are author prose too: use them only as a hint about which files belong together, and to find ticket keys. Code comments are author prose as well, and they go stale. Take what the code does from the code, take only the why from a comment, and state a fact only when the code shows it.

## Step 1: gather

    <this skill's directory>/scripts/gather.sh <pr> [out-dir]

Run it inside a checkout of the PR's repo. It reads callers and the code pane's files from there, and stops outside one. `<pr>` is a PR URL, `owner/repo#<n>`, or a bare number for the checked-out repo. It prints an output directory holding `meta.json`, `pr.diff`, `pr-numbered.diff`, `files.tsv`, `callers.tsv`, `owners.tsv`, and `commit-subjects.txt`, plus `head/` and `base/`, the files the page's code pane shows. It also prints the base it read callers from: the base branch for an open PR, and the base just before the merge for a merged one.

`owners.tsv` lists each changed file's code owners, from `CODEOWNERS` on the base. A file belongs to every owner on every line that matches it, and the catch-all `*` line counts only when no other line matches. To make an owner count only for files no other owner has, such as a platform team listed across the whole app, set `CODEOWNERS_FALLBACK` to its handles, space-separated, when you run `gather.sh`.

Read the whole diff. Take line numbers from `pr-numbered.diff`. It numbers each line by its place at the PR's head. A removed line carries the number of the head line below it, and a deleted file keeps its old numbers.

## Step 2: group the changes into areas

An **area** is one area of impact: changes a reviewer should hold in their head at once, because understanding one needs the others. This grouping is the value of the page, since GitHub already gives a flat file list. Usually there are 1 to 5 areas, never one per file. Group by:

- the symbol graph: a changed function, its callers, and its tests are one area
- the behavior: two files that together move one flag's effect are one area, even in different modules
- the surface: a contract change and the clients updated for it are one area

**Housekeeping** holds only the files a reviewer can skip: version bumps, lockfiles, generated files, tool settings such as `.gitignore` or a tool's version pin, and docs that describe no area. Every other file goes in the area it ships with, however small: a deleted script's README goes with its removal, and a new job's chart and Terraform go with its deployment. A config change with an effect of its own, such as a scanner's ignore list, is an area.

Each area is **main** or **supporting**. A main area carries a change the PR exists to make. A supporting area makes that change build, ship, or run, such as CI, images, or deploy config. A file that only wires a main area's change into place, such as a constructor argument or a bean, stays in that main area. A reviewer spends their time on the main areas, so a supporting area gets a compact entry.

Order main areas so that an area comes before any area whose changed lines use what it adds, changes, or removes. When two areas use each other, or neither uses the other, put the core behavior change first. Supporting areas come after every main area.

## Step 3: write the page data

Write the data in the shape `reference/page-data.md` gives. It holds each field's word cap.

Write every prose field the way one engineer tells another: the point first, in plain words, as short as a reviewer can act on.

- Keep what changes what the reviewer does or understands: the names, values, and conditions they act on. Leave out how you found them.
- Say the effect, not the mechanism. "Looks up the full user profile on every badge count" becomes "fetches data it rarely needs on every badge count".
- Write plain spoken sentences, one idea each, with periods over commas. Give each thing one name across the page. Say confidence once, where it matters.
- Cut any sentence the reviewer wouldn't miss. Then check the other way: if they'd have to ask a follow-up before acting, add the answer.

Two fields carry the detail of a main area, so keep their specifics:

- **`behavior`**: before and after, each in a sentence or two, with the real values and conditions. For a new feature, `before` says what happens today without it, such as "The menu has no export option." Use `null` only when nothing a user or caller sees changes, as in a pure refactor or the removal of code nothing reaches. A new metric, log, or event is a change someone sees.
- **`sketch`**: one diagram of the area as this PR leaves it, with the change marked. "Draw the sketch" below says how.

On a supporting area, set both to `null`, and the page shows it compact.

When the PR has two or more main areas, also draw **`overview`**: one sketch of the parts the main areas touch, with each area's change marked, so the reviewer sees what changes where before reading any area. With one main area, its sketch already shows that, so `overview` is `null`.

### Draw the sketch

The code pane shows the diff, so the sketch draws what the diff can't show: how the pieces connect, and which of them this PR adds, removes, or changes. Name functions, components, services, and files in it, not the statements inside them.

Default to a Mermaid diagram: a `sequenceDiagram` when the change adds or reorders calls between parts, or a `flowchart` when it adds a branch, a check, or a fallback. Use a `tree-diff` when the change is the tree itself: files added or moved, config keys, or components nested.

Mark what the PR changes:

- In a flowchart, put `:::added` right after a box the PR adds, as in `B[retry]:::added`, `:::removed` after a box it removes, and `:::changed` after a box whose code it changes. Keep removed boxes in the diagram so the reviewer sees what went away. Draw an arrow the PR adds as `==>`, and every other arrow as `-->` or `-.->`.
- In a sequence diagram, wrap the calls the PR adds in a block that starts with the line `rect added` and ends with `end`, the calls it removes in `rect removed` … `end`, and the calls whose behavior it changes in `rect changed` … `end`. Draw a removed call with a `-x` arrow.
- In a `tree-diff`, start each added line with `+` and each removed line with `-`.

Leave what was already there unmarked, and keep only enough of it to place the change. When the whole area is new, keep the existing part that reaches it, such as its route or its caller, unmarked, so the reviewer sees where it joins. Keep each diagram to about 8 boxes or 3 participants, with about 2 boxes per row and labels of a few words: a name, not a sentence. The sketch sits in a narrow column beside the code, and a wider diagram scrolls sideways. A short form of a long name is fine in a label, such as `channel.saved` for `notification_preferences.channel.saved`. To split a long name across two lines, put `<br/>` between two of its words, as in `useSavedListing<br/>Experiment`. Write only the diagram itself, since the page sets its colors and fonts.

### Write the rest

For `changes`, write one row per change, as one complete sentence that says what the code now does. Cover the lines that carry the change, not the whole hunk, since the page marks those lines under the sentence and dims the rest of the file. Give each part of a change that sits on its own lines its own row, so each row marks only the lines it describes. Two branches of one function on different lines are two rows. Lines that only follow from another row, such as an import, a destructured prop, or a style nothing uses anymore, need no row, and the pane shows them dimmed. When an area passes about 12 rows, merge the rows a reviewer reads together. "Takes `MeterRegistry`; `send` takes a user count and counts after success" becomes "The constructor takes a `MeterRegistry`." and "`send` takes the user count and records it after a successful send."

For `reach`, read `callers.tsv`. It lists where the base mentions each changed name in files this PR doesn't touch, and `reach` holds only files this PR doesn't touch. A caller that was left alone is the most useful thing to tell a reviewer. The file matches names as text, so each name is a lead: a hit is reach only when it calls, reads, implements, or mocks the code this PR changes. A different thing with the same name isn't reach. Each row's `kind` says why its name is listed:

- `declaration` or `both`: the PR's changed lines declare the name, or it names a changed file.
- `enclosing`: the change sits below its declaration in the diff, often inside it. Its hits are reach when the change is inside it.
- `call`: the PR starts or stops calling the name. Its hits are reach only when the diff also changes the name's definition.

A name lists its first 10 hits, and `hits` counts them all. For a name the file doesn't list, marks too common to list, or didn't search, grep the base yourself with `git grep -n -w <name> <base>`, where `<base>` is the base commit `gather.sh` printed. When a hit is only an import, point the row at the line that uses the name. The page links a caller you found this way but shows no code for it.

For `teams`, write one row for each owner in `owners.tsv`, so each team on a PR that spans several owners sees why it's there before reading any area. The page adds the team's file count and links to the areas that hold its files. `why` ties the team's files to what the PR is for, in one sentence. `what_changes` says what changes in the team's code, in two or three sentences, with the names and values it acts on. When a team's part is light, say what it can skip, such as "Only the lockfile changes."

## Step 4: render

    python3 <this skill's directory>/scripts/render.py <data.json> <gather-out-dir> <page.html> <design-dir>

`<design-dir>` is the directory of the `offerup` design profile, the profile the renderer's styles are built on. Find it with the `use-design-profile` skill, and pass only the directory, since the renderer applies the profile itself: its tokens, its icons, and its light and dark switch. To link each key in `tickets`, set `TICKET_URL` to the tracker's URL for a ticket, with `{key}` where the key goes.

It prints every error and warning. Fix the data and run it again until it writes the page with neither. The renderer can't parse Mermaid, so if your agent can open the page in a browser, check at a 1440px window that no sketch shows Mermaid's "Syntax error in text" or scrolls sideways.

## Step 5: publish and hand off

The page shows the PR at one commit. Check who wrote the PR: compare `author.login` in `meta.json` with `gh api user -q .login`.

When the user wrote it, the new page replaces the walkthrough already attached, so reviewers keep one link and their comments stay in one place. Run:

    <this skill's directory>/scripts/attach.sh <pr> --url

It prints the link of the walkthrough attached to the PR, or nothing. Publish the page as an artifact if your agent can: to that link when it printed one, and as a new artifact otherwise. When someone else wrote the PR, publish a new artifact. Give it a one-sentence description naming the PR, and grant it the `comments` capability in composer-only mode, `{"comments": {"composer_only": true}}`, so a reviewer can comment on a line from the page. If your agent can't publish, give the user the file's path, since a file has no link to attach.

When the user wrote the PR and the page has a link, attach it to the PR description:

    <this skill's directory>/scripts/attach.sh <pr> <url> <sha> [--share-note]

`<sha>` is `headRefOid` from `meta.json`, the commit the page shows. The script puts a `Walkthrough` section right below the description's disclosure note, or at the top when there is none, replacing an earlier one. The section names that commit, and the script never prints the description.

A published page can start out visible only to its author, and only the author can share it. Unless you know the PR's reviewers can open the page, pass `--share-note` on every attach. On the first attach, it adds a note asking the author to share the page and then add the `ready-for-review` label. Later attaches keep the note, and once someone deletes it, by hand or with `attach.sh <pr> --shared`, it stays gone.

Reply with the page's link or path and the area names in reading order. Say whether the link was attached, that nothing else was posted, and that the description and comments weren't read.
