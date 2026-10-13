-- argv: "people", the message, then one handle per recipient
--   or: "group", the message, then a group chat's name
--   or: "groups", to list the names of named group chats
on run argv
  set mode to item 1 of argv
  with timeout of 30 seconds
    tell application "Messages"
      if mode is "groups" then
        set out to ""
        repeat with c in chats
          if name of c is not missing value and (count of participants of c) > 1 then set out to out & (name of c) & linefeed
        end repeat
        return out
      end if
      set theMessage to item 2 of argv
      if mode is "group" then
        set matches to {}
        repeat with c in chats
          if name of c is not missing value and (name of c) is (item 3 of argv) then set end of matches to contents of c
        end repeat
        if (count of matches) is 0 then return "no group"
        if (count of matches) > 1 then return "several groups"
        send theMessage to item 1 of matches
        return
      end if
      set wanted to items 3 thru -1 of argv
      if (count of wanted) is 1 then
        set svc to 1st service whose service type = iMessage
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
