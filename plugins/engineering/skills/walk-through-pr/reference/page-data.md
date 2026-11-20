# Page data

`scripts/render.py` builds the page from one JSON file. `page-data.schema.json` is its shape. The renderer supplies the layout, the reading-order list, the PR and ticket links, the file links, the counts, and the code pane beside each area. You write only what takes reading the diff.

Text fields allow `backtick` spans for code. A `where` is a repo path, optionally with `:line` or `:start-end`, such as `src/emitter.ts:10-48`. Write the full path. The page shows only the file name and links it to that file in the PR.

```json
{
  "title": "Play a confetti burst when a buyer accepts an offer",
  "tickets": ["ACME-42"],
  "summary": "Adds a confetti burst when a buyer accepts an offer.",
  "teams": [
    {"owner": "@acme/chat", "why": "You own the offer sheet, where the burst plays.", "what_changes": "Accepting an offer plays 40 particles for 1.2 seconds before the sheet closes."},
    {"owner": "@acme/platform", "why": "You own the Metro config the sprite needs.", "what_changes": "Adds `.webp` to the asset extensions. Nothing else in the build changes."}
  ],
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
| `title` | The page's headline: what the PR does, in plain words and sentence case. Start from the PR's title in `meta.json` and keep its wording where the diff bears it out. Leave out commit prefixes such as `feat(scope):`, ticket keys, and branch names. | 12 words |
| `tickets` | The ticket keys the PR is for, such as `ABC-123`, from its title, its branch name, or `commit-subjects.txt`, or an empty list. A number that isn't a ticket, such as a build number in a release branch, doesn't count. The page links each key when `TICKET_URL` is set. | |
| `summary` | What the PR is, for someone who hasn't seen it. One or two sentences. | 50 words |
| `teams` | One row per owner in `owners.tsv`, as `SKILL.md` describes, or an empty list when it lists none. `owner` is the handle as `owners.tsv` writes it. `why`: why the team is on the PR. `what_changes`: what changes in the team's code, in two or three sentences. | 20 words per `why`, 45 per `what_changes` |
| `overview` | One sketch of the parts the main areas touch, in the same shape as an area's `sketch`, or `null`, as `SKILL.md` describes. | |
| `areas` | In reading order, main areas first. | |
| `name` | A few words naming the area of impact. | |
| `gist` | What changed in this area, in one sentence. | 15 words |
| `behavior` | Before and after, each in a sentence or two. For a new feature, `before` says what happens today without it. `null` when nothing a user or caller sees changes, as in a pure refactor, and on a supporting area. This is the detail a reviewer needs most, so keep the specifics: values, conditions, and who sees the change. | |
| `sketch` | One diagram of the area as this PR leaves it, with what the PR adds, removes, or changes marked, as `SKILL.md` describes. `kind` is `mermaid` for Mermaid source, or `tree-diff` for an indented tree whose lines start with `+`, `-`, or a space. `null` on a supporting area. An area whose `behavior` and `sketch` are both `null` is a supporting area and shows compact. | |
| `changes` | The changes that make up this area, in reading order: contract, implementation, call sites, then config. The page shows each file at its first row, with all of that file's rows under it. One row per change, as one complete sentence. `where` is the file and the lines the change covers, as `path:start-end` or `path:line`, numbered as in `pr-numbered.diff`. A binary file, or a file renamed with no line changes, takes the bare path. `role` is `behavior`, `contract`, `config`, or `docs`. `contract` is a change that code outside the area depends on: an API, a schema, a type, a message format, an event, or a signature that other callers use. `config` is a value that must match something outside the code, such as a flag or experiment name, an env var, or a build setting. `docs` is documentation. Everything else is `behavior`, including a constructor argument that dependency injection fills and the wiring that passes it in. Put a mechanical change repeated across files, or a file that only re-exports or types another row's change inside the area, such as a barrel `index.ts` or a `*Props.ts` file, in that row's `also`. A type that another area or a caller outside the PR uses is a `contract` row of its own. Test files and their fixtures go in `tests`, not here. | 20 words per `change` |
| `reach` | Code in files this PR doesn't touch that uses the changed code, from `callers.tsv` or your own grep, numbered as on the base. Use an empty list when nothing does, and the page says so. | 15 words per `note` |
| `tests` | `files`: the test files this area changes, which the code pane shows under Tests. `covered`: changed behavior that a test at the PR head checks. `missing`: changed behavior that no test checks. For a removal, the changed behavior is what the remaining code does without it, so removing code nothing reached leaves both empty. On a supporting area, leave both empty. Phrases, not sentences. | 12 words each |
| `housekeeping` | The files a reviewer can skip, as `SKILL.md` defines them, one row each, with a short `note` or `""`. | 15 words per `note` |

Every path in `files.tsv` appears in an area's `changes`, a row's `also`, an area's `tests.files`, or `housekeeping`. A file that holds changes for two areas appears in both. A path the data leaves out shows under housekeeping, with a warning.

