# Page data

`scripts/render.py` builds the page from one JSON file you write. It takes the layout, the counts, the read times, the dependency links, and the reading checkboxes from its template and from `gather.sh`'s output. You write only what takes reading the diff. Text fields allow `backtick` spans for code. Every sentence must trace to the diff, the ticket, or the repo, never to the PR description.

```json
{
  "lede": "One sentence, from the code, saying what the change does.",
  "open_first": {"path": "src/emitter.ts", "why": "because every other cohort calls it"},
  "ticket": {
    "key": "ABC-123",
    "url": "https://tracker/browse/ABC-123",
    "summary": "The ticket's summary line",
    "asks": [{"ask": "Show confetti when an offer is accepted", "status": "addressed", "where": "src/chat/offer.tsx:42", "note": ""}],
    "unasked": ["A version bump in `package.json`"]
  },
  "cohorts": [
    {
      "id": "particle-emitter",
      "name": "Particle emitter",
      "summary": "A few words for the orientation table",
      "what_changed": "One or two sentences, from the code.",
      "depends_on": [],
      "files": {"src/emitter.ts": "behavior", "src/emitter.test.ts": "test"},
      "behavior": {"before": "No particles render.", "after": "A burst of 40 particles renders for 1.2s."},
      "layers": [{"where": "src/emitter.ts:10-48", "does": "spawns and animates particles", "code": "optional short snippet", "count": "optional, such as: same change in 14 tests"}],
      "diagram": null,
      "blast_radius": ["`src/feed/card.tsx:88` calls `emit` and wasn't changed"],
      "tests": {"asserted": ["emits 40 particles"], "gaps": ["no test for reduced motion"]},
      "review_focus": [{"q": "Does the cleanup run if the component unmounts mid-animation?", "where": "src/emitter.ts:51"}],
      "author_questions": [{"q": "Where does the 1.2s duration come from?", "where": "src/emitter.ts:12", "looked_for": "a design token, a constant elsewhere, or a ticket note"}]
    }
  ],
  "housekeeping": [{"path": "package.json", "kind": "release", "note": "version 1.2.3 to 1.3.0"}],
  "version_bump": [{"package": "chat-widgets", "from": "1.2.3", "to": "1.3.0", "convention": "Minor bump, which matches this project's history."}]
}
```

## Fields

- **`ticket`:** `null` when the PR title and branch carry no ticket key. `asks` is empty when the ticket states none. `status` is `addressed`, `partial`, or `not in this diff`. `where` is the `file:line` that does it, and `note` says which part is missing for `partial`. `unasked` lists substantial changes no ask covers.
- **`cohorts`:** in reading order. `id` is kebab-case. `depends_on` lists only ids of earlier cohorts.
- **`files`:** every path in `files.tsv` belongs to exactly one cohort or to `housekeeping`, with a role: `behavior`, `contract`, `test`, `config`, `release`, `docs`, or `generated`. A manifest change that only adds dependencies is `config`. The renderer computes file counts, line counts, and read times from these.
- **`behavior`:** two concrete lines, or `null` for a pure refactor, which renders as "Behavior is unchanged."
- **`layers`:** contract, implementation, call sites, tests, then config. `code` holds only the lines that carry the change. Give a mechanical change repeated across many files one layer with a `count`.
- **`diagram`:** mermaid `sequenceDiagram` source, only when the call order, a fan-out, or who talks to whom changed. Otherwise `null`.
- **`blast_radius`:** callers outside the diff, from `callers.tsv`. An empty list renders as "Nothing outside this diff calls the changed code."
- **`review_focus`:** 2 to 4 questions a reviewer can answer by reading, each with its `file:line`.
- **`author_questions`:** up to 3 questions that only the author can answer, with what you looked for and didn't find. Use an empty list when there's nothing to ask.
- **`housekeeping`:** release plumbing, docs, and generated files only, one row each. `version_bump` lists one entry per bumped package, and is empty when there is none.

## What the data must not have

- No verdict, score, grade, or risk rating, in any field.
- No claim that something is wrong. Phrase it as a review focus question.
- No sentence whose source is the PR description.
