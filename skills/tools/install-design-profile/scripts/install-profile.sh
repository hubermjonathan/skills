#!/bin/sh
# Installs or updates one design profile from explicit file references.
# Creates the profile store (~/.claude/artifact-design-profiles) if it is
# missing, so no separate setup step is needed.
#
#   sh install-profile.sh --profile NAME --grammar PATH --tokens PATH [--icons PATH]
#
# --profile is required; there is no default. 'offerup' is only a default in the
# resolver, as the fallback when nothing selects a profile.
#
# Source filenames are irrelevant; each file is copied to its canonical name.
# That makes browser-deduplicated names ("tokens (1).css") and per-system names
# ("acme-grammar.md") work without renaming anything first.
#
# Safe to re-run — updates the files in place.
set -u

PROFILE=
GRAMMAR=
TOKENS=
ICONS=

usage() {
  cat <<'USAGE'
usage: install-profile.sh --profile NAME --grammar PATH --tokens PATH [--icons PATH]

  --profile NAME   profile name to install as                    [required]
  --grammar PATH   the profile's usage rules (markdown)          [required]
  --tokens  PATH   the profile's design tokens (css)             [required]
  --icons   PATH   the profile's icon sprite (svg)               [optional]

There is no default name — ask which design system this is rather than guessing.
Paths may be absolute, relative, or start with ~/.
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --profile) shift; PROFILE=${1:-} ;;
    --grammar) shift; GRAMMAR=${1:-} ;;
    --tokens)  shift; TOKENS=${1:-} ;;
    --icons)   shift; ICONS=${1:-} ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; echo >&2; usage >&2; exit 2 ;;
  esac
  shift
done

# ~/ is expanded here because a quoted argument from a caller never gets shell expansion
expand() {
  case "$1" in
    "~")   printf '%s' "$HOME" ;;
    "~/"*) printf '%s' "$HOME/${1#\~/}" ;;
    *)     printf '%s' "$1" ;;
  esac
}
GRAMMAR=$(expand "${GRAMMAR}")
TOKENS=$(expand "${TOKENS}")
[ -n "$ICONS" ] && ICONS=$(expand "$ICONS")

# The design-profile skill is a sibling under the plugin's skills/ directory, so this
# resolves wherever the plugin is checked out. Parameter expansion rather than
# $(cd … && pwd): the path is never canonicalised, but it also never passes
# through a command substitution, which keeps taint analysis clean.
case "$0" in
  */*) SKILLS=${0%/*}/../.. ;;
  *)   SKILLS=../.. ;;
esac
RESOLVER="$SKILLS/design-profile/scripts/profile.sh"
PROFILES="$HOME/.claude/artifact-design-profiles"
DEST="$PROFILES/$PROFILE"

case "$PROFILE" in
  "") echo "missing required --profile NAME — ask which design system this is; there is no default." >&2
      echo >&2; usage >&2; exit 2 ;;
  */*|.|..) echo "invalid profile name: '$PROFILE'" >&2; exit 2 ;;
  none) echo "'none' is reserved: it means no profile at all, so it cannot be installed." >&2; exit 2 ;;
esac

# The profile store lives outside the skills, so this is the one place that
# creates it — there is no separate setup step.
if [ ! -d "$PROFILES" ]; then
  mkdir -p "$PROFILES" || { echo "could not create the profile store: $PROFILES" >&2; exit 1; }
  echo "created the profile store: $PROFILES"
fi

# --- validate every reference before copying anything -----------------------
bad=0
check() { # path, flag-name
  p=$1; flag=$2
  if [ -z "$p" ]; then echo "missing required --$flag" >&2; bad=1; return; fi
  if [ ! -e "$p" ]; then echo "--$flag: no such file: $p" >&2; bad=1; return; fi
  if [ -d "$p" ]; then echo "--$flag is a directory, not a file: $p" >&2; bad=1; return; fi
  if [ ! -r "$p" ]; then echo "--$flag: not readable: $p" >&2; bad=1; return; fi
  if [ ! -s "$p" ]; then echo "--$flag: file is empty: $p" >&2; bad=1; return; fi
}
check "$GRAMMAR" grammar
check "$TOKENS"  tokens
[ -n "$ICONS" ] && check "$ICONS" icons
[ "$bad" = 0 ] || { echo >&2; usage >&2; exit 2; }

# Sniff content so a mis-mapped path fails loudly instead of installing a
# profile whose "grammar" is actually a stylesheet.
looks_svg()  { head -c 4000 "$1" | grep -qi '<svg'; }
looks_css()  { head -c 4000 "$1" | grep -q -- '--[a-zA-Z]' || head -c 4000 "$1" | grep -qi ':root'; }
looks_md()   { head -c 4000 "$1" | grep -q '^#' || head -c 4000 "$1" | grep -q '^- '; }

if looks_svg "$GRAMMAR"; then echo "--grammar looks like an SVG: $GRAMMAR" >&2; bad=1; fi
if looks_css "$GRAMMAR" && ! looks_md "$GRAMMAR"; then
  echo "--grammar looks like CSS, not markdown: $GRAMMAR" >&2
  echo "  did --grammar and --tokens get swapped?" >&2; bad=1
fi
if looks_svg "$TOKENS"; then echo "--tokens looks like an SVG: $TOKENS" >&2; bad=1; fi
if ! looks_css "$TOKENS"; then
  echo "--tokens does not look like CSS (no custom properties or :root found): $TOKENS" >&2; bad=1
fi
if [ -n "$ICONS" ] && ! looks_svg "$ICONS"; then
  echo "--icons does not look like an SVG: $ICONS" >&2; bad=1
fi
[ "$bad" = 0 ] || { echo >&2; echo "nothing was installed." >&2; exit 2; }

# --- install ---------------------------------------------------------------
echo "installing profile '$PROFILE'"
[ -d "$DEST" ] && echo "  updating an existing profile — its current files will be overwritten"
echo "  grammar  <- $GRAMMAR"
echo "  tokens   <- $TOKENS"
if [ -n "$ICONS" ]; then
  echo "  icons    <- $ICONS"
else
  echo "  icons    <- (none given; installing without a sprite, which is supported)"
fi

mkdir -p "$DEST"
cp "$GRAMMAR" "$DEST/grammar.md"
cp "$TOKENS"  "$DEST/tokens.css"
if [ -n "$ICONS" ]; then
  cp "$ICONS" "$DEST/icons.svg"
else
  rm -f "$DEST/icons.svg"   # a re-install without --icons removes a stale sprite
fi

# --- verify ----------------------------------------------------------------
echo
fail=0
for f in grammar.md tokens.css; do
  if [ -s "$DEST/$f" ]; then echo "  ok  profiles/$PROFILE/$f"
  else echo "  MISSING OR EMPTY  profiles/$PROFILE/$f"; fail=1; fi
done
[ -f "$DEST/icons.svg" ] && echo "  ok  profiles/$PROFILE/icons.svg"
[ "$fail" = 0 ] || { echo; echo "install incomplete — see above." >&2; exit 1; }

# Ask the resolver for this profile by name, so proving it loads never depends
# on — or disturbs — whichever profile is currently active.
if [ -f "$RESOLVER" ] && sh "$RESOLVER" "$PROFILE" >/dev/null 2>&1; then
  echo "  ok  the resolver loads '$PROFILE'"
else
  echo "  warning: installed, but scripts/profile.sh could not resolve '$PROFILE'"
fi

echo
echo "profile '$PROFILE' installed at $DEST"
echo "all installed profiles: $(ls "$PROFILES" | tr '\n' ' ')"

# --- is it the one that will actually be used? -----------------------------
# Mirrors the resolver: the mode file, else the 'offerup' default.
MODE_FILE="$HOME/.claude/artifact-design-profile"
cur=""
if [ -r "$MODE_FILE" ]; then
  read -r cur <"$MODE_FILE" 2>/dev/null || :   # non-zero at EOF without a newline; value is set
  cur=$(printf '%s' "$cur" | tr -d '[:space:]')
fi

if [ -z "$cur" ]; then
  if [ "$PROFILE" = offerup ]; then
    echo "no profile is selected, so the 'offerup' default means this profile is active."
  else
    echo "no profile is selected, so the default 'offerup' is active — NOT '$PROFILE'."
    echo "to use it, run the /skills:switch-design-profile skill with '$PROFILE'."
  fi
elif [ "$cur" != "$PROFILE" ]; then
  echo "the active profile is '$cur', so '$PROFILE' will NOT be used until you switch."
  echo "run the /skills:switch-design-profile skill with '$PROFILE'."
else
  echo "the active profile is '$cur', so this profile is the one in use."
fi
