---
name: create-ticket
description: >
  Draft and create Jira tickets: work tickets, bugs from a Slack or PR thread, and
  change tickets for a prod deploy. Use when the user says "make a ticket", "file a
  ticket", "draft a ticket", "create a change ticket", or asks to capture work for
  someone else to pick up.
---

## Before writing

- Get the project, issue type, and required fields from the tracker's issue type metadata. Never guess field ids.
- Search for an existing ticket on the same problem. If one exists, show it and ask whether to comment there instead.
- For a ticket from a thread, read the whole thread first, not just the linked message.
- Take conventions from the user's instructions and the repo's CLAUDE.md or AGENTS.md: title formats, scheduling fields, sprint, labels. If one is needed and missing, ask.

## Kinds

**Work ticket.** Title says what changes, in plain words. Description: the problem, what is being asked, acceptance criteria. Leave the solution out unless the user wants it prescribed.

**Bug from a thread.** Symptom, evidence (error text, ids, timestamps), and a link to the thread. No speculation about the cause beyond what the thread shows.

**Change ticket for a prod deploy.** One per service, with these fields:

- type `Change`, title `deploy {service} v{version} to prod`
- description: what changed for that service, written with the `brief` skill for a change approver who does not know the codebase. Add the prod promotion PR link.
- change impact description: the same text
- change verified in staging: `Yes`
- planned start date: the next working day at 11:00 local, unless the user gives one
- assignee: the user
- sprint: the team's active sprint, unless the user names one

After creating it, link it to the original ticket, the one the work was for. Find that key in the prod promotion PR's title or description, and ask if there is none or more than one. Add a linked work item on the change ticket so it reads "Is the Release for" the original: link type `Released`, with the original as the inward issue and the change ticket as the outward issue. The original then reads "Is released in" the change ticket. Check the link from the change ticket's side before moving on.

Once created, move it to review if the user asks.

## Rules

- Write every description with the `brief` skill. A reader should get the ask in ten seconds.
- Link every blocked and blocking ticket you know of. Ask if the relationship is unclear.
- Show the draft (type, title, fields, description) and create only after the user confirms, unless they already said to create it.
- If a create fails with a permission error on one Atlassian tool, try the other connected Atlassian tool before giving up.
- Reply with the ticket link and nothing else.
