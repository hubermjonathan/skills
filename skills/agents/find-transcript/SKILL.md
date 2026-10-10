---
name: find-transcript
description: >
  Find this session's transcript file, or list where agents keep session transcripts.
  Use when a skill or task needs the full record of the current session, or needs to
  read past sessions.
---

# Find a transcript

Each agent keeps its session transcripts in a session store. `scripts/find-transcript.sh`, relative to this skill's directory, holds the stores it knows. To search others, set `TRANSCRIPT_DIRS` to their directories, colon-separated.

## This session's transcript

    scripts/find-transcript.sh "<a distinctive phrase from this conversation's first user message>" [days]

It searches session files changed in the last `days`, 2 by default, newest first, and prints the first one that holds the phrase. It prints nothing from any other session. When nothing matches it exits 1: set `TRANSCRIPT_DIRS` to your agent's session store if you know it, and retry. If it still finds nothing, tell the caller the transcript is out of reach.

## The session stores

    scripts/find-transcript.sh --stores

It prints every store on one colon-separated line, ready to pass as `TRANSCRIPT_DIRS`.
