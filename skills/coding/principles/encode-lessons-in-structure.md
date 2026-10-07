# Encode Lessons in Structure

**Strength order.** From strongest: an unrepresentable state that cannot compile, then a lint or banned API that fails CI, then a canonical helper, then a runtime check. Agents copy whatever the surrounding code already does, so a weaker guard becomes the next template.

**Feedback loop:**
- **Capture every correction.** When the human intervenes or tests fail, decide if it's a one-off or a pattern.
- **Route to the right layer.** One-off -> brain note. Recurring fix -> skill or lint rule. Systemic issue -> principle.
- **Close the loop.** Don't just record. Apply now or create a concrete todo.

**Anti-patterns:**
- Acknowledging without recording ("I'll keep that in mind" does not persist)
- Recording without routing (a brain note about a lint rule that should exist is wasted unless the lint rule gets implemented)
