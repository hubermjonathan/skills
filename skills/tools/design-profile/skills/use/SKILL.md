---
name: use
description: >
  Style a self-contained HTML page with a named design profile: its grammar, design
  tokens, and icon sprite. Use when building, editing, or reviewing an HTML page or
  artifact that should follow a design profile. Requires the profile name.
---

# Use a design profile

A profile is a mined design system: usage rules, design tokens, and an optional icon sprite. Resolve it before writing markup, so the tokens shape the page instead of being added after.

## 1. Resolve the profile

Take the profile name from the request. If there is none, list the installed profiles and ask which to use. Never pick one yourself.

    sh scripts/profile.sh <name>

It prints the paths to the profile's files. Act on its exit code:

- **0**: resolved. Go on to step 2.
- **1**: not installed, or a file is missing. It lists what is installed. Say which profile was asked for and stop. Never fall back to another profile. The user adds one with `design-profile:install`, or builds one with `design-profile:create`.
- **2**: no name given. It lists what is installed. Ask which to use.

## 2. Build the page

1. Read the profile's `grammar.md`. It is the rule set, and it wins over this skill. It is large, so jump by its headings.
2. Inline `tokens.css` in full in a `<style>` tag. Never retype or summarize its values, and never write a raw value where a token exists.
3. Add the light and dark toggle the tokens file defines, if it has one, starting in the mode it specifies.
4. Add a page container. Component libraries rarely define one.
5. Paste `icons.svg` only if the page earns an icon. The default is none: before adding one, delete it, and if nothing is lost, keep it deleted.
6. Check the page against the grammar's do-not list. Respect `prefers-reduced-motion` and keep keyboard focus visible.

## When the grammar is silent

- Never use a token or icon that asserts a claim: paid tier, verified, promoted, certified, or rating. A decorative page has no standing to state those. A word is honest, a borrowed badge is not.
- A grammar ends with what couldn't be verified when it was mined. Don't present those values as confirmed.
