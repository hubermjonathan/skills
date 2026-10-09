#!/bin/sh
# Usage: attach.sh <pr> <url> [gh flags, such as --repo owner/name]
# Puts the walkthrough link at the top of the PR description, replacing an earlier one.
# The description never reaches stdout, so the agent running this never reads it.
set -eu
pr=$1 url=$2
shift 2
sha=$(gh pr view "$pr" "$@" --json headRefOid --jq '.headRefOid[:7]')
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
{
  printf '<!-- pr-walkthrough -->\n> [!TIP]\n> 🗺️ **[Walkthrough](%s)** of `%s`: start the review here.\n<!-- /pr-walkthrough -->\n\n' "$url" "$sha"
  gh pr view "$pr" "$@" --json body --jq .body |
    awk '/^<!-- pr-walkthrough -->$/ { skip = 1 } !skip && (started || NF) { started = 1; print } /^<!-- \/pr-walkthrough -->$/ { skip = 0 }'
} > "$tmp"
gh pr edit "$pr" "$@" --body-file "$tmp" > /dev/null
echo "attached the walkthrough of $sha to the top of $pr"
