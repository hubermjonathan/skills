#!/bin/sh
# Usage: attach.sh <pr> <url> <sha> [--share-note] [gh flags, such as --repo owner/name]
#        attach.sh <pr> --shared [gh flags]
#        attach.sh <pr> --url [gh flags]
# Puts a Walkthrough section with the link and <sha>, the commit the page shows, right below the
# PR description's disclosure note, or at the top when there is none, replacing an earlier one.
# --share-note asks the author to share the page. The note appears on the first attach and stays
# on later ones that pass the flag. Once someone deletes it, it stays gone. --shared deletes it.
# --url prints the link of the walkthrough already attached, or nothing.
# The rest of the description never reaches stdout, so the agent running this never reads it.
set -eu
pr=$1 url=$2
shift 2
share=0
case $url in
  --url | --shared) ;;
  *)
    sha=$(printf %.7s "${1:?usage: attach.sh <pr> <url> <sha> [--share-note] [gh flags]}")
    shift
    if [ "${1:-}" = --share-note ]; then share=1; shift; fi
    ;;
esac
raw=$(mktemp) body=$(mktemp) out=$(mktemp)
trap 'rm -f "$raw" "$body" "$out"' EXIT
gh pr view "$pr" "$@" --json body --jq .body > "$raw"
awk '{ sub(/\r$/, "") } 1' "$raw" > "$body"

bounds='
  pass == 1 {
    if (/^ *(```|~~~)/) fence = !fence
    else if (fence || e) {}
    else if ($0 == "<!-- pr-walkthrough -->") { s = FNR; kept = 0 }
    else if ($0 == "<!-- /pr-walkthrough -->") { if (s) e = FNR }
    else if (s && /^> \[!IMPORTANT\]/) kept = 1
    next
  }
  { in_s = e && FNR >= s && FNR <= e }
'
edit() {
  awk 'NR > 1 { printf "\n" } { printf "%s", $0 }' "$out" | gh pr edit "$pr" "$@" --body-file - > /dev/null
}

if [ "$url" = --url ]; then
  awk "$bounds"'
    in_s && match($0, /\*\*\[Walkthrough\]\([^)]*\)\*\*/) { print substr($0, RSTART + 16, RLENGTH - 19); exit }
  ' pass=1 "$body" pass=2 "$body"
  exit 0
fi

if [ "$url" = --shared ]; then
  if [ "$(awk "$bounds"' END { print (e && kept) ? 1 : 0 }' pass=1 "$body")" = 0 ]; then
    echo "$pr has no share note"
    exit 0
  fi
  awk "$bounds"'
    in_s && !NF { held++; next }
    in_s && /^> \[!IMPORTANT\]/ { held = 0; drop = 1; next }
    drop && /^>/ { next }
    { drop = 0; for (; held; held--) print "" }
    { print }
    END { for (; held; held--) print "" }
  ' pass=1 "$body" pass=2 "$body" > "$out"
  edit "$@"
  echo "deleted the share note on $pr"
  exit 0
fi

note=$(awk "$bounds"' END { print (share && (!e || kept)) ? 1 : 0 }' share="$share" pass=1 "$body")
awk "$bounds"'
  function section() {
    print "<!-- pr-walkthrough -->"
    print "## Walkthrough"
    print "> [!TIP]"
    print "> 🗺️ **[Walkthrough](" url ")** of `" sha "`: start the review here."
    if (note) {
      print ""
      print "> [!IMPORTANT]"
      print "> The walkthrough may be visible only to its author. Share it with the reviewers, with comment access, then add the `ready-for-review` label or delete this note."
    }
    print "<!-- /pr-walkthrough -->"
    print ""
    done = 1
  }
  in_s { drop = FNR == e; next }
  drop && !NF { next }
  { drop = 0 }
  !started++ && !/^> \[!NOTE\]/ { section() }
  !done && in_note && !/^>/ { if (!NF) print; section(); in_note = 0; if (!NF) next }
  /^> \[!NOTE\]/ && !done { in_note = 1 }
  { print }
  END { if (!done) section() }
' url="$url" sha="$sha" note="$note" pass=1 "$body" pass=2 "$body" > "$out"
edit "$@"
echo "attached the walkthrough of $sha to $pr$( [ "$note" = 1 ] && echo ', with the share note')"
