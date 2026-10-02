---
name: create-change-ticket
description: >
  Create the Jira change ticket for a prod deploy, one per service, linked to the
  ticket the work was for. Use when a service is going to prod and needs its
  change ticket, or when asked to create or draft a change ticket.
---

## Before writing

- Get the project, issue type, and required fields from the tracker's issue type metadata. Never guess field ids.
- Search for an existing change ticket titled `deploy {service} v{version} to prod`. If one exists, show it and ask whether to use it instead.
- Take conventions from the user's instructions and the repo's CLAUDE.md or AGENTS.md: scheduling fields, sprint, labels. If one is needed and missing, ask.

## Fields

One ticket per service:

- type `Change`, title `deploy {service} v{version} to prod`
- description: what changed for that service, written with the `brief` skill for a change approver who does not know the codebase. Add the prod promotion PR link.
- change impact description: the same text
- change verified in staging: `Yes`
- planned start date: the next working day at 11:00 local, unless the user gives one
- assignee: the user
- sprint: the team's active sprint, unless the user names one

## Link the original ticket

After creating it, link it to the original ticket, the one the work was for. Find that key in the prod promotion PR's title or description, and ask if there is none or more than one. Add a linked work item on the change ticket so it reads "Is the Release for" the original: link type `Released`, with the original as the inward issue and the change ticket as the outward issue. The original then reads "Is released in" the change ticket. Check the link from the change ticket's side before moving on.

## Rules

- Show the draft (title, fields, description) and create only after the user confirms, unless they already said to create it.
- If a create fails with a permission error on one Atlassian tool, try the other connected Atlassian tool before giving up.
- Once created, move it to review if the user asks.
- Reply with the ticket link and nothing else.
