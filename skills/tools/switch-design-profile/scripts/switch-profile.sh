#!/bin/sh
# Sets the active design profile by writing ~/.claude/artifact-design-profile.
#
#   sh switch-profile.sh <name>      an installed profile, or 'none' to opt out
#   sh switch-profile.sh --show      report the current selection, change nothing
#
# The mode file holds one profile name on one line and the resolver reads it on
# every run, so a switch applies to the next artifact — no restart. This is the
# only script in the skill set that writes user config, and it does so only when
# explicitly invoked.
set -u

PROFILES="$HOME/.claude/artifact-design-profiles"
MODE_FILE="$HOME/.claude/artifact-design-profile"

usage() { echo "usage: switch-profile.sh <name|none>   |   switch-profile.sh --show" >&2; exit 2; }

[ $# -eq 1 ] || usage
NAME=$1

installed() { ls "$PROFILES" 2>/dev/null | tr '\n' ' '; }

current=""
if [ -r "$MODE_FILE" ]; then
  # a file with no trailing newline makes read report failure after assigning, so
  # the status is ignored — same as in the resolver.
  read -r current <"$MODE_FILE" 2>/dev/null || :
  current=$(printf '%s' "$current" | tr -d '[:space:]')
fi

if [ "$NAME" = --show ]; then
  if [ -n "$current" ]; then
    echo "active:    $current   (from $MODE_FILE)"
  else
    echo "active:    offerup   (the default — $MODE_FILE is not set)"
  fi
  echo "installed: $(installed)"
  exit 0
fi

case "$NAME" in
  -*|*/*|.|..|"") echo "invalid profile name: '$NAME'" >&2; usage ;;
esac

# 'none' is reserved and always valid; anything else must actually be installed,
# so this cannot point the resolver at a profile that will fail to load.
if [ "$NAME" != none ] && [ ! -d "$PROFILES/$NAME" ]; then
  echo "profile '$NAME' is not installed." >&2
  echo "installed: $(installed)" >&2
  echo "install it with the install-design-profile skill, or use 'none' to opt out." >&2
  exit 1
fi

if [ "$current" = "$NAME" ]; then
  echo "the active profile is already '$NAME' — nothing to do."
  exit 0
fi

dir=$(dirname "$MODE_FILE")
[ -d "$dir" ] || mkdir -p "$dir" || exit 1
tmp=$(mktemp) || exit 1
echo "$NAME" >"$tmp" || { rm -f "$tmp"; exit 1; }
cat "$tmp" >"$MODE_FILE" || { rm -f "$tmp"; echo "ERROR: could not write $MODE_FILE" >&2; exit 1; }
rm -f "$tmp"

if [ -n "$current" ]; then echo "active profile: $current -> $NAME"
else echo "active profile: (unset) -> $NAME"; fi
echo "written to $MODE_FILE — this takes effect on the next artifact, no restart."
[ "$NAME" = none ] && echo "'none' means the design-profile skill stands down and applies nothing."
exit 0
