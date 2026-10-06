#!/bin/sh
# Sends stdin as an iMessage to $IMESSAGE_HANDLE.
# Usage: send.sh <<'MSG'
#        <message>
#        MSG
#
# Exit codes: 0 = sent, 1 = Messages refused the send, 2 = bad input or setup.

handle=$(printf '%s' "${IMESSAGE_HANDLE:-}" | tr -d '[:space:]')
if [ -z "$handle" ]; then
  echo "not sent: IMESSAGE_HANDLE is not set. Set it to a phone number in E.164 form (+11234567890) or an Apple ID email." >&2
  exit 2
fi

message=$(cat)
if [ -z "$(printf '%s' "$message" | tr -d '[:space:]')" ]; then
  echo "not sent: the message on stdin is empty." >&2
  exit 2
fi

if ! out=$(/usr/bin/osascript "$(dirname "$0")/send.applescript" "$message" "$handle" 2>&1); then
  echo "not sent: $out" >&2
  echo "common causes: not on macOS, Messages is not signed in to iMessage, the handle can't receive iMessage, or this process lacks Automation permission for Messages (System Settings > Privacy & Security > Automation)." >&2
  exit 1
fi
echo sent
