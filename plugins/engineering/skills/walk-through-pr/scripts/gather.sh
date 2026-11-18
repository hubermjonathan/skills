#!/usr/bin/env bash
set -uo pipefail

RAW="${1:?usage: gather.sh <pr-number-or-url> [out-dir]}"
OUT="${2:-}"

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
[[ "$PR" =~ ^[0-9]+$ ]] || { echo "could not parse a PR number from: $RAW" >&2; exit 1; }
REPO="${REPO:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)}"
ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
REMOTE=$(git remote -v 2>/dev/null | awk -v r="$REPO" '$3 == "(fetch)" && tolower($2) ~ ("[/:]" tolower(r) "(\\.git)?/?$") { print $1; exit }')
[[ -n "$REPO" && -n "$ROOT" && -n "$REMOTE" ]] || {
  echo "run gather.sh inside a checkout of ${REPO:-the PR repo}: it reads callers and the code pane files from there" >&2
  exit 1
}

OUT="${OUT:-${TMPDIR:-/tmp}/pr-walkthrough-${REPO//\//-}-$PR}"
mkdir -p "$OUT" || exit 1
rm -rf "$OUT/head" "$OUT/base"
echo "out: $OUT"

gh pr view "$PR" --repo "$REPO" --json \
  number,title,url,author,state,isDraft,baseRefName,headRefName,headRefOid,mergeCommit,labels,createdAt \
  > "$OUT/meta.json" || { echo "gh pr view failed" >&2; exit 1; }
gh pr diff "$PR" --repo "$REPO" > "$OUT/pr.diff" || { echo "gh pr diff failed" >&2; exit 1; }
gh api "repos/$REPO/pulls/$PR/files" --paginate -q '.[] | [.status, .additions, .deletions, .filename] | @tsv' \
  > "$OUT/files.tsv" || { echo "gh api pulls/$PR/files failed" >&2; exit 1; }
gh pr view "$PR" --repo "$REPO" --json commits -q '.commits[] | .messageHeadline' > "$OUT/commit-subjects.txt" 2>/dev/null || true

read -r BASE HEAD MERGE < <(python3 -c 'import json,sys;m=json.load(open(sys.argv[1]));print(m["baseRefName"],m["headRefOid"],(m["state"]=="MERGED" and (m.get("mergeCommit") or {}).get("oid")) or "-")' "$OUT/meta.json")
if [[ "$MERGE" != - ]]; then
  { git -C "$ROOT" fetch -q --no-write-fetch-head "$REMOTE" "$MERGE" || git -C "$ROOT" cat-file -e "$MERGE^{commit}"; } \
    && BASE_OID=$(git -C "$ROOT" rev-parse "$MERGE^1") && BASE_WHAT="$BASE just before the merge"
else
  OID=$(git -C "$ROOT" ls-remote "$REMOTE" "refs/heads/$BASE" | cut -f1) && [[ -n "$OID" ]] \
    && git -C "$ROOT" fetch -q --no-write-fetch-head "$REMOTE" "$OID" && BASE_OID=$OID && BASE_WHAT="$BASE"
fi
[[ -n "${BASE_OID:-}" ]] || { echo "could not fetch the base from $REMOTE" >&2; exit 1; }
git -C "$ROOT" fetch -q --no-write-fetch-head "$REMOTE" "pull/$PR/head" 2>/dev/null || git -C "$ROOT" cat-file -e "$HEAD^{commit}" \
  || { echo "could not fetch the PR head $HEAD from $REMOTE" >&2; exit 1; }

python3 - "$OUT" "$BASE_OID" "$HEAD" "$ROOT" <<'PY'
import collections, json, os, re, subprocess, sys
out, base, head, root = sys.argv[1:5]

meta = json.load(open(f"{out}/meta.json"))
meta["baseOid"] = base
json.dump(meta, open(f"{out}/meta.json", "w"), indent=1)

rows = [l.rstrip("\n").split("\t") for l in open(f"{out}/files.tsv") if l.count("\t") == 3]
changed = [r[3] for r in rows]
test_path = re.compile(r"(^|/)(tests?|__tests__|__fixtures__)/|\.(test|spec)\.[jt]sx?$|Tests?\.(java|kt)$|_test\.(go|py)$|(^|/)test_[^/]*\.py$")

def diff_path(header):
    return max((p for p in changed if header.endswith(" b/" + p)), key=len, default=header.split(" b/", 1)[-1])

diff = open(f"{out}/pr.diff", errors="replace", newline="").read().removesuffix("\n").split("\n")
with open(f"{out}/pr-numbered.diff", "w") as numbered:
    new = old = 0
    hunk = False
    for line in diff:
        line = line.rstrip("\r")
        m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)", line)
        if line.startswith("diff --git "):
            hunk = False
        elif m:
            old, new, hunk = int(m.group(1)), int(m.group(2)), True
        elif hunk and line[:1] == "-":
            line = f"{new or old:>6} {line}"
            old += 1
        elif hunk and line[:1] in ("+", " "):
            old += line[:1] == " "
            line = f"{new:>6} {line}"
            new += 1
        print(line, file=numbered)

skip = set("""if for while switch return function catch typeof new super await async yield import require
print assert expect describe test it public private protected static final const let var class interface type
export default void string number boolean String int long Integer Long Boolean Object List Map Set Optional
null true false this self def fn func extends implements readonly abstract override val enum struct""".split())
decl_span = re.compile(r"\b(function|def|class|interface|type|enum|const|let|var|public|private|protected|static|func|fn)\b[^(){=;:]*")
ident = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
call = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]{2,})\s*\(")
decl, enclosing, renamed = set(), set(), set()
plus, minus = collections.Counter(), collections.Counter()

def declared(text):
    for span in decl_span.finditer(text):
        names = [n for n in ident.findall(re.split(r"\b(?:extends|implements)\b", span.group(0))[0]) if n not in skip]
        yield from names[-1:]

def code(line):
    text = re.sub(r"\s(//|#)\s.*$", "", line.strip())
    return "" if text.startswith(("import ", "package ", "from ", "using ", "#", "//", "/*", "*", "<!--")) else text

def declare_file(path):
    name = path.rsplit("/", 1)[-1].split(".")[0]
    if not test_path.search(path) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{2,}", name) and name not in ("index", "main", "package"):
        decl.add(name)

path, hunk, scopes = "", False, []
for l in diff:
    l = l.rstrip("\r")
    if l.startswith("diff --git "):
        path, hunk = diff_path(l), False
        declare_file(path)
    elif not hunk and l.startswith("rename from "):
        renamed.add(l[len("rename from "):])
        declare_file(l[len("rename from "):])
    elif l.startswith("@@"):
        hunk, scopes = True, []
        context = l.split("@@", 2)[-1].strip()
        if len(context) >= 80:
            context = re.sub(r"\w+$", "", context)
        if not test_path.search(path):
            enclosing.update(declared(context))
    elif hunk and l[:1] in ("+", "-", " ") and not test_path.search(path) and (text := code(l[1:])):
        indent = len(l[1:]) - len(l[1:].lstrip())
        if l[0] == " ":
            scopes = [s for s in scopes if s[0] < indent] + [(indent, n) for n in declared(text)]
            continue
        enclosing.update(n for i, n in scopes if i < indent)
        decl.update(declared(text))
        (plus if l[0] == "+" else minus).update(call.findall(text))
decl -= skip
enclosing -= decl
calls = {s for s in set(plus) | set(minus) if plus[s] != minus[s]} - skip
names = sorted(decl | enclosing | calls, key=lambda s: (s not in decl | enclosing, -len(s), s))
syms, unsearched = names[:80], names[80:]

def kind(s):
    return ("both" if s in decl and s in calls else "declaration" if s in decl
            else "enclosing" if s in enclosing else "call")

callers = ["# symbol\tkind\thits\twhere\ttext"]
if syms:
    excluded = sorted(set(changed) | renamed)
    cmd = (["git", "-C", root, "grep", "-n", "-I", "-w", "-F"] + sum((["-e", s] for s in syms), [])
           + [base, "--", "."] + [f":(exclude,literal){p}" for p in excluded])
    grep = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if grep.returncode > 1:
        sys.exit(f"git grep on {base} failed: {(grep.stderr.strip().splitlines() or [grep.returncode])[0]}")
    word = re.compile(r"\b(" + "|".join(map(re.escape, syms)) + r")\b")
    hits = collections.defaultdict(list)
    for line in grep.stdout.splitlines():
        where, num, text = line[len(base) + 1:].split(":", 2)
        for s in set(word.findall(text)):
            hits[s].append(f"{where}:{num}\t{text.strip()[:120]}")
    for s in syms:
        found = hits.get(s, [])
        if not found:
            callers.append(f"{s}\t{kind(s)}\t0\t-\tnothing outside the diff mentions it")
        elif len(found) > 150:
            callers.append(f"{s}\t{kind(s)}\t{len(found)}\t-\ttoo common to list")
        else:
            callers += [f"{s}\t{kind(s)}\t{len(found)}\t{h}" for h in found[:10]]
callers += [f"{s}\t{kind(s)}\t-\t-\tnot searched, past the first 80 names" for s in unsearched]
open(f"{out}/callers.tsv", "w").write("\n".join(callers) + "\n")

def save(ref, path, into):
    shown = subprocess.run(["git", "-C", root, "show", f"{ref}:{path}"], capture_output=True)
    if shown.returncode == 0 and b"\0" not in shown.stdout[:8000]:
        dest = os.path.join(out, into, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(shown.stdout)

for status, _, _, path in rows:
    if status != "removed":
        save(head, path, "head")
for path in {c.split("\t")[3].rsplit(":", 1)[0] for c in callers[1:]} - {"-"}:
    save(base, path, "base")
PY
[[ $? -eq 0 ]] || exit 1

cat <<EOF

gathered:
  $OUT/meta.json             title, author, refs, counts, labels (no body)
  $OUT/pr.diff               the full unified diff
  $OUT/pr-numbered.diff      the same diff with the head's line numbers
  $OUT/files.tsv             status, +, -, path
  $OUT/commit-subjects.txt   author prose, hints only
  $OUT/callers.tsv           where the base mentions each changed name, outside the diff
  $OUT/head/, $OUT/base/     changed files at the head and callers' files on the base, for the page's code pane

base: $BASE_OID ($BASE_WHAT)   head: $HEAD
EOF
