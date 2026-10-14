---
name: create-qr-code
description: >
  Generate a QR code for a link with the qrencode CLI and show it in the reply. Use
  when asked for a QR code, whether the request gives the link or refers to one
  from earlier in the conversation.
---

# Create QR code

## Pick the link

- If the request gives a link, use it as is.
- Otherwise, take the link the request refers to from the conversation. "It" usually means the last link you or the user shared, such as an artifact, PR, or doc link. When several links could fit, pick the one the conversation was about most recently, and name it in your reply so the user can correct you.
- If the conversation has no link, ask for one.

A QR code for a local file path, a `file://` URL, or a `localhost` address won't open on another device. Say so before you generate one.

## Generate it

Write a PNG to a working file named `qr-<short-name>.png`, with the link in single quotes:

    qrencode -s 10 -m 2 -o <dir>/qr-<short-name>.png '<link>'

`-s 10` makes each module 10 pixels and `-m 2` keeps a margin, so a phone can scan it off a screen.

## Show it

Embed the PNG in your reply as an image by its absolute path, with the link as plain text under it. If your interface can't show images, run `qrencode -t UTF8 '<link>'` and put its output in a code block instead.
