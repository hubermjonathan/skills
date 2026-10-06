#!/bin/sh
set -u

PROFILES="$HOME/.claude/artifact-design-profiles"

installed() { ls "$PROFILES" 2>/dev/null | sed 's/^/  /' || echo "  (none)"; }

if [ $# -ne 1 ] || [ -z "$1" ]; then
  echo "usage: profile.sh <name>   a profile name is required" >&2
  echo "installed profiles:" >&2
  installed >&2
  exit 2
fi

P=$1
case "$P" in
  */*|.|..) echo "invalid profile name: '$P'" >&2; exit 2 ;;
esac

if [ ! -d "$PROFILES/$P" ]; then
  echo "profile '$P' is not installed."
  echo "installed profiles:"
  installed
  echo
  echo "install it with the install skill, or build it with the create skill."
  exit 1
fi

echo "profile: $P"
echo "grammar: $PROFILES/$P/grammar.md"
echo "tokens:  $PROFILES/$P/tokens.css"
if [ -f "$PROFILES/$P/icons.svg" ]; then
  echo "icons:   $PROFILES/$P/icons.svg"
else
  echo "icons:   (none, this profile ships no sprite)"
fi

for f in grammar.md tokens.css; do
  [ -s "$PROFILES/$P/$f" ] || { echo "ERROR: $f is missing or empty for profile '$P'"; exit 1; }
done
