#!/usr/bin/env bash
# Writes the Codex marketplace and each plugin's plugin.json from .claude-plugin/marketplace.json,
# then checks every plugin the marketplace lists. A plugin in another repo is synced and checked
# through that repo's checkout beside this one, or under REPOS_DIR. With --check, it writes nothing
# and fails on any file that is out of date.
set -euo pipefail
cd "$(dirname "$0")/.."

check=false
[ "${1:-}" = --check ] && check=true
repos="${REPOS_DIR:-$(dirname "$PWD")}"
src=.claude-plugin/marketplace.json
fail=0
names=" "

err() { echo "error: $*" >&2; fail=1; }

put() {
  if $check; then
    [ "$(cat "$1" 2>/dev/null)" = "$2" ] || err "$1 is out of date: run scripts/sync-plugins.sh"
  else
    printf '%s\n' "$2" > "$1"
  fi
}

frontmatter() { awk -v key="$2" '/^---$/ { n++; next } n == 1 && $1 == key ":" { print $2; exit }' "$1"; }

put .agents/plugins/marketplace.json "$(jq '{
  name,
  interface: { displayName: "\(.name) skills" },
  plugins: [.plugins[] | {
    name,
    source: (if (.source | type) == "string"
      then { source: "local", path: .source }
      else .source + { path: ("./" + .source.path) } end),
    policy: { installation: "AVAILABLE", authentication: "ON_INSTALL" },
    category: "Productivity",
    interface: { displayName }
  }]
}' "$src")"

while read -r plugin; do
  name=$(jq -r .name <<<"$plugin")
  if [ "$(jq -r '.source | type' <<<"$plugin")" = string ]; then
    dir=$(jq -r '.source | ltrimstr("./")' <<<"$plugin")
    repo=https://github.com/hubermjonathan/skills
    root=.
    [ -d "$dir" ] || { err "$name: $dir is missing"; continue; }
  else
    repo=$(jq -r '.source.url | rtrimstr(".git")' <<<"$plugin")
    root="$repos/$(basename "$repo")"
    dir="$root/$(jq -r .source.path <<<"$plugin")"
    [ -d "$dir" ] || { echo "skipped $name: no checkout at $dir" >&2; continue; }
  fi

  put "$dir/plugin.json" "$(jq --arg repo "$repo" --argjson owner "$(jq .owner "$src")" '{
    "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
    name,
    description,
    author: $owner,
    repository: $repo,
    extensions: { "com.openai": { interface: { displayName } } }
  }' <<<"$plugin")"

  for md in "$dir"/skills/*/SKILL.md; do
    skill=$(basename "$(dirname "$md")")
    yaml="$(dirname "$md")/agents/openai.yaml"
    [ "$(frontmatter "$md" name)" = "$skill" ] || err "$md: name differs from its folder"
    case "$names" in *" $skill "*) err "$skill: two skills share this name" ;; esac
    names="$names$skill "
    [ -f "$yaml" ] || { err "$yaml is missing"; continue; }
    claude=$([ "$(frontmatter "$md" disable-model-invocation)" = true ] && echo user || echo model)
    codex=$(grep -q 'allow_implicit_invocation: false' "$yaml" && echo user || echo model)
    [ "$claude" = "$codex" ] || err "$skill: SKILL.md says $claude-invoked, agents/openai.yaml says $codex-invoked"
    grep -qF "](${md#"$root"/})" "$root/README.md" || err "$skill: $root/README.md has no row for it"
  done
done < <(jq -c '.plugins[]' "$src")

for dir in plugins/*/; do
  jq -e --arg dir "./${dir%/}" 'any(.plugins[]; .source == $dir)' "$src" >/dev/null || err "${dir%/} is not in $src"
done

if command -v claude >/dev/null; then
  claude plugin validate . >/dev/null || err "claude plugin validate . failed"
fi

exit "$fail"
