---
name: design-profile
description: "Use whenever building, editing, or reviewing an HTML artifact — any self-contained HTML page, whether published through an artifact tool or saved as a file, including dashboards, reports, charts, trackers, timelines, calculators, landing pages, and one-off interactive tools. Load it before writing the page's markup or choosing any color, font, spacing, or radius, not after. It supplies the styling system every artifact should use — the active design profile's grammar, design tokens, and icon sprite, selected by the ~/.claude/artifact-design-profile mode file and defaulting to 'offerup'. A profile name passed as the skill's argument, or named by the user for this page, overrides the default for that page only. When the selected profile is 'none' the skill stands down and applies nothing."
---

# Apply a design profile

Applies a real, mined design system to a self-contained HTML page. Profiles are self-contained, so this
skill is design-system-agnostic — the active one is chosen by configuration, not hardcoded here.

This is the default styling path for artifacts, not an occasional exception: a page that invents
its own colors and spacing when a profile is active is the failure mode this exists to prevent. Resolve
the profile *before* writing markup, so the tokens shape the page rather than getting retrofitted onto it.

## Step 1 — resolve the profile

Check for an override first. The user overrides the default for this page by passing a profile name as the skill's argument (`design-profile offerup`, `design-profile none`) or by naming one in the request ("use the offerup profile", "no design profile"). "No design profile" and similar mean `none`.

```sh
sh scripts/profile.sh <override>   # an override was given
sh scripts/profile.sh              # no override: the active profile
```

An override applies to this page only. It never writes the mode file, so the next page goes back to the default. To change the default, use the `switch-design-profile` skill.

Either form prints the profile name, where it came from, and absolute paths to that profile's files. The
selection lives in the mode file `~/.claude/artifact-design-profile` — one profile name on one line —
and is `offerup` when that file is absent or empty. The file is read on every run, so
the `switch-design-profile` skill applies to the next artifact with no restart.

Act on its exit code:

- **0** — a profile resolved; continue to step 2.
- **3** — the profile is `none`, the reserved opt-out. **Stop using this skill.** Apply no grammar, no
  tokens, no sprite; build the page on your own judgement. This is a deliberate choice, not a
  misconfiguration, so don't offer to fix it, don't suggest installing a profile, and don't mention
  the profile machinery in your answer.
- **1** — the named profile isn't installed; it lists what is available. Do not silently fall back to
  a different profile, including the default when an override was given; say which one was requested and stop.

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

Adding a design system means adding a sibling directory with those filenames and naming it in the
mode file. Nothing in this file needs to change. The store is created by
the `install-design-profile` skill on first install; use that skill rather than writing to it directly.

`none` is a reserved name, not a directory — it means "no profile", and it is honoured before the
filesystem is consulted, so a directory called `none` can never be selected.

## Honest limits

A profile's grammar ends with the claims that could not be verified when it was mined. Don't present
inferred values as confirmed.
