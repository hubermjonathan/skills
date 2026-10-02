---
name: use
description: >
  Style a self-contained HTML page with a named design profile: its grammar, design
  tokens, and icon sprite. Use when building, editing, or reviewing an HTML page or
  artifact that should follow a design profile. Requires the profile name.
---

# Use a design profile

Applies a real, mined design system to a self-contained HTML page. Profiles are self-contained, so this
skill is design-system-agnostic: the profile is named on every use, never assumed.

Resolve the profile *before* writing markup, so the tokens shape the page rather than getting
retrofitted onto it.

## Step 1 — resolve the profile

A profile name is required. Take it from the skill's argument or from the request ("in the offerup
profile"). If none was given, list the installed profiles and ask which to use. Never pick one yourself.

```sh
sh scripts/profile.sh <name>
```

It prints absolute paths to that profile's files. Act on its exit code:

- **0** — the profile resolved; continue to step 2.
- **1** — the profile isn't installed, or a file is missing; it lists what is installed. Say which one
  was requested and stop. Never fall back to a different profile.
- **2** — no name was given; it lists what is installed. Ask which to use.

## Step 2 — read and apply

1. **Read the profile's `grammar.md`.** It is the rule set. Profiles are large, so jump by its own
   headings rather than reading top to bottom.
2. **Inline the profile's `tokens.css`** in full inside a `<style>` tag. Never retype values from it,
   never summarise it, and never write a raw hex where a token exists.
3. **Add the theme toggle** the profile's tokens file defines, if it has one.
4. **Paste the profile's `icons.svg`** only if the page has actually earned an icon. Default is none.
   Some profiles ship no sprite; that is normal.
5. **Build**, then check the page against the profile's do-not list.

## Non-negotiables that hold across profiles

A profile's own `grammar.md` always wins over this list. These are the defaults when it is silent:

- **Style only through tokens.** If a value has a token, use the token.
- **Ship the light/dark toggle** the profile defines, defaulting to whichever mode it specifies.
- **Supply a page container.** Component libraries rarely define one, so an artifact must add it.
- **Never use a token or icon that asserts a claim** — paid tier, verified, promoted, certified,
  rating. Those state something about the reader or the subject that a decorative page has no
  standing to state. A word is honest; a borrowed badge is not.
- **The default is no icon.** Before adding one, delete it — if nothing is lost, keep it deleted.
- **Respect `prefers-reduced-motion`** and keep keyboard focus visible.

## Profile layout

Profiles are data, not part of this skill. Each is a directory under `~/.claude/artifact-design-profiles/`:

```
~/.claude/artifact-design-profiles/<name>/
  grammar.md    usage rules — read into context, jump by heading
  tokens.css    values — inlined verbatim into the page
  icons.svg     optional sprite — pasted only when an icon is earned
```

Adding a design system means adding a sibling directory with those filenames. Nothing in this file
needs to change. The `install` skill creates the store on first install; use it rather than writing to
the store directly.

## Honest limits

A profile's grammar ends with the claims that could not be verified when it was mined. Don't present
inferred values as confirmed.
