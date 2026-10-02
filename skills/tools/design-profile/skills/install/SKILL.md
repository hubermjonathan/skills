---
name: install
description: Install or update a design profile for HTML artifacts.
disable-model-invocation: true
---

# Install a design profile

A profile is three files: usage rules (markdown), design tokens (css), and an optional icon sprite
(svg). Your job is to work out which local file plays each role, then hand the script explicit paths.
They are installed into `~/.claude/artifact-design-profiles/<name>/`, which the script creates on first
use — there is no separate setup step.

## The script takes per-file references only

```sh
sh scripts/install-profile.sh --profile NAME --grammar PATH --tokens PATH [--icons PATH]
```

It does no searching and no guessing. **Source filenames are irrelevant** — each file is copied to its
canonical name, so `tokens (1).css`, `offerup-grammar.md`, or `sprite.svg` all work untouched. Paths
may be absolute, relative, or start with `~/`.

**`--profile` is required and has no default.** If the person did not name the design system, ask — a filename or
a repo name is a hint, not an answer, and installing under the wrong name means the resolver will never
find it.

`--icons` is optional; a profile without a sprite is supported, and re-installing without `--icons`
removes a previously installed one.

## Translating what the person actually said

They will rarely hand you flags. Resolve their input first, then call the script once.

**A folder** — "install the profile from ~/Downloads", "the files are in ./design-system":
list it and map each file to a role. Do not assume canonical names.

```sh
ls -la <folder>
```

**Direct references** — "use ~/Downloads/grammar.md and ~/Downloads/tokens.css": pass them through.

**A description** — "the ones I just downloaded", "they're on my desktop", "I saved them somewhere in
Documents": search the likely places, newest first, and confirm before installing.

```sh
ls -lt ~/Downloads ~/Desktop 2>/dev/null | head -40
find ~/Downloads ~/Desktop ~/Documents -maxdepth 2 \( -name '*.css' -o -name '*.md' -o -name '*.svg' \) \
  -newermt '-14 days' 2>/dev/null | head -20
```

**Mapping by role, not by name.** Read the first lines of a candidate when its name is ambiguous:
the tokens file declares custom properties (`--ou-…`) or a `:root` block; the grammar file is prose
markdown with `#` headings; the sprite starts with `<svg` and contains `<symbol id=…>`.

**When it is ambiguous, ask.** Two plausible `.css` files, or no obvious grammar file, is a question
worth one round trip — installing the wrong file produces a profile that looks fine and renders wrong.

**State the mapping before running**, so a bad guess is visible:

> profile → `offerup`
> grammar → `~/Downloads/offerup-grammar.md`
> tokens → `~/Downloads/tokens (1).css`
> icons → none found

## Guardrails already in the script

You do not need to pre-validate; it refuses and installs nothing when a reference is missing, is a
directory, is unreadable, or is empty. It also **sniffs content** and rejects a swapped
`--grammar`/`--tokens` pair, a `.svg` passed as either, or a tokens file with no custom properties.
Relay its error rather than working around it.

## What to tell them afterwards

Say the profile is installed, and that pages use it by naming it to the `use` skill.

Also warn that a re-install **overwrites** a profile's files: profiles are a shared source of truth, so
local edits belong upstream instead.

## Verifying

```sh
sh ../use/scripts/profile.sh <name>
```

Prints the resolved paths for that profile. The install script runs this itself, so a clean install has
already proven the profile loads.

## Authoring a profile from scratch

Not this skill's job — it installs files that already exist. To build a profile by mining a design
system, use the `create` skill; it mines and writes the profile itself, so it does not
come back through here.
