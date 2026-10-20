#!/bin/sh
# Sends stdin to the people named as arguments, looking each name up in IMESSAGE_HANDLES,
# or to a group chat by its name with --group. Prints names, never handles.
set -f
script="$(dirname "$0")/send.applescript"
start_group="Messages can't start a group from a script. Start a group text from a phone, with the agent's account and those people, then send again."

lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

names() {
  for pair in ${IMESSAGE_HANDLES:-}; do lower "${pair%%=*}"; echo; done
}

handle_for() {
  for pair in ${IMESSAGE_HANDLES:-}; do
    if [ "$(lower "${pair%%=*}")" = "$(lower "$1")" ]; then printf '%s' "${pair#*=}"; return 0; fi
  done
  return 1
}

# Runs send.applescript and leaves its output in $out. Masks any handle in an error.
messages() {
  if ! out=$(/usr/bin/osascript "$script" "$@" 2>&1); then
    echo "not sent: $(printf '%s' "$out" | sed -E 's/\+?[0-9]{7,}/<number>/g; s/[^[:space:]]+@[^[:space:]]+/<email>/g')" >&2
    echo "common causes: not on macOS, Messages is not signed in to iMessage, a handle can't receive iMessage, or this process lacks Automation permission for Messages (System Settings > Privacy & Security > Automation)." >&2
    exit 1
  fi
}

read_message() {
  message=$(cat)
  if [ -z "$(printf '%s' "$message" | tr -d '[:space:]')" ]; then
    echo "not sent: the message on stdin is empty." >&2
    exit 2
  fi
}

# Messages' upload daemon reads files only from a few folders, so each file goes out from a copy in the user's temp folder.
files=""
n=0
while [ "${1:-}" = "--attach" ]; do
  if [ $# -lt 2 ] || [ ! -f "$2" ] || [ ! -r "$2" ]; then
    echo "not sent: --attach takes a file that exists, such as --attach shot.png." >&2
    exit 2
  fi
  case "$2" in *"
"*) echo "not sent: an --attach path can't hold a line break." >&2; exit 2 ;; esac
  if [ -z "$files" ]; then
    stage=$(mktemp -d "$(getconf DARWIN_USER_TEMP_DIR)send-blue-bubble.XXXXXX") || exit 1
    trap 'rm -rf "$stage"' EXIT
  fi
  n=$((n + 1))
  copy="$stage/$n/$(basename "$2")"
  mkdir "$stage/$n" && cp "$2" "$copy" || exit 1
  files="${files:+$files
}$copy"
  shift 2
done

check_files() {
  case "$out" in
    failed:*) echo "the text was sent, but Messages couldn't send $(basename "${out#failed:}")." >&2; exit 1 ;;
    unconfirmed:*) echo "the text was sent, but $(basename "${out#unconfirmed:}") was still sending after a minute. Ask the user whether it arrived before sending it again." >&2; exit 1 ;;
  esac
}

case "${1:-}" in
  --list)
    names
    exit 0
    ;;
  --groups)
    messages groups
    printf '%s' "$out"
    exit 0
    ;;
  --group)
    if [ $# -ne 2 ] || [ -z "$2" ]; then
      echo "not sent: --group takes one group chat name, such as --group 'Budget updates'." >&2
      exit 2
    fi
    read_message
    messages group "$message" "$files" "$2"
    case "$out" in
      "no group") echo "not sent: no group chat is named '$2'. $start_group Name it '$2' there." >&2; exit 3 ;;
      "several groups") echo "not sent: more than one group chat is named '$2'. Rename one from a phone, then send again." >&2; exit 3 ;;
    esac
    check_files
    echo sent
    exit 0
    ;;
esac

if [ -z "$(printf '%s' "${IMESSAGE_HANDLES:-}" | tr -d '[:space:]')" ]; then
  echo "not sent: IMESSAGE_HANDLES is not set. Set it to space-separated name=handle pairs, such as 'me=+11234567890 jac=jac@icloud.com'." >&2
  exit 2
fi

if [ $# -eq 0 ]; then
  echo "not sent: name at least one recipient, such as 'send.sh me'. Known names: $(names | paste -sd ' ' -)" >&2
  exit 2
fi

asked="$*"
handles=""
for name in "$@"; do
  if ! handle=$(handle_for "$name"); then
    echo "not sent: no handle for '$name' in IMESSAGE_HANDLES. Known names: $(names | paste -sd ' ' -)" >&2
    exit 2
  fi
  if ! printf '%s' "$handle" | grep -Eq '^\+[0-9]{8,15}$|^[^@[:space:]]+@[^@[:space:]]+$'; then
    echo "not sent: the handle for '$name' is not a phone number in E.164 form (+11234567890) or an email." >&2
    exit 2
  fi
  case "
$handles
" in *"
$handle
"*) continue ;; esac
  handles="$handles
$handle"
done

read_message

# One argument per handle, so a handle never passes through the shell twice.
set --
while IFS= read -r handle; do
  [ -n "$handle" ] && set -- "$@" "$handle"
done <<HANDLES
$handles
HANDLES

messages people "$message" "$files" "$@"
if [ "$out" = "no group" ]; then
  echo "not sent: no group chat has exactly these people: $asked. $start_group" >&2
  exit 3
fi
check_files
echo sent
