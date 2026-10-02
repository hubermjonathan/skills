---
name: create
description: Build a new design profile by mining a design system for its real values.
disable-model-invocation: true
---

# Create a design profile

A profile is three files that let an HTML page carry a design system honestly:

| file | what it holds |
|---|---|
| `grammar.md` | usage rules — how the design system applies color, type, geometry, motion, state, voice, icons |
| `tokens.css` | values only — CSS custom properties covering both themes |
| `icons.svg` | optional `<symbol>` sprite, referenced with `<use href="#id">` |

Your job is to **mine** those from a real source of truth, not to invent them. A profile whose values
came from taste is worse than no profile, because it looks authoritative while being wrong.

## Step 1 — ask where to mine. Do not skip this.

You cannot guess a design system's source of truth. Ask, and wait for an answer:

> Where should I mine this profile from? Useful sources, best first:
> - a **theme/design-token package** in a local repo (`~/Code/<repo>/packages/theme`, `tokens/`, `themes/`)
> - a **component library** whose components hardcode the real defaults
> - a **design-tool export** — Figma variables/styles as JSON or CSS
> - **design-system documentation** — a PDF, Confluence page, or style guide
> - a **live site**, as a last resort: its stylesheet gives colors but not intent
>
> Also: what should the profile be **named**, and does the design system ship an **icon set** worth including?

Ask which of several candidates is canonical when more than one exists — a legacy native theme and a
current web theme will disagree, and picking the deprecated one silently poisons everything downstream.
If they point at a repo they haven't cloned, or a Figma file you cannot read, say so and ask for a path
or an export rather than substituting a guess.

## Step 2 — mine with subagents, one per domain

A design system is too large to read into one context, and the domains are independent. Fan out
**parallel subagents in a single message**, each read-only, each owning one domain of the source the
person named:

| agent | comes back with |
|---|---|
| color | the palette; *semantic* assignments (accent, danger, surface, border, text) and which raw hue backs each; contrast results for text pairs, failures included |
| themes | light **and** dark values for the same token names; how the system switches; whether dark genuinely exists |
| geometry | radii, border widths, the spacing scale, shadow/elevation steps |
| typography | families with real fallbacks, and the size/weight/line-height ramp |
| motion | durations and easings as constants, plus reduced-motion handling |
| components | the defaults that give the design system its feel: button heights, form field anatomy, dialog and card treatment, table density, empty/loading states, and hover/focus/active/disabled |
| voice + icons | sentence vs title case, how errors are phrased, punctuation habits; whether a real icon set exists and how it is referenced |

Brief every agent identically on the non-negotiables:

- **report file path and line for every value.** A value without a citation is a guess.
- **count usages** — `grep -rn "#[0-9a-fA-F]\{6\}" <src> | sort | uniq -c | sort -rn` — but prefer what
  the theme package *exports* over what is hardcoded most often. A hex in eleven files may still not be
  the canonical color; those near-misses are traps worth reporting by name.
- **when sources disagree**, report both and say which looks canonical and why.
- **report gaps as gaps.** Never interpolate a missing scale step or infer a radius.
- return findings as data, not prose — you are assembling files from them.

Read the returned findings yourself before writing anything. If two agents contradict each other, or one
reports a source you didn't expect to be authoritative, resolve it — go look — rather than averaging.
Spawn a follow-up agent for a domain that came back thin.

## Step 3 — write the three files

**`tokens.css`** — values only, no usage prose. Open with a comment block citing the exact source paths
and the date mined, so the next person can re-derive it. Carry both themes through the custom properties
alone (`:root` for light, redefined under `@media (prefers-color-scheme: dark)` and `[data-theme=…]`), so
a page never needs a per-theme rule of its own. Namespace the properties (`--<profile>-…`).

**`grammar.md`** — the rule set, written to be *jumped through by heading*, not read start to finish.
Include, and separate clearly:

- the invariants — the few properties that make the design system recognisable
- per-area rules: color, geometry, typography, motion, state, components, voice, icons
- **where sources disagree**, and which one wins
- **platform-only rules** that must not be generalised to a web page
- **bugs in the source** — things that ship but should not be copied
- **tokens the system is missing**, so a gap isn't mistaken for an oversight
- a **do-not list** — the short, blunt version
- **genuinely unverified** — end here, always. Anything inferred rather than read goes in this section.

**`icons.svg`** — only if the design system has a real set worth carrying. `<symbol>` elements with stable ids,
`currentColor` for fills so tokens drive them. A profile with no sprite is fully supported; ship none
rather than a weak one.

## Step 4 — honesty rules that outrank completeness

- **Never write a value you did not read.** No interpolated scale steps, no "probably" radii.
- **Cite sources** in `tokens.css` and at the top of `grammar.md`.
- **Never include a token or icon that asserts a claim** — verified, paid tier, promoted, certified,
  rating. A decorative page has no standing to state those about anyone.
- **Say what you could not check.** The unverified section is the feature that makes the rest trustworthy.

## Step 5 — write into the profile store, then verify

Write the files straight to their destination, using the name agreed in step 1:

```sh
mkdir -p ~/.claude/artifact-design-profiles/<name>
```

```
~/.claude/artifact-design-profiles/<name>/
  grammar.md
  tokens.css
  icons.svg     (omit entirely if the design system has no set worth carrying)
```

**Check whether the directory already exists first** —
if it does, you are overwriting someone's profile, so say so and confirm before you do.

Then prove it loads, using the resolver in the sibling `use` skill:

```sh
sh ../use/scripts/profile.sh <name>
```

Exit 0 with the three paths printed means done. Exit 1 means a file is missing or empty — fix it, don't
report success. Then tell the person the profile is ready, and that pages use it by naming it to the
`use` skill.

The `install` skill is for files that already exist somewhere else; you don't need it here.
