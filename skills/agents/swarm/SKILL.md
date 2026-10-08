---
name: swarm
description: >
  Fan out N parallel workers, drain them, and return one report. Use for multi-
  reviewer code review, parallel coverage of separate slices, races on the same
  brief, or parallel exploration, and when another skill needs parallel workers.
---

# Swarm

Fan out N parallel workers. They may cover separate slices, race the same brief, or mix both. The parent waits, aggregates, and returns one report.

## Start

Track one todo per phase before launching anything: Frame, Fan out, Aggregate, Report.

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare the selection rule before spawning:
   - `first pass`: the first worker to report PASS wins
   - `rank all`: score every result and order them
   - `best-of`: pick one result
   - `majority`: keep a finding only when more than half the workers report it independently
3. Set N from the user, from the calling skill, or from the shape. N is total workers.
4. Pick the worker model. By default workers inherit the parent's model. For a race where diverse judgment matters, spread them across the models your agent offers, and name each worker's model up front.
5. Give each writing worker its own output: a git worktree, or its own directory. Never two workers on one file. When workers verify or measure commits, each brief names the exact SHAs. A measurement brief also names the method (sample count, what one sample is, order), and the worker records both in its result.

## Phase B: Fan out

Spawn all N workers at once as background subagents, in one batch, so they run in parallel. Writing workers each get their own git worktree. If your agent cannot run subagents in parallel, run them one after another, each in a fresh context, and note that in the report.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence. A worker that can prove a defect reports `ISSUES` and lists every issue it can prove, not only the first.

In a race, briefs are identical and blind: no worker sees another's output or the parent's theory.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read the terminal results. Drop a result that does not record the SHAs and method its brief names, and rerun that worker once. After a second miss, record a gap. A gap does not count as a pass. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated report with the table, issue one-liners, gaps or dropouts, and the selection rule when one was used.
