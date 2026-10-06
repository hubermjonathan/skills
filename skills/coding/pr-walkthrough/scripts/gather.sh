#!/usr/bin/env bash
# gather everything a pr walkthrough needs, from the diff and repo only.
#
# deliberately does NOT fetch the pr body, review comments, or issue comments.
# the walkthrough describes what the code does, not what the author said it does.
#
# usage: gather.sh <pr-number-or-url> [out-dir]
set -uo pipefail

RAW="${1:?usage: gather.sh <pr-number-or-url> [out-dir]}"
OUT="${2:-}"

# accept a url, a #number, or a bare number
REPO_FLAG=""
if [[ "$RAW" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
  REPO_FLAG="--repo ${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  PR="${BASH_REMATCH[3]}"
else
  PR="${RAW#\#}"
fi
[[ "$PR" =~ ^[0-9]+$ ]] || { echo "could not parse a pr number from: $RAW" >&2; exit 1; }

if [[ -z "$OUT" ]]; then
  OUT="${TMPDIR:-/tmp}/pr-walkthrough-$PR"
fi
mkdir -p "$OUT" || exit 1

echo "out: $OUT"

# ---- metadata. no `body`, no comments, on purpose -----------------------
gh pr view "$PR" $REPO_FLAG --json \
  number,title,url,author,state,isDraft,baseRefName,headRefName,headRefOid,additions,deletions,changedFiles,labels,createdAt \
  > "$OUT/meta.json" || { echo "gh pr view failed" >&2; exit 1; }

# ---- the diff, and a per-file table ------------------------------------
gh pr diff "$PR" $REPO_FLAG > "$OUT/pr.diff"

BASE=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["baseRefName"])' "$OUT/meta.json")
HEAD=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["headRefOid"])' "$OUT/meta.json")

# numstat with rename/status, from the diff itself so it works without a fetch
gh api "repos/{owner}/{repo}/pulls/$PR/files" --paginate \
  -q '.[] | [.status, .additions, .deletions, .filename] | @tsv' \
  > "$OUT/files.tsv" 2>/dev/null \
  || awk '/^diff --git/{f=$4; sub(/^b\//,"",f); print "modified\t0\t0\t" f}' "$OUT/pr.diff" > "$OUT/files.tsv"

# ---- commit subjects -----------------------------------------------------
# author prose. useful only as a hint about file grouping; never a source of
# truth for what the code does.
gh pr view "$PR" $REPO_FLAG --json commits \
  -q '.commits[] | .messageHeadline' > "$OUT/commit-subjects.txt" 2>/dev/null || true

# ---- ticket key, from the title and branch only -------------------------
# the body is off limits, so the key has to come from somewhere the author
# could not bury an instruction in.
python3 - "$OUT/meta.json" > "$OUT/ticket-key.txt" <<'PY'
import json, re, sys
m = json.load(open(sys.argv[1]))
hay = f"{m.get('title','')} {m.get('headRefName','')}"
keys = re.findall(r'\b([A-Z][A-Z0-9]{1,9}-\d+)\b', hay.upper())
print(keys[0] if keys else "")
PY

# ---- changed symbols -----------------------------------------------------
# added/removed declarations, for the blast-radius grep below. intentionally
# crude and language-agnostic: it over-collects, and the caller filters.
grep -hE '^[+-]' "$OUT/pr.diff" \
  | grep -vE '^(\+\+\+|---)' \
  | grep -ohE '\b(function|def|class|interface|type|const|let|var|public|private|protected|static|func|fn)\b[^(){=;]*' \
  | grep -ohE '[A-Za-z_][A-Za-z0-9_]{2,}' \
  | sort -u > "$OUT/symbols-raw.txt"

# ---- release plumbing the repo expects ----------------------------------
# what sibling commits touching the same directories also changed, so the
# walkthrough can say whether this pr follows the house convention.
{
  echo "# version manifests / changelogs / changesets present near the changed files"
  cut -f4 "$OUT/files.tsv" | while read -r f; do dirname "$f"; done | sort -u \
    | while read -r d; do
        while [[ "$d" != "." && "$d" != "/" ]]; do
          for candidate in terraform/published.json CHANGELOG.md package.json .changeset; do
            [[ -e "$d/$candidate" ]] && echo "$d/$candidate"
          done
          d=$(dirname "$d")
        done
      done | sort -u
} > "$OUT/release-plumbing.txt" 2>/dev/null

cat <<EOF

gathered:
  $OUT/meta.json             title, author, refs, counts, labels (no body)
  $OUT/pr.diff               the full unified diff
  $OUT/files.tsv             status, +, -, path
  $OUT/commit-subjects.txt   author prose, hints only
  $OUT/ticket-key.txt        $(cat "$OUT/ticket-key.txt")
  $OUT/symbols-raw.txt       candidate changed identifiers, for a blast-radius grep
  $OUT/release-plumbing.txt  version/changelog files that sit above the changed dirs

base: $BASE   head: $HEAD
EOF
