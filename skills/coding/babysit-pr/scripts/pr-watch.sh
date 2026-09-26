#!/usr/bin/env bash
# pr-watch.sh <pr> [--merge-only]
# one json object per line, flushed. emits ONLY on change. never a heartbeat.
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
# gh pr view infers owner/name from the cwd; gh api cannot, and the line-comment
# endpoint below is a gh api call. resolve it once, loudly.
REPO_SLUG="$GHREPO"
[[ -n "$REPO_SLUG" ]] || REPO_SLUG="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)"
INTERVAL="${WATCH_INTERVAL:-60}"

PREV="$(mktemp)"; SEEN="$(mktemp)"   # SEEN: ids already reported
trap 'rm -f "$PREV" "$SEEN"' EXIT

now() { date -u +%FT%TZ; }
# every line carries repo and pr, so one Monitor can watch several prs.
emit() {
  printf '{"type":"%s","at":"%s","repo":"%s","pr":"%s"%s}\n' \
    "$1" "$(now)" "$GHREPO" "$PR" "${2:+,$2}"
}
die()  { emit watcher_died "\"reason\":$(jq -Rn --arg v "$1" '$v')"; exit 1; }
seen() { grep -qxF "$1" "$SEEN" 2>/dev/null; }
mark() { echo "$1" >> "$SEEN"; }
p()    { jq -r "$1 // empty" <<<"$2"; }

FIELDS='state,isDraft,mergeStateStatus,reviewDecision,autoMergeRequest,statusCheckRollup,comments,reviews,mergeCommit'

while :; do
  if ! snap="$(gh pr view "$PR" "${GHARGS[@]}" --json "$FIELDS" 2>&1)"; then die "$snap"; fi
  jq -e . <<<"$snap" >/dev/null 2>&1 || die "gh returned non-json: ${snap:0:200}"

  state="$(p .state "$snap")"
  am="$(jq -r '.autoMergeRequest' <<<"$snap")"
  msj="$(p .mergeStateStatus "$snap")"
  prev_am="$(jq -r '.autoMergeRequest // "null"' "$PREV" 2>/dev/null || echo null)"

  # the review requirement, reported on change only. null means the base branch
  # asks for no review, which is NOT the same as approved, so it travels as the
  # empty string and the consumer decides.
  rd="$(p .reviewDecision "$snap")"
  prev_rd="$(jq -r '.reviewDecision // ""' "$PREV" 2>/dev/null || echo "")"
  if [[ -s "$PREV" && "$rd" != "$prev_rd" ]]; then
    emit review_decision "\"decision\":$(jq -Rn --arg v "$rd" '$v')"
  fi

  # line-level review comments live in neither .comments (issue level) nor
  # .reviews[].body. they are their own endpoint, and they are how a human
  # actually reviews a diff, so a watcher without them cannot see a review at
  # all. an empty review body is normal when the substance is all inline, which
  # is why .reviews is no longer filtered on a non-empty body either.
  inline="$(gh api "/repos/$REPO_SLUG/pulls/$PR/comments" --paginate 2>/dev/null \
    | jq -r '.[]? | "r\(.id) \(.user.login//"") \(if (.in_reply_to_id != null) or ((.body//"")|test("-\\s*claude\\s*$")) then "agent" else "human" end) \(.path//"?"):\(.line // .original_line // 0) \(.body // "" | gsub("[\r\n]+"; " "))"')"

  # comments, review bodies and line comments, by id. each source prefixes its
  # own ids so two numbering spaces cannot collide in SEEN.
  while read -r id author agent body; do
    [[ -z "$id" ]] && continue
    seen "$id" && continue
    mark "$id"
    [[ -s "$PREV" ]] || continue          # first pass seeds, never reports history
    if [[ "$MERGE_ONLY" == 0 ]]; then
      emit review_comment "\"author\":$(jq -Rn --arg v "$author" '$v'),\"agent\":$([[ "$agent" == agent ]] && echo true || echo false),\"id\":\"$id\",\"body_preview\":$(jq -Rn --arg v "${body:0:160}" '$v')"
    fi
  # array concat, not a comma inside one [...]: `,` binds tighter than `|` in jq,
  # so a comma-joined pair of generators would feed the second one the first's output.
  done < <( { jq -r '([(.comments // [])[] | {id:("c"+(.id|tostring)),author:(.author.login//""),
                          agent:(if ((.body//"")|test("-\\s*claude\\s*$")) then "agent" else "human" end),body:(.body//"")}]
                    + [(.reviews  // [])[] | {id:("v"+(.id|tostring)),author:(.author.login//""),
                          agent:"human",body:(((.state//"") + " " + (.body//""))|ltrimstr(" "))}])
                    | .[] | "\(.id) \(.author) \(.agent) \(.body | gsub("[\r\n]+"; " "))"' <<<"$snap"
            printf '%s\n' "$inline"; } )

  if [[ "$MERGE_ONLY" == 0 ]]; then
    # failing checks, by check id, transitions only
    while read -r cid name url; do
      [[ -z "$cid" ]] && continue
      seen "f$cid" && continue
      mark "f$cid"
      emit check_failed "\"check\":$(jq -Rn --arg v "$name" '$v'),\"url\":$(jq -Rn --arg v "$url" '$v')"
    done < <(jq -r '(.statusCheckRollup // [])[]
                     | select((.conclusion // .state // "") | test("FAILURE|TIMED_OUT|CANCELLED|ERROR|ACTION_REQUIRED"))
                     | "\(.name // .context)@\(.completedAt // "")|\(.name // .context)|\(.detailsUrl // .targetUrl // "")"' <<<"$snap" \
             | tr '|' ' ')

    allgreen="$(jq -r '((.statusCheckRollup // []) | length) as $n
                       | if $n == 0 then "no" else
                         (if any(.statusCheckRollup[]; ((.conclusion // .state // "") | test("SUCCESS|NEUTRAL|SKIPPED") | not)) then "no" else "yes" end)
                         end' <<<"$snap")"
    if [[ "$allgreen" == yes ]] && ! seen green; then mark green; emit check_passed; fi
    [[ "$allgreen" == no ]] && sed -i '' '/^green$/d' "$SEEN" 2>/dev/null

    if [[ "$am" != null && "$prev_am" == null && -s "$PREV" ]]; then emit automerge_enabled; fi
  fi

  # the stall table
  if [[ -s "$PREV" ]]; then
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
