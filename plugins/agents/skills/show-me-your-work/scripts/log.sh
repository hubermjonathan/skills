#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 7 ]; then
	printf 'usage: log.sh <logfile> <run> <phase> <decision> <why> <evidence> <result>\n' >&2
	printf 'Pass new as <run> on a run'"'"'s first row. log.sh prints the id to pass on its later rows.\n' >&2
	exit 1
fi

logfile="$1"
run="$2"
shift 2

mkdir -p "$(dirname "$logfile")"

if [ ! -s "$logfile" ]; then
	printf 'ts\trun\tphase\tdecision\twhy\tevidence\tresult\n' >> "$logfile"
fi

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
[ "$run" = new ] && run="${ts//[-:]/}"
spreadsheet_safe() {
	local v
	v=$(printf '%s' "$1" | tr '\t\n\r' '   ')
	case "$v" in
		=*|+*|-*|@*) printf "'%s" "$v" ;;
		*) printf '%s' "$v" ;;
	esac
}
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
	"$ts" "$(spreadsheet_safe "$run")" "$(spreadsheet_safe "$1")" "$(spreadsheet_safe "$2")" "$(spreadsheet_safe "$3")" "$(spreadsheet_safe "$4")" "$(spreadsheet_safe "$5")" \
	>> "$logfile"
printf '%s\n' "$run"
