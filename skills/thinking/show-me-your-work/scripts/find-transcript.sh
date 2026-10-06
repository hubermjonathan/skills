#!/usr/bin/env bash
set -uo pipefail

phrase="${1:?usage: find-transcript.sh \"<phrase>\" [days]}"
days="${2:-2}"

encoded="$(printf '%s' "$PWD" | tr '/.' '--')"
if [ -n "${TRANSCRIPT_DIRS:-}" ]; then
	IFS=: read -r -a dirs <<<"$TRANSCRIPT_DIRS"
else
	dirs=(
		"$HOME/.claude/projects/$encoded"
		"$HOME/.claude/projects"
		"$HOME/.codex/sessions"
		"$HOME/.cursor/projects"
	)
fi

for d in "${dirs[@]}"; do
	[ -d "$d" ] || continue
	hit="$(find "$d" -type f -name '*.jsonl' -mtime "-$days" -print0 2>/dev/null \
		| xargs -0 ls -t 2>/dev/null \
		| while read -r f; do grep -lF -- "$phrase" "$f" 2>/dev/null && break; done)"
	if [ -n "$hit" ]; then
		printf '%s\n' "$hit"
		exit 0
	fi
done
exit 1
