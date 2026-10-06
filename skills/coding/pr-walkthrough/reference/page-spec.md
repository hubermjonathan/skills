# Page structure

The page is a docs article, not a dashboard, laid out in three columns. If a design profile supplies a docs shell, use it as intended.

- **Nav rail:** the reading progress line at the top, such as `1 of 4 read`, then the cohorts in reading order, plus `ticket`, `orientation`, and `housekeeping`. Each item is an anchor link, and a cohort's item shows a check mark once the reader ticks it. Mark the first one `aria-current="page"`.
- **Article:** the walkthrough, in the order below.
- **TOC rail:** the layers inside the cohort in view, or a flat list of every cohort's sections. Don't duplicate the nav rail.

## Article order

**1. Eyebrow, h1, and lede**

The eyebrow is the repo and PR number, such as `org/repo #123`. The h1 is the PR title. The lede is one sentence, from the code, saying what the change does. Under it goes a plain row of facts: author, base ← head, files, +/-, and labels.

**2. Orientation**

This is the reviewer's first 30 seconds: a short table, one row per cohort.

| Area | What changed | Depends on | Files | + / - | Read | For the author |
|---|---|---|---|---|---|---|

`Read` is a time estimate in minutes for that cohort alone, at about 10 lines of behavior code a minute, rounded up. Count only the cohort's behavior code, not the whole diff. `Depends on` names earlier cohorts, or a dash. `For the author` is the number of questions only the author can answer. Put the generated and housekeeping rows last, with dashes.

Then add one line naming the reading order, and one line naming the single file the reviewer should open first, and why.

**3. Ticket**

The key as a link, the summary, and the asks table:

| Ask | In this diff | Where |
|---|---|---|

`In this diff` is `addressed`, `partial`, or `not in this diff`, rendered as a plain word, not a badge that asserts a claim. `Where` is a `file:line`. Below the table, list the changes in the diff that no ask covers.

If the PR title and branch carry no ticket key, say so in one line and skip the section.

**4. One section per cohort**

The h2 is the area name, with the reader's checkbox beside it, labeled "I've read this". Then, in order:

- a **depends on** line linking the earlier cohorts this one builds on, or saying it depends on nothing
- a one-paragraph **what changed**
- the **behavior delta**, as a two-row table (`before` and `after`) or a tip callout, whichever reads better for the cohort. Never both.
- the **layers**, as an ordered list: each `path:line-range`, then what that layer does. Show only the code that carries the change, as a short code block with the filename in its header. A mechanical rename repeated across 14 tests is one block plus a count, never 14 blocks.
- a mermaid `sequenceDiagram` in `<pre class="mermaid">`, only if the call flow changed
- the **blast radius:** a list of call sites outside the diff, or the sentence that nothing else calls it
- the **test coverage:** what this diff asserts, and what behavior has no assertion
- the **review focus:** 2 to 4 questions, each with its `file:line`
- **only the author knows:** up to 3 questions, each with its `file:line` and what you looked for and didn't find. Open the list with one line saying the PR description wasn't read, so it may already answer some of them. Leave the list out when there's nothing to ask.

**5. Housekeeping**

One section with the reader's checkbox beside its heading, and one table, one row each for release plumbing, docs, and generated files, with no walkthrough. If a version bump is present, state the old and new values and whether the bump matches the project's convention, from `release-plumbing.txt` and sibling history.

**6. Footer**

One short paragraph of plain text, with no styling flourish. It says that nothing was posted to the PR, that the PR description and comments weren't read, and that the diff, the ticket, and the repo are the only sources. Name the head SHA, so the reader knows which revision the page maps.

## Reading progress

The checkboxes are the reader's own marks. They start empty, and the page never ticks one itself. Save their state in `localStorage` under a key built from the repo, the PR number, and the head SHA, so a new push starts fresh. Storage can be blocked where the page is hosted, so the page must still work without it. This script does both. Fill in the key, give each checkbox `data-cohort="<cohort id>"`, give its nav item `data-nav="<cohort id>"`, and give the progress line `data-progress`:

```html
<script>
(() => {
  const key = "pr-walkthrough:<owner>/<repo>#<pr>@<head-sha>";
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(key) || "{}"); } catch (e) {}
  const boxes = [...document.querySelectorAll("input[data-cohort]")];
  const progress = document.querySelector("[data-progress]");
  const update = () => {
    const done = boxes.filter((b) => b.checked).length;
    if (progress) progress.textContent = `${done} of ${boxes.length} read`;
    for (const b of boxes) {
      for (const n of document.querySelectorAll(`[data-nav="${b.dataset.cohort}"]`)) n.classList.toggle("read", b.checked);
    }
  };
  for (const b of boxes) {
    b.checked = !!saved[b.dataset.cohort];
    b.addEventListener("change", () => {
      saved[b.dataset.cohort] = b.checked;
      try { localStorage.setItem(key, JSON.stringify(saved)); } catch (e) {}
      update();
    });
  }
  update();
})();
</script>
```

Style `.read` on nav items with a check mark. That's the only progress styling.

## What the page must not have

- No verdict, score, grade, risk rating, or "estimated review effort" out of 5. A per-cohort minute estimate is a schedule, not a judgment, so it's allowed. A single number rating the PR is not.
- No severity colors on cohorts. Semantic color is for the behavior-delta callout only.
- No badge that asserts a claim, such as verified, approved, safe, or reviewed. The reader's own checkboxes are the only progress marks.
- No "AI generated" note, no poem, and no emoji section markers.
- No sentence whose source is the PR description.
