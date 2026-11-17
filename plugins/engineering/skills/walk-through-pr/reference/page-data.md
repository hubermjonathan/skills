# Page data

`scripts/render.py` builds the page from one JSON file. `page-data.schema.json` is its shape. The renderer supplies the layout, the reading order, the PR and ticket links, the file links, and the counts. You write only what takes reading the diff.

Text fields allow `backtick` spans for code. A `where` is a repo path, optionally with `:line` or `:start-end` at the PR head, such as `src/emitter.ts:10-48`. Write the full path. The page shows only the file name and links it to that file in the PR.

```json
{
  "summary": "Adds a confetti burst when a buyer accepts an offer.",
  "overview": null,
  "areas": [
    {
      "name": "Confetti on accept",
      "gist": "Accepting an offer now plays a short confetti burst.",
      "behavior": {
        "before": "Accepting an offer closes the sheet and shows nothing.",
        "after": "Accepting an offer plays 40 particles for 1.2 seconds, then closes the sheet."
      },
      "sketch": {
        "kind": "mermaid",
        "source": "sequenceDiagram\n  participant Sheet as OfferSheet\n  participant Emitter\n  Sheet->>Sheet: saveOffer()\n  rect added\n  Sheet->>Emitter: emitConfetti(40)\n  Emitter-->>Sheet: done after 1.2s\n  end"
      },
      "changes": [
        {"change": "Adds an emitter that spawns and animates particles.", "where": "src/emitter.ts:10-48", "role": "behavior"},
        {"change": "Fires the burst after the offer saves.", "where": "src/chat/offer.tsx:42", "role": "behavior"},
        {"change": "Closes the sheet when the burst ends, not right away.", "where": "src/chat/offer.tsx:47", "role": "behavior"}
      ],
      "reach": [{"where": "src/feed/card.tsx:88", "note": "Also calls `emit`, unchanged"}],
      "tests": {"files": ["src/emitter.test.ts", "src/offer.test.ts"], "covered": ["The particle count"], "missing": ["Reduced motion"]}
    },
    {
      "name": "Particle sprite in the bundle",
      "gist": "The app bundle now ships the particle sprite.",
      "behavior": null,
      "sketch": null,
      "changes": [
        {"change": "Adds `.webp` to the asset extensions, so the sprite bundles.", "where": "metro.config.js:12", "role": "config"}
      ],
      "reach": [],
      "tests": {"files": [], "covered": [], "missing": []}
    }
  ],
  "housekeeping": [{"where": "package.json", "note": "Version 1.2.3 to 1.3.0"}]
}
```

## Fields

The renderer warns when a field runs past its word cap. Treat a warning as a sentence to cut.

| Field | What it holds | Cap |
|---|---|---|
| `summary` | What the PR is, for someone who hasn't seen it. One or two sentences. | 50 words |
| `overview` | One sketch of the parts the main areas touch, with each area's change marked, in the same shape as an area's `sketch`. `null` when the PR has one main area. | |
| `areas` | In reading order, main areas first. | |
| `name` | A few words naming the area of impact. | |
| `gist` | What changed in this area, in one sentence. | 15 words |
| `behavior` | Before and after, each in a sentence or two, or `null` for a pure refactor or a supporting area. This is the detail a reviewer needs most, so keep the specifics: values, conditions, and who sees the change. | |
| `sketch` | One diagram of the area as this PR leaves it, with what the PR adds or removes marked, as `SKILL.md` describes. `kind` is `mermaid` for Mermaid source, or `tree-diff` for an indented tree whose lines start with `+`, `-`, or a space. `null` on a supporting area. The renderer warns when a sketch marks nothing. An area whose `behavior` and `sketch` are both `null` shows compact, and the renderer warns when it comes before a main area. | |
| `changes` | The changes that make up this area, in reading order: contract, implementation, call sites, then config. One row per change, as one complete sentence. A file with several changes gets several rows, which the page lists under the file. `where` is the file and the line where the change starts. `role` is `behavior`, `contract`, `config`, or `docs`. `contract` is a change that code outside the area depends on: an API, a schema, a message format, an event, or a signature that other callers use. A constructor argument that dependency injection fills, and the wiring that passes it in, are `behavior`. Put a mechanical change repeated across files in one row, with the other files in `also`. Test files go in `tests`, not here. The renderer warns on a `;` outside a code span. | 20 words per `change` |
| `reach` | Code in files this PR doesn't touch that uses the changed names, from `callers.tsv`. Use an empty list when nothing does, and the page says so. | 15 words per `note` |
| `tests` | `files`: the test files this area changes, which the page counts as accounted for but doesn't list. `covered`: behavior that a test in the PR checks. `missing`: behavior that no test checks. Phrases, not sentences. | 12 words each |
| `housekeeping` | The files a reviewer can skip, as `SKILL.md` defines them, one row each, with a short `note` or `""`. | |

Every path in `files.tsv` appears in an area's `changes` (or its `also`), an area's `tests.files`, or `housekeeping`. A file that holds changes for two areas appears in both. A path the data leaves out shows under housekeeping, with a warning.

## What the data must not have

- No verdict, score, or risk rating, in any field.
- No claim that something is wrong, and no questions. State what the code does, and the reviewer judges it.
- No sentence whose source is the PR description or its comments.
- No claim about what the code does that only a code comment supports.
