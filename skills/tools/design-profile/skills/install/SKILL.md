---
name: install
description: Install or update a design profile for HTML artifacts.
disable-model-invocation: true
---

# Install a design profile

A profile is three files: usage rules (markdown), design tokens (CSS), and an optional icon sprite (SVG). Work out which local file plays each role, then run the script once with explicit paths:

    sh scripts/install-profile.sh --profile NAME --grammar PATH --tokens PATH [--icons PATH]

It copies each file to its canonical name, so source filenames don't matter. It installs nothing when a file is missing, empty, a directory, or looks like the wrong role, such as swapped grammar and tokens. Relay its error instead of working around it. It ends by checking that the profile loads.

## 1. Get the name

`--profile` has no default. If the user didn't name the design system, ask. A filename or a repo name is a hint, not an answer, and a profile installed under the wrong name is never found.

## 2. Find the files

- **A folder:** list it and map each file to a role.
- **Paths:** pass them through.
- **A description,** such as "the ones I just downloaded": look in the likely places, newest first, and confirm before installing.

      find ~/Downloads ~/Desktop ~/Documents -maxdepth 2 \( -name '*.css' -o -name '*.md' -o -name '*.svg' \) -newermt '-14 days' 2>/dev/null | head -20

Map by content, not name. The tokens file declares custom properties or a `:root` block. The grammar is markdown with `#` headings. The sprite starts with `<svg` and holds `<symbol id=...>` elements. When two files fit one role, or no grammar file is obvious, ask. A wrong file installs cleanly and renders wrong.

## 3. State the mapping, then install

Show the mapping before running, so a bad guess is visible:

    profile -> offerup
    grammar -> ~/Downloads/offerup-grammar.md
    tokens  -> ~/Downloads/tokens (1).css
    icons   -> none found

A re-install without `--icons` removes the old sprite.

Afterwards, say the profile is installed and that pages use it by naming it to the `use` skill. Warn that a re-install overwrites the profile's files, so local edits belong in the profile's source.
