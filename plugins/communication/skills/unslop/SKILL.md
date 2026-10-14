---
name: unslop
description: >
  Cut AI writing tells from prose a person outside the session reads: PR bodies,
  tickets, Slack messages, and docs. Use on that prose, or when asked to make text
  sound less like AI.
---

# Unslop

Edit text to remove AI patterns. Word and sentence rules, such as plain words, active voice, sentence length, and punctuation, live in the `technical-writing` skill. This catalog holds only the tells that skill doesn't cover.

## Process

1. Scan for the patterns below.
2. Rewrite. Preserve meaning, match intended tone.
3. Self-audit: "What makes this obviously AI generated?" Fix remaining tells.

## Patterns to detect and fix

### Content

1. **Vague attributions.** "Experts believe", "Industry reports suggest", "Some critics argue". Name the source or delete.

### Language

2. **AI vocabulary.** Additionally, crucial, delve, enduring, enhance, fostering, garner, interplay, intricate, landscape (abstract), pivotal, showcase, tapestry (abstract), testament, underscore, vibrant. Replace with plain words.
3. **Fancy ways to say "is".** "serves as", "stands as", "boasts", "features". Just say "is" or "has".
4. **"Not just X, but Y."** State the point directly instead.
5. **Rule of three.** Forcing ideas into groups of three. Use the natural number.
6. **False ranges.** "from X to Y" where X and Y aren't on a meaningful scale. List topics directly.

### Style

7. **Boldface overuse.** Don't bold every proper noun or acronym.
8. **Inline-header lists.** The tell is a bold label and colon that restates the line: "**Performance:** Performance improved...". Convert those to prose. A bold lead-in that ends in a period, names the item, and is followed by genuinely new detail ("**Schema in TypeScript.** Tables live in one file.") is fine, not a tell.
9. **Decorative emojis.** Remove from headings and bullets.
10. **Curly quotes.** Replace with straight quotes.

### Communication artifacts

11. **Chatbot phrases.** "I hope this helps!", "Let me know if...", "Of course!", "Certainly!", "Found the smoking gun!" Remove.
12. **Sycophantic tone.** "Great question! You're absolutely right!" Respond directly.

### Filler

13. **Excessive hedging.** "could potentially possibly be argued that it might" becomes "may".
14. **Generic conclusions.** "The future looks bright." State specific plans or facts.
