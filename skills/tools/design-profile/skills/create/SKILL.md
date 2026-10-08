---
name: create
description: Add a design profile, from finished profile files or by mining a design system for its real values.
disable-model-invocation: true
---

# Create a design profile

A profile is three files that let an HTML page carry a design system honestly:

| File | What it holds |
|---|---|
| `grammar.md` | usage rules: how the design system applies color, type, geometry, motion, state, voice, and icons |
| `tokens.css` | values only: CSS custom properties for both themes |
| `icons.svg` | optional `<symbol>` sprite, referenced with `<use href="#id">` |

They come from one of two places: finished files someone hands you, or a design system you mine for its real values. Never invent them: a profile built on taste looks authoritative while being wrong, which is worse than no profile.

## 1. Get the name

The profile name has no default. If the user didn't name the design system, ask. A filename or a repo name is a hint, not an answer, and a profile installed under the wrong name is never found.

Check whether the name is taken: `sh ../use/scripts/profile.sh <name>`, relative to this skill's directory, exits 0 when it is. If it is, say so and confirm before overwriting.

## 2. Pick the path

Look at what the user gave you:

- **Profile files:** paths, a folder holding a markdown rules file and a CSS file of custom properties, or a description such as "the ones I just downloaded". Go to step 3.
- **A source to mine:** a theme or token package, a component library, a design-tool export, documentation, or a live site. Go to step 4.
- **Nothing, or a folder that could be either:** ask, and wait:

> Do you have the profile files already, or should I mine them from the design system? Useful sources to mine, best first:
> - a theme or design-token package in a local repo (`packages/theme`, `tokens/`, `themes/`)
> - a component library whose components hardcode the real defaults
> - a design-tool export, such as Figma variables or styles as JSON or CSS
> - design-system documentation: a PDF, a wiki page, or a style guide
> - a live site, as a last resort: its stylesheet gives colors but not intent

## 3. Map the files you were given

- **A folder:** list it and map each file to a role.
- **Paths:** pass them through.
- **A description:** look in the likely places, newest first, and confirm before installing.

      find ~/Downloads ~/Desktop ~/Documents -maxdepth 2 \( -name '*.css' -o -name '*.md' -o -name '*.svg' \) -newermt '-14 days' 2>/dev/null | head -20

Map by content, not name. The tokens file declares custom properties or a `:root` block. The grammar is markdown with `#` headings. The sprite starts with `<svg` and holds `<symbol id=...>` elements. When two files fit one role, or no grammar file is obvious, ask. A wrong file installs cleanly and renders wrong.

Show the mapping before installing, so a bad guess is visible:

    profile -> offerup
    grammar -> ~/Downloads/offerup-grammar.md
    tokens  -> ~/Downloads/tokens (1).css
    icons   -> none found

Then go to step 5.

## 4. Mine a design system

### Pick the source

When several candidates exist, ask which is canonical. A legacy native theme and a current web theme disagree, and mining the deprecated one poisons everything after it. If the source is a repo that isn't cloned or a file you can't read, ask for a path or an export instead of guessing. Ask whether the design system ships an icon set worth including.

### Mine with one subagent per domain

A design system is too large for one context, and its domains are independent. Spawn read-only subagents in parallel, one per domain of the named source:

| Domain | Comes back with |
|---|---|
| color | the palette, the semantic roles (accent, danger, surface, border, text) and the raw hue behind each, and contrast results for text pairs, failures included |
| themes | light and dark values for the same token names, how the system switches, and whether dark really exists |
| geometry | radii, border widths, the spacing scale, and shadow or elevation steps |
| typography | families with real fallbacks, and the size, weight, and line-height ramp |
| motion | durations and easings as constants, and reduced-motion handling |
| components | the defaults that give the system its feel: button heights, form fields, dialogs and cards, table density, empty and loading states, and hover, focus, active, and disabled states |
| voice and icons | sentence or title case, how errors are phrased, punctuation habits, and whether a real icon set exists and how it is referenced |

Give every subagent the same rules:

- Cite a file path and line for every value. A value without a citation is a guess.
- Count usages (`grep -rn "#[0-9a-fA-F]\{6\}" <src> | sort | uniq -c | sort -rn`), but prefer what the theme package exports over what is hardcoded most often. Report near-miss values by name: a hex in eleven files may still not be the canonical color.
- When sources disagree, report both and say which looks canonical and why.
- Report gaps as gaps. Never interpolate a missing scale step or infer a radius.
- Return findings as data, not prose.

Read the findings yourself before writing anything. When two subagents contradict each other, or one cites a source you didn't expect, go look instead of averaging. Spawn a follow-up for a domain that came back thin.

### Write the three files

Write them to a working directory, not into the profile store.

**`tokens.css`**: values only, no usage prose. Open with a comment that cites the source paths and the date mined, so the next person can re-derive it. Carry both themes in the custom properties alone (`:root` for light, redefined under `@media (prefers-color-scheme: dark)` and `[data-theme=...]`), so a page never needs a per-theme rule. Namespace the properties as `--<profile>-...`.

**`grammar.md`**: the rule set, written to be jumped through by heading. Cite the sources at the top. Keep these sections separate:

- the invariants: the few properties that make the system recognizable
- rules per area: color, geometry, typography, motion, state, components, voice, and icons
- where sources disagree, and which one wins
- platform-only rules that must not carry over to a web page
- bugs in the source: things that ship but shouldn't be copied
- tokens the system is missing, so a gap isn't mistaken for an oversight
- a do-not list: the short, blunt version
- unverified: always last. Anything inferred rather than read goes here.

**`icons.svg`**: only if the system has a real set worth carrying. Use `<symbol>` elements with stable ids and `currentColor` fills, so tokens drive them. Ship no sprite rather than a weak one.

One rule outranks completeness: never write a value you didn't read.

## 5. Install it

Run the install script once, relative to this skill's directory, with explicit paths:

    sh scripts/install-profile.sh --profile <name> --grammar <path> --tokens <path> [--icons <path>]

It copies each file to its canonical name, so source filenames don't matter. It installs nothing when a file is missing, empty, a directory, or looks like the wrong role, such as swapped grammar and tokens. Relay its error instead of working around it. A re-install without `--icons` removes the old sprite. It ends by checking that the profile loads.

Then tell the user the profile is ready, and that pages use it by naming it to the `use` skill. Warn that a re-install overwrites the profile's files, so local edits belong in the profile's source.
