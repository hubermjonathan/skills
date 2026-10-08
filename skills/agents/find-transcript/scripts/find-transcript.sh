#!/usr/bin/env bash
set -uo pipefail

if [ -n "${TRANSCRIPT_DIRS:-}" ]; then
	IFS=: read -r -a stores <<<"$TRANSCRIPT_DIRS"
else
	stores=(
		"$HOME/.claude/projects"
		"$HOME/.codex/sessions"
		"$HOME/.cursor/projects"
	)
fi

if [ "${1:-}" = --stores ]; then
	(IFS=:; printf '%s\n' "${stores[*]}")
	exit 0
fi

phrase="${1:?usage: find-transcript.sh \"<phrase>\" [days] | --stores}"
days="${2:-2}"

dirs=("${stores[@]}")
if [ -z "${TRANSCRIPT_DIRS:-}" ]; then
	encoded="$(printf '%s' "$PWD" | tr '/.' '--')"
	dirs=("$HOME/.claude/projects/$encoded" "${dirs[@]}")
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
