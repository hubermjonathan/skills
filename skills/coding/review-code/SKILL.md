---
name: review-code
description: >
  Review a pull request or diff against the ticket that asked for it, then optionally
  address the findings. Use when the user says "review this pr", "review my
  changes", "code review", or "check this against the ticket".
---

Review what was asked for against what was built.

1. Get the ask: the ticket linked in the PR body, title, or branch. With no ticket, use the PR description.
2. Get the diff live from git: `git fetch`, then `git diff origin/<base>...<head>`. Not `gh pr diff`.
3. Read the review already on the PR, from humans and automated reviewers: invoke the `comment-pr` skill for where it lives. Their points are findings on equal footing with yours. Deduplicate.
4. Review for:
   - ticket compliance: every ask addressed, nothing extra built
   - correctness: bugs, broken edge cases, wrong assumptions
   - simplicity: a smaller way to get the same result
5. Back every finding by reading the code. Drop what you cannot back.
6. Stay blind when reviewing your own work: judge against the ticket and the diff, not your plan or your reasons. Subagent prompts may quote the ticket and the diff but never your theories about the intended design.
7. When the user wants several independent reviewers, or says "consensus review", "swarm review", or "N reviewers", invoke the `swarm` skill. Frame it as a race of N reviewers (default 3) on identical, blind briefs: the ticket text and the diff command, plus steps 4 and 5 of this skill, and nothing about intended design. Use the `majority` selection rule, then back each surviving finding yourself with step 5 before reporting it.

## Output

Findings ranked most severe first. Each one: `file:line`, what is wrong, a concrete failure scenario, the suggested fix, and its source (you or a named reviewer).

## Addressing findings

Only when the user asks, or when the PR is the user's own and they want it fixed:

- Fix what is worth fixing with the smallest change. Decline the rest with a reason.
- Write every finding and its outcome to `.scratch/<pr-number>-review.md`.
- Before committing and pushing, invoke the `git` skill.

Never post review comments, approve, or request changes unless the user asks.
