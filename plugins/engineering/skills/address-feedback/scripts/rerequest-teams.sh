#!/usr/bin/env bash
# Usage: rerequest-teams.sh <pr> [gh flags, such as --repo owner/name]
# Requests each team again whose review request a review cleared: the team was requested, a review
# came in after, and the team is no longer requested. A team someone removed by hand stays off, and
# an approved PR is left alone. Prints each team it requests.
set -euo pipefail
pr=$1
shift
read -r repo decision pending < <(gh pr view "$pr" "$@" --json url,reviewDecision,reviewRequests \
  --jq '"\(.url | split("/")[3:5] | join("/")) \(.reviewDecision // "" | if . == "" then "NONE" else . end) ,\([.reviewRequests[] | select(.__typename == "Team") | .slug] | join(",")),"')
[[ $decision == APPROVED ]] && exit 0
for team in $(gh api "repos/$repo/issues/$pr/timeline" --paginate --slurp | jq -r 'add | reduce .[] as $e ({};
    if $e.event == "review_requested" and $e.requested_team then .[$e.requested_team.slug] = "requested"
    elif $e.event == "review_request_removed" and $e.requested_team then del(.[$e.requested_team.slug])
    elif $e.event == "reviewed" then map_values(if . == "requested" then "reviewed" else . end)
    else . end) | to_entries[] | select(.value == "reviewed") | .key'); do
  team="${repo%%/*}/$team"
  [[ $pending == *",$team,"* ]] && continue
  gh pr edit "$pr" "$@" --add-reviewer "$team" > /dev/null
  echo "requested $team again on $pr"
done
