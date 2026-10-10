#!/usr/bin/env bash
set -uo pipefail
PR="${1:?usage: pr-watch.sh <pr> [--merge-only] [--repo <owner/name>]}"; shift
MERGE_ONLY=0; GHREPO=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --merge-only) MERGE_ONLY=1;;
    --repo)       GHREPO="${2:-}"; shift;;
  esac
  shift
done
GHARGS=(); [[ -n "$GHREPO" ]] && GHARGS=(--repo "$GHREPO")
INTERVAL="${WATCH_INTERVAL:-60}"
AGENT_NOTE='\A> \[!NOTE\]\r?\n> [^\n]*responding on behalf of'
PR_NUM="$PR"; REPO_SLUG="$GHREPO"

PREV="$(mktemp)"; SEEN="$(mktemp)"
trap 'rm -f "$PREV" "$SEEN"' EXIT

now() { date -u +%FT%TZ; }
emit() {
  printf '{"type":"%s","at":"%s","repo":"%s","pr":"%s"%s}\n' \
    "$1" "$(now)" "$REPO_SLUG" "$PR_NUM" "${2:+,$2}"
}
die()  { emit watcher_died "\"reason\":$(jq -Rn --arg v "$1" '$v')"; exit 1; }
seen() { grep -qxF "$1" "$SEEN" 2>/dev/null; }
mark() { echo "$1" >> "$SEEN"; }
p()    { jq -r "$1 // empty" <<<"$2"; }

FIELDS='state,isDraft,labels,mergeStateStatus,reviewDecision,autoMergeRequest,statusCheckRollup,comments,reviews,mergeCommit,headRefOid'
WRITER='if ((.body // "") | test($note)) then "agent" else "human" end'

read -r PR_NUM REPO_SLUG < <(gh pr view "$PR" "${GHARGS[@]}" --json number,url -q '"\(.number) \(.url | split("/")[3:5] | join("/"))"' 2>/dev/null)
[[ -n "$REPO_SLUG" ]] || die "could not resolve pr $PR"

while :; do
  if ! snap="$(gh pr view "$PR" "${GHARGS[@]}" --json "$FIELDS" 2>&1)"; then die "$snap"; fi
  jq -e . <<<"$snap" >/dev/null 2>&1 || die "gh returned non-json: ${snap:0:200}"

  state="$(p .state "$snap")"
  am="$(jq -r '.autoMergeRequest' <<<"$snap")"
  msj="$(p .mergeStateStatus "$snap")"
  prev_am="$(jq -r '.autoMergeRequest // "null"' "$PREV" 2>/dev/null || echo null)"

  rd="$(p .reviewDecision "$snap")"
  prev_rd="$(jq -r '.reviewDecision // ""' "$PREV" 2>/dev/null || echo "")"
  if [[ -s "$PREV" && "$rd" != "$prev_rd" ]]; then
    emit review_decision "\"decision\":$(jq -Rn --arg v "$rd" '$v')"
  fi

  if [[ -s "$PREV" && "$MERGE_ONLY" == 0 ]]; then
    while read -r label; do
      [[ -n "$label" ]] && emit labeled "\"label\":$(jq -Rn --arg v "$label" '$v')"
    done < <(jq -r --slurpfile prev "$PREV" '((.labels // []) | map(.name)) - (($prev[0].labels // []) | map(.name)) | .[]' <<<"$snap")
  fi

  inline="$(gh api "/repos/$REPO_SLUG/pulls/$PR_NUM/comments" --paginate 2>/dev/null \
    | jq -r --arg note "$AGENT_NOTE" ".[]? | \"r\(.id) \(.user.login//\"\") \($WRITER) \(.path//\"?\"):\(.line // .original_line // 0) \(.body // \"\" | gsub(\"[\r\n]+\"; \" \"))\"")"

  while read -r id author writer body; do
    [[ -z "$id" ]] && continue
    seen "$id" && continue
    mark "$id"
    [[ -s "$PREV" && "$writer" == human ]] || continue
    if [[ "$MERGE_ONLY" == 0 ]]; then
      emit review_comment "\"author\":$(jq -Rn --arg v "$author" '$v'),\"id\":\"$id\",\"body_preview\":$(jq -Rn --arg v "${body:0:160}" '$v')"
    fi
  done < <( { jq -r --arg note "$AGENT_NOTE" "([(.comments // [])[] | {id:(\"c\"+(.id|tostring)),author:(.author.login//\"\"),writer:($WRITER),body:(.body//\"\")}]
                    + [(.reviews  // [])[] | select((.body // \"\") != \"\") | {id:(\"v\"+(.id|tostring)),author:(.author.login//\"\"),writer:($WRITER),body:(((.state//\"\") + \" \" + .body)|ltrimstr(\" \"))}])
                    | .[] | \"\(.id) \(.author) \(.writer) \(.body | gsub(\"[\r\n]+\"; \" \"))\"" <<<"$snap"
            printf '%s\n' "$inline"; } )

  if [[ "$MERGE_ONLY" == 0 ]]; then
    while IFS=$'\t' read -r cid name url; do
      [[ -z "$cid" ]] && continue
      seen "f$cid" && continue
      mark "f$cid"
      emit check_failed "\"check\":$(jq -Rn --arg v "$name" '$v'),\"url\":$(jq -Rn --arg v "$url" '$v')"
    done < <(jq -r '.headRefOid as $sha | (.statusCheckRollup // [])[]
                     | select((.conclusion // .state // "") | test("FAILURE|TIMED_OUT|CANCELLED|ERROR|ACTION_REQUIRED"))
                     | "\(.name // .context)@\($sha)@\(.completedAt // "")\t\(.name // .context)\t\(.detailsUrl // .targetUrl // "")"' <<<"$snap")

    allgreen="$(jq -r '((.statusCheckRollup // []) | length) as $n
                       | if $n == 0 then "no" else
                         (if any(.statusCheckRollup[]; ((.conclusion // .state // "") | test("SUCCESS|NEUTRAL|SKIPPED") | not)) then "no" else "yes" end)
                         end' <<<"$snap")"
    if [[ "$allgreen" == yes ]] && ! seen green; then mark green; emit check_passed; fi
    [[ "$allgreen" == no ]] && sed -i '' '/^green$/d' "$SEEN" 2>/dev/null

    if [[ "$am" != null && "$prev_am" == null && -s "$PREV" ]]; then emit automerge_enabled; fi
  fi

  if [[ -s "$PREV" && "$state" == OPEN ]]; then
    stall=""
    if   [[ "$msj" == DIRTY  ]]; then stall=conflict
    elif [[ "$msj" == BEHIND ]]; then stall=behind_base
    elif [[ "$am" == null && "$prev_am" != null ]]; then stall=automerge_disabled
    elif [[ "$am" != null && "$msj" != BLOCKED ]] \
      && jq -e 'any((.statusCheckRollup // [])[]; ((.conclusion // .state // "") | test("FAILURE|TIMED_OUT|ERROR")))' <<<"$snap" >/dev/null; then
      stall=checks_failing
    fi
    if [[ -n "$stall" ]] && ! seen "s$stall"; then mark "s$stall"; emit merge_blocked "\"reason\":\"$stall\""; fi
    [[ -z "$stall" ]] && sed -i '' '/^s/d' "$SEEN" 2>/dev/null
  fi

  printf '%s' "$snap" > "$PREV"

  case "$state" in
    MERGED) emit pr_merged "\"merge_commit\":$(jq -Rn --arg v "$(p .mergeCommit.oid "$snap")" '$v')"; exit 0;;
    CLOSED) emit pr_closed; exit 0;;
  esac
  sleep "$INTERVAL"
done
