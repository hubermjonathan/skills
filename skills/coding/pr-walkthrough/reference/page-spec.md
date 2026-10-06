# Page structure

The page is a docs article, not a dashboard, laid out in three columns. If a design profile supplies a docs shell, use it as intended.

- **Nav rail:** the cohorts in reading order, plus `ticket`, `orientation`, and `housekeeping`. Each item is an anchor link. Mark the first one `aria-current="page"`.
- **Article:** the walkthrough, in the order below.
- **TOC rail:** the layers inside the cohort in view, or a flat list of every cohort's sections. Don't duplicate the nav rail.

## Article order

**1. Eyebrow, h1, and lede**

The eyebrow is the repo and PR number, such as `org/repo #123`. The h1 is the PR title. The lede is one sentence, from the code, saying what the change does. Under it goes a plain row of facts: author, base ← head, files, +/-, and labels.

**2. Orientation**

This is the reviewer's first 30 seconds: a short table, one row per cohort.

| Area | What changed | Files | + / - | Read |
|---|---|---|---|---|

`Read` is a time estimate in minutes for that cohort alone, from its lines of behavior code, not the whole diff. Put the generated and housekeeping rows last, with a dash.

Then add one line naming the reading order, and one line naming the single file the reviewer should open first, and why.

**3. Ticket**

The key as a link, the summary, and the asks table:

| Ask | In this diff | Where |
|---|---|---|

`In this diff` is `addressed`, `partial`, or `not in this diff`, rendered as a plain word, not a badge that asserts a claim. `Where` is a `file:line`. Below the table, list the changes in the diff that no ask covers.

If the PR title carried no ticket key, say so in one line and skip the section.

**4. One section per cohort**

The h2 is the area name. Then, in order:

- a one-paragraph **what changed**
- the **behavior delta**, as a two-row table (`before` and `after`) or a tip callout, whichever reads better for the cohort. Never both.
- the **layers**, as an ordered list: each `path:line-range`, then what that layer does. Show only the code that carries the change, as a short code block with the filename in its header. A mechanical rename repeated across 14 tests is one block plus a count, never 14 blocks.
- a mermaid `sequenceDiagram` in `<pre class="mermaid">`, only if the call flow changed
- the **blast radius:** a list of call sites outside the diff, or the sentence that nothing else calls it
- the **test coverage:** what this diff asserts, and what behavior has no assertion
- the **review focus:** 2 to 4 questions, each with its `file:line`

**5. Housekeeping**

One section with one table, one row each for release plumbing, docs, and generated files, with no walkthrough. If a version bump is present, state the old and new values and whether the bump matches the project's convention, from `release-plumbing.txt` and sibling history.

**6. Footer**

One short paragraph of plain text, with no styling flourish. It says that nothing was posted to the PR, that the PR description and comments weren't read, and that the ticket and the diff are the only sources. Name the head SHA, so the reader knows which revision the page maps.

## What the page must not have

- No verdict, score, grade, risk rating, or "estimated review effort" out of 5. A per-cohort minute estimate is a schedule, not a judgment, so it's allowed. A single number rating the PR is not.
- No severity colors on cohorts. Semantic color is for the behavior-delta callout only.
- No badge that asserts a claim, such as verified, approved, safe, or reviewed.
- No "AI generated" note, no poem, and no emoji section markers.
- No sentence whose source is the PR description.
