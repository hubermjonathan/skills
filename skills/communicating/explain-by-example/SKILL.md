---
name: explain-by-example
description: >
  Explain something already said in more depth by walking through one concrete
  example, step by step. Use when the user asks for more detail on a finding, a
  decision, a bug, or how something works, asks for an example, or says they don't
  follow an explanation.
---

# Explain by example

Walk the user through one concrete case, so they watch it happen instead of reading the rule again.

1. **Find the gap.** Work out the part they didn't follow: the cause, the effect, or why it matters. Answer that part, not the whole topic.
2. **Pick one real example.** Take it from the work at hand: a real PR, file, ticket, command, or log line, with its real names and numbers. Invent one only when no real case fits, and say it's invented.
3. **Walk it in order.** Start from the state before anything happens. Then number each step as it happens: who or what acts, what changes, and what the user would see. Stop at the step where it goes wrong, or where the point lands.
4. **Say what it means.** In one or two sentences, give the consequence and the general rule the example shows.
5. **Tie the fix to the step.** If there is a fix or a decision, name the step where it changes the outcome.

One example, not several. Skip background the user already has.
