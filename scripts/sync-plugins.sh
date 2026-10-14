#!/usr/bin/env bash
# Usage: sync-plugins.sh [--check] [repo...]
# For each repo, writes the Codex marketplace and each plugin's plugin.json from the repo's
# .claude-plugin/marketplace.json, then checks every plugin it lists. Skill names must be unique
# across all the repos, since their skills install side by side. The repos default to this one. With
# --check, it writes nothing and fails on any file that is out of date.
set -euo pipefail

check=false
[ "${1:-}" = --check ] && { check=true; shift; }
[ $# -gt 0 ] || set -- "$(dirname "$0")/.."
roots=()
for repo in "$@"; do roots+=("$(cd "$repo" && pwd)"); done
src=.claude-plugin/marketplace.json
fail=0
names=" "

err() { echo "error: $(basename "$PWD"): $*" >&2; fail=1; }

put() {
  if $check; then
    [ "$(cat "$1" 2>/dev/null)" = "$2" ] || err "$1 is out of date: run scripts/sync-plugins.sh"
  else
    mkdir -p "$(dirname "$1")"
    printf '%s\n' "$2" > "$1"
  fi
}

frontmatter() { awk -v key="$2" '/^---$/ { n++; next } n == 1 && $1 == key ":" { print $2; exit }' "$1"; }

for root in "${roots[@]}"; do
  cd "$root"
  url=$(git remote get-url origin | sed -E 's#^git@github\.com:#https://github.com/#; s#\.git$##')

  put .agents/plugins/marketplace.json "$(jq '{
    name,
    interface: { displayName: "\(.name) skills" },
    plugins: [.plugins[] | {
      name,
      source: { source: "local", path: .source },
      policy: { installation: "AVAILABLE", authentication: "ON_INSTALL" },
      category: "Productivity",
      interface: { displayName }
    }]
  }' "$src")"

  while read -r plugin; do
    name=$(jq -r .name <<<"$plugin")
    dir=$(jq -r '.source | ltrimstr("./")' <<<"$plugin")
    [ -d "$dir" ] || { err "$name: $dir is missing"; continue; }

    put "$dir/plugin.json" "$(jq --arg repo "$url" --argjson owner "$(jq .owner "$src")" '{
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
      grep -qF "]($md)" README.md || err "$skill: README.md has no row for it"
    done
  done < <(jq -c '.plugins[]' "$src")

  for dir in plugins/*/; do
    jq -e --arg dir "./${dir%/}" 'any(.plugins[]; .source == $dir)' "$src" >/dev/null || err "${dir%/} is not in $src"
  done

  if command -v claude >/dev/null; then
    claude plugin validate . >/dev/null || err "claude plugin validate . failed"
  fi
done

exit "$fail"
