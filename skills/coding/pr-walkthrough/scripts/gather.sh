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

# accept a url, owner/repo#number, a #number, or a bare number. the last two
# mean the repo checked out in the current directory.
REPO=""
if [[ "$RAW" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
  REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
  PR="${BASH_REMATCH[3]}"
elif [[ "$RAW" =~ ^([^/#[:space:]]+/[^/#[:space:]]+)#([0-9]+)$ ]]; then
  REPO="${BASH_REMATCH[1]}"
  PR="${BASH_REMATCH[2]}"
else
  PR="${RAW#\#}"
fi
[[ "$PR" =~ ^[0-9]+$ ]] || { echo "could not parse a pr number from: $RAW" >&2; exit 1; }
HERE=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
REPO="${REPO:-$HERE}"
[[ -n "$REPO" ]] || { echo "no repo: pass a pr url or owner/repo#number, or run inside the pr's repo" >&2; exit 1; }
REPO_FLAG="--repo $REPO"
ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
IN_CHECKOUT=""
[[ -n "$ROOT" && "$HERE" == "$REPO" ]] && IN_CHECKOUT=1

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
gh api "repos/$REPO/pulls/$PR/files" --paginate \
  -q '.[] | [.status, .additions, .deletions, .filename] | @tsv' \
  > "$OUT/files.tsv" 2>/dev/null \
  || awk '/^diff --git/{f=$4; sub(/^b\//,"",f); print "modified\t0\t0\t" f}' "$OUT/pr.diff" > "$OUT/files.tsv"

# ---- the diff with the head's line numbers -------------------------------
# so a file:line citation can be read off the page instead of worked out.
python3 - "$OUT/pr.diff" > "$OUT/pr-numbered.diff" <<'PY'
import re, sys
n = 0
for line in open(sys.argv[1], errors="replace"):
    line = line.rstrip("\n")
    m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line)
    if m:
        n = int(m.group(1))
        print(line)
    elif line.startswith(("diff --git", "index ", "--- ", "+++ ", "new file", "deleted file", "similarity", "rename ", "Binary")):
        print(line)
    elif line.startswith("-"):
        print(f"{'':>6} {line}")
    elif line.startswith(("+", " ")):
        print(f"{n:>6} {line}")
        n += 1
    else:
        print(line)
PY

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

# ---- callers outside the diff, on the base branch -----------------------
# one git grep for every declaration and call that the diff adds or removes in
# non-test code, so the walkthrough's blast radius needs no greps of its own.
if [[ -n "$IN_CHECKOUT" ]]; then
  git -C "$ROOT" fetch -q origin "$BASE" 2>/dev/null || true
  python3 - "$OUT" "origin/$BASE" "$ROOT" > "$OUT/callers.tsv" <<'PY'
import collections, re, subprocess, sys
out, ref, root = sys.argv[1:4]
changed = [l.rstrip("\n").split("\t")[3] for l in open(f"{out}/files.tsv") if l.count("\t") == 3]
skip = set("""if for while switch return function catch typeof new super await async yield import require
print assert expect describe test it public private protected static final const let var class interface type
export default void string number boolean String int long Integer Long Boolean Object List Map Set Optional
null true false this self def fn func extends implements readonly abstract override val""".split())
test_path = re.compile(r"(^|/)(tests?|__tests__|spec)/|\.(test|spec)\.[jt]sx?$|Tests?\.(java|kt)$|_test\.(go|py)$")
decl_span = re.compile(r"\b(function|def|class|interface|type|const|let|var|public|private|protected|static|func|fn)\b[^(){=;]*")
ident = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
call = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]{2,})\s*\(")
decl = set()
plus, minus = collections.Counter(), collections.Counter()
path = ""
for l in open(f"{out}/pr.diff", errors="replace"):
    if l.startswith("diff --git"):
        path = l.split(" b/", 1)[-1].strip()
        base = path.rsplit("/", 1)[-1].split(".")[0]
        if not test_path.search(path) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{2,}", base) and base not in ("index", "main", "package"):
            decl.add(base)
        continue
    if l.startswith("@@") and not test_path.search(path):
        for span in decl_span.finditer(l.split("@@", 2)[-1]):
            decl.update(ident.findall(span.group(0)))
        continue
    if l.startswith(("+++", "---")) or not l.startswith(("+", "-")) or test_path.search(path):
        continue
    text = l[1:].strip()
    if text.startswith(("import ", "package ", "from ", "#include", "using ")):
        continue
    for span in decl_span.finditer(text):
        decl.update(ident.findall(span.group(0)))
    (plus if l.startswith("+") else minus).update(call.findall(text))
decl -= skip
calls = {s for s in set(plus) | set(minus) if plus[s] != minus[s]} - skip
syms = sorted(decl | calls, key=lambda s: (-len(s), s))[:80]
print("# symbol\tkind\thits\twhere\ttext")
if not syms:
    sys.exit()
cmd = ["git", "-C", root, "grep", "-n", "-I", "-w", "-F"] + sum((["-e", s] for s in syms), []) + [ref, "--", "."] + [f":(exclude){p}" for p in changed]
lines = subprocess.run(cmd, capture_output=True, text=True, errors="replace").stdout.splitlines()
word = re.compile(r"\b(" + "|".join(map(re.escape, syms)) + r")\b")
hits = collections.defaultdict(list)
for line in lines:
    path, num, text = line[len(ref) + 1:].split(":", 2)
    for s in set(word.findall(text)):
        hits[s].append(f"{path}:{num}\t{text.strip()[:120]}")
for s in syms:
    kind = "both" if s in decl and s in calls else "declaration" if s in decl else "call"
    found = hits.get(s, [])
    if not found:
        print(f"{s}\t{kind}\t0\t-\tnothing outside the diff mentions it")
    elif len(found) > 150:
        print(f"{s}\t{kind}\t{len(found)}\t-\ttoo common to list")
    else:
        for h in found[:10]:
            print(f"{s}\t{kind}\t{len(found)}\t{h}")
PY
else
  echo "# skipped: run gather.sh inside a checkout of $REPO to list callers" > "$OUT/callers.tsv"
fi

# ---- release plumbing the repo expects ----------------------------------
# what sibling commits touching the same directories also changed, so the
# walkthrough can say whether this pr follows the house convention. this reads
# the local checkout, so it only runs inside a checkout of the pr's repo.
{
  if [[ -z "$IN_CHECKOUT" ]]; then
    echo "# skipped: run gather.sh inside a checkout of $REPO to list version files"
  else
    echo "# version manifests / changelogs / changesets present near the changed files"
    cut -f4 "$OUT/files.tsv" | while read -r f; do dirname "$f"; done | sort -u \
      | while read -r d; do
          while [[ "$d" != "." && "$d" != "/" ]]; do
            for candidate in terraform/published.json CHANGELOG.md package.json .changeset; do
              [[ -e "$ROOT/$d/$candidate" ]] && echo "$d/$candidate"
            done
            d=$(dirname "$d")
          done
        done | sort -u
    for candidate in CHANGELOG.md package.json .changeset; do
      [[ -e "$ROOT/$candidate" ]] && echo "$candidate"
    done
  fi
} > "$OUT/release-plumbing.txt" 2>/dev/null

cat <<EOF

gathered:
  $OUT/meta.json             title, author, refs, counts, labels (no body)
  $OUT/pr.diff               the full unified diff
  $OUT/pr-numbered.diff      the same diff with the head's line numbers
  $OUT/files.tsv             status, +, -, path
  $OUT/commit-subjects.txt   author prose, hints only
  $OUT/ticket-key.txt        $(cat "$OUT/ticket-key.txt")
  $OUT/symbols-raw.txt       candidate changed identifiers
  $OUT/callers.tsv           where the base branch mentions each changed name, outside the diff
  $OUT/release-plumbing.txt  version/changelog files that sit above the changed dirs

base: $BASE   head: $HEAD
EOF
