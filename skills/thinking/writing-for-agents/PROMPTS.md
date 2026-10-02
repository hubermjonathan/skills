# Prompts for subagents and sessions

The prompt branch of [`writing-for-agents`](SKILL.md): what changes when the document is a prompt handed to a subagent, a workflow agent, or another session. Everything else about writing it is the universal reference in `SKILL.md`.

A prompt differs from a skill in two ways. Its reader starts **cold**, knowing nothing you have not written down. And it is read **once**, in full, rather than sitting in context behind a pointer. So descriptions, invocation, and router skills do not apply, and the context-load arithmetic changes: the cost is the prompt's length against the reader's window, plus whatever the reader sends back into yours.

What carries over unchanged: completion criteria, leading words, prompting the positive, pruning, and pointing at files instead of pasting them. Splitting by sequence works better here than anywhere, because a subagent or a new session is a real context boundary: hand out one stage, and the later ones cannot pull the reader forward.

## The cold reader

Write everything the reader needs to act, and nothing it can look up itself.

- **Goal and why.** What done looks like, and the reason behind it. A reader that knows the why makes the right call on cases the prompt did not foresee.
- **What is already known.** What was tried, what failed, what is settled. A reader without it re-litigates decisions or repeats a dead end.
- **Exact handles.** Ids, paths, branch names, environments, ticket keys, PR numbers. Never "the PR we discussed".
- **Pointers over pastes.** Name the file and say when to read it. Paste only what the reader cannot reach.

The test: a new engineer handed only this text could do the work. If they would have to ask a question, answer it in the prompt.

## The return contract

For a subagent or workflow agent, what it returns lands in your context. Name the shape every time:

- what to return: conclusions, findings, a verdict, a file path
- the format: a list, a schema, `file:line` citations
- the bound: a word limit, or "only confirmed findings"

With no stated shape, the default is under 300 words with a `file:line` citation for every claim about code. Ask for conclusions, never raw file dumps or logs. When the output is large, have the reader write it to a file and return the path.

## Neutral framing

A prompt that states your theory gets your theory confirmed. When the reader is checking, reviewing, or verifying:

- quote the source material (the ticket, the diff, the error) and ask the question
- leave out your hypothesis about the cause or the intended design. "Verify the retry path handles 429s correctly" smuggles in a conclusion. "Report how this diff behaves on each status code the client can return" does not.
- when several readers review the same thing independently, give each the same material and none of the others' findings

## Authority and limits

Say what the reader may do and where its work goes:

- actions it may take (edit, commit, push, post, merge) and any it must not
- where it writes, as absolute paths
- when to stop and report instead of pressing on: a wrong plan, a failing precondition, a decision that belongs to a human

## Session prompts

A prompt for another session, one the user will drive, carries extra duties:

- **Who acts, and when to wait.** Mark which steps the session does and which need the user. When the user must act (log in, click, trigger), the session says exactly what to do and waits for their word.
- **Setup is prompted, never assumed.** If the work needs accounts, data, or config, the session walks the user through it rather than assuming an earlier session did it.
- **Progress survives interruption.** The session appends each result to a file as it goes, so a crash or a closed terminal loses nothing.
- **Standalone.** The session reads only this prompt, so everything from "The cold reader" applies in full.

## Handing off a session prompt

When the user asks for a prompt for a new session:

1. Write it to `.scratch/<slug>-prompt.md` at the repo root.
2. No frontmatter and no preamble about what the file is. The first line is the first instruction.
3. Reply with the file path only, so the user can start the new session with "follow the instructions in <path>".
