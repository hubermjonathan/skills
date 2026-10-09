#!/bin/sh
# Usage: attach.sh <pr> <url> [gh flags, such as --repo owner/name]
# Puts a Walkthrough section with the link right below the PR description's disclosure note,
# replacing an earlier one. The description never reaches stdout, so the agent running this
# never reads it.
set -eu
pr=$1 url=$2
shift 2
sha=$(gh pr view "$pr" "$@" --json headRefOid --jq '.headRefOid[:7]')
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
gh pr view "$pr" "$@" --json body --jq .body |
  awk -v url="$url" -v sha="$sha" '
    function section() {
      print "<!-- pr-walkthrough -->"
      print "## Walkthrough"
      print "> [!TIP]"
      print "> 🗺️ **[Walkthrough](" url ")** of `" sha "`: start the review here."
      print "<!-- /pr-walkthrough -->"
      print ""
      done = 1
    }
    /^<!-- pr-walkthrough -->$/ { skip = 1; next }
    skip { if ($0 == "<!-- /pr-walkthrough -->") { skip = 0; drop = 1 }; next }
    drop && !NF { next }
    { drop = 0 }
    NR == 1 && !/^> \[!NOTE\]/ { section() }
    !done && in_note && !/^>/ { if (!NF) print; section(); in_note = 0; if (!NF) next }
    /^> \[!NOTE\]/ && !done { in_note = 1 }
    { print }
    END { if (!done) section() }
  ' > "$tmp"
gh pr edit "$pr" "$@" --body-file "$tmp" > /dev/null
echo "attached the walkthrough of $sha to $pr, below the disclosure note"
