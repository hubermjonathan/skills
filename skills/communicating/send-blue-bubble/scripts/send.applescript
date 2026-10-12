-- argv: the message, then one handle per recipient.
on run argv
  set theMessage to item 1 of argv
  set wanted to rest of argv
  with timeout of 30 seconds
    tell application "Messages"
      set svc to 1st service whose service type = iMessage
      if (count of wanted) is 1 then
        send theMessage to buddy (item 1 of wanted) of svc
        return
      end if
      repeat with c in chats
        set have to {}
        repeat with p in participants of c
          set end of have to (handle of p as text)
        end repeat
        if my sameMembers(have, wanted) then
          send theMessage to c
          return
        end if
      end repeat
      -- Messages can't start a group chat from a script, so a new group has to start from a phone.
      return "no group"
    end tell
  end timeout
end run

on sameMembers(have, wanted)
  if (count of have) is not (count of wanted) then return false
  repeat with h in wanted
    if (h as text) is not in have then return false
  end repeat
  return true
end sameMembers
