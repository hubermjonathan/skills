#!/bin/sh
# Usage: attach.sh <pr> <url> [--share-note] [gh flags, such as --repo owner/name]
#        attach.sh <pr> --shared [gh flags]
# Puts a Walkthrough section with the link right below the PR description's disclosure note,
# replacing an earlier one. --share-note asks the author to share the page, on the first
# attach only: once someone deletes the note, it stays gone. --shared deletes the note.
# The description never reaches stdout, so the agent running this never reads it.
set -eu
pr=$1 url=$2
shift 2
body=$(mktemp) out=$(mktemp)
trap 'rm -f "$body" "$out"' EXIT
if [ "$url" = --shared ]; then
  gh pr view "$pr" "$@" --json body --jq .body > "$body"
  awk '
    /^<!-- pr-walkthrough -->$/ { s = 1 }
    s && !NF { held++; next }
    s && /^> \[!IMPORTANT\]/ { held = 0; drop = 1; next }
    drop && /^>/ { next }
    { drop = 0; for (; held; held--) print "" }
    /^<!-- \/pr-walkthrough -->$/ { s = 0 }
    { print }
    END { for (; held; held--) print "" }
  ' "$body" > "$out"
  if cmp -s "$body" "$out"; then echo "$pr has no share note"; exit 0; fi
  gh pr edit "$pr" "$@" --body-file "$out" > /dev/null
  echo "deleted the share note on $pr"
  exit 0
fi
share=0
if [ "${1:-}" = --share-note ]; then share=1; shift; fi
sha=$(gh pr view "$pr" "$@" --json headRefOid --jq '.headRefOid[:7]')
gh pr view "$pr" "$@" --json body --jq .body > "$body"
note=$(awk -v share="$share" '
  /^<!-- pr-walkthrough -->$/ { seen = 1; s = 1 }
  s && /^> \[!IMPORTANT\]/ { kept = 1 }
  /^<!-- \/pr-walkthrough -->$/ { s = 0 }
  END { print (share && (!seen || kept)) ? 1 : 0 }' "$body")
awk -v url="$url" -v sha="$sha" -v note="$note" '
  function section() {
    print "<!-- pr-walkthrough -->"
    print "## Walkthrough"
    print "> [!TIP]"
    print "> 🗺️ **[Walkthrough](" url ")** of `" sha "`: start the review here."
    if (note) {
      print ""
      print "> [!IMPORTANT]"
      print "> The walkthrough may be visible only to its author. Share it with the reviewers, then add the `ready-for-review` label or delete this note."
    }
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
' "$body" > "$out"
gh pr edit "$pr" "$@" --body-file "$out" > /dev/null
echo "attached the walkthrough of $sha to $pr, below the disclosure note$( [ "$note" = 1 ] && echo ', with the share note')"
