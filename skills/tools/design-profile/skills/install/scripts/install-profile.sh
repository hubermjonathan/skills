#!/bin/sh
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

There is no default name. Ask which design system this is rather than guessing.
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

case "$0" in
  */*) SKILLS=${0%/*}/../.. ;;
  *)   SKILLS=../.. ;;
esac
RESOLVER="$SKILLS/use/scripts/profile.sh"
PROFILES="$HOME/.claude/artifact-design-profiles"
DEST="$PROFILES/$PROFILE"

case "$PROFILE" in
  "") echo "missing required --profile NAME. Ask which design system this is, since there is no default." >&2
      echo >&2; usage >&2; exit 2 ;;
  */*|.|..) echo "invalid profile name: '$PROFILE'" >&2; exit 2 ;;
esac

if [ ! -d "$PROFILES" ]; then
  mkdir -p "$PROFILES" || { echo "could not create the profile store: $PROFILES" >&2; exit 1; }
  echo "created the profile store: $PROFILES"
fi

bad=0
check() {
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

echo "installing profile '$PROFILE'"
[ -d "$DEST" ] && echo "  updating an existing profile, so its current files will be overwritten"
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
  rm -f "$DEST/icons.svg"
fi

echo
fail=0
for f in grammar.md tokens.css; do
  if [ -s "$DEST/$f" ]; then echo "  ok  profiles/$PROFILE/$f"
  else echo "  MISSING OR EMPTY  profiles/$PROFILE/$f"; fail=1; fi
done
[ -f "$DEST/icons.svg" ] && echo "  ok  profiles/$PROFILE/icons.svg"
[ "$fail" = 0 ] || { echo; echo "install incomplete, see above." >&2; exit 1; }

if [ -f "$RESOLVER" ] && sh "$RESOLVER" "$PROFILE" >/dev/null 2>&1; then
  echo "  ok  the resolver loads '$PROFILE'"
else
  echo "  warning: installed, but scripts/profile.sh could not resolve '$PROFILE'"
fi

echo
echo "profile '$PROFILE' installed at $DEST"
echo "all installed profiles: $(ls "$PROFILES" | tr '\n' ' ')"
