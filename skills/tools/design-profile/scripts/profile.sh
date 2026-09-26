#!/bin/sh
# Resolves a design profile and prints the paths to its files.
#
#   sh profile.sh            the active profile
#   sh profile.sh <name>     that named profile, whatever is active
#
# The active profile is named in the mode file ~/.claude/artifact-design-profile,
# one name on one line, and is "offerup" when that file is absent or empty. The
# mode file is read on every run, so a switch takes effect on the next artifact
# with no restart.
#
# The <name> form is for the install and create skills, which need to prove one
# profile loads without disturbing whichever one is active.
#
# Exit codes: 0 = resolved, 1 = named profile not installed, 3 = "none", the
# reserved opt-out — no profile is active and the skill must stand down.
set -u

PROFILES="$HOME/.claude/artifact-design-profiles"
MODE_FILE="$HOME/.claude/artifact-design-profile"

if [ $# -gt 1 ]; then
  echo "usage: profile.sh [name]" >&2
  exit 2
fi

P=${1:-}
if [ -n "$P" ]; then
  SRC="requested"
else
  SRC=""
  if [ -r "$MODE_FILE" ]; then
    # read reports failure at EOF on a file with no trailing newline, having still
    # assigned what it read — so the status is ignored rather than treated as empty.
    read -r P <"$MODE_FILE" 2>/dev/null || :
    # trim whitespace, so a stray space or an editor's stray blank still resolves
    P=$(printf '%s' "$P" | tr -d '[:space:]')
    [ -n "$P" ] && SRC=$MODE_FILE
  fi
  if [ -z "$P" ]; then
    P=offerup
    SRC=default
  fi
fi

# "none" is reserved and checked before the filesystem, so it cannot be
# shadowed by a directory that happens to be called none.
if [ "$P" = none ]; then
  echo "profile: none   (source: $SRC)"
  echo "no design profile is active — do not apply one; build the page normally."
  exit 3
fi

if [ ! -d "$PROFILES/$P" ]; then
  echo "profile '$P' (from $SRC) is not installed."
  echo "available profiles:"
  ls "$PROFILES" 2>/dev/null | sed 's/^/  /' || echo "  (none)"
  echo
  echo "either switch to one of the above with the /skills:switch-design-profile skill,"
  echo "install it with the /skills:install-design-profile skill,"
  echo "or switch to 'none' to opt out of design profiles entirely."
  exit 1
fi

echo "profile: $P   (source: $SRC)"
echo "grammar: $PROFILES/$P/grammar.md"
echo "tokens:  $PROFILES/$P/tokens.css"
if [ -f "$PROFILES/$P/icons.svg" ]; then
  echo "icons:   $PROFILES/$P/icons.svg"
else
  echo "icons:   (none — this profile ships no sprite)"
fi

for f in grammar.md tokens.css; do
  [ -s "$PROFILES/$P/$f" ] || { echo "ERROR: $f is missing or empty for profile '$P'"; exit 1; }
done
