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
      set theFiles to {}
      if (item 3 of argv) is not "" then set theFiles to paragraphs of (item 3 of argv)
      if mode is "group" then
        set matches to {}
        repeat with c in chats
          if name of c is not missing value and (name of c) is (item 4 of argv) then set end of matches to contents of c
        end repeat
        if (count of matches) is 0 then return "no group"
        if (count of matches) > 1 then return "several groups"
        return my deliver(theMessage, theFiles, item 1 of matches)
      end if
      set wanted to items 4 thru -1 of argv
      if (count of wanted) is 1 then
        set svc to 1st service whose service type = iMessage
        return my deliver(theMessage, theFiles, buddy (item 1 of wanted) of svc)
      end if
      repeat with c in chats
        set have to {}
        repeat with p in participants of c
          set end of have to (handle of p as text)
        end repeat
        if my sameMembers(have, wanted) then
          return my deliver(theMessage, theFiles, c)
        end if
      end repeat
      -- Messages can't start a group chat from a script, so a new group has to start from a phone.
      return "no group"
    end tell
  end timeout
end run

-- An alias, unlike a POSIX file, gives sandboxed Messages access to the file.
-- send reports no error when a file fails, so each one waits for its transfer's status.
on deliver(theMessage, theFiles, target)
  tell application "Messages"
    send theMessage to target
    repeat with f in theFiles
      set known to id of file transfers
      send ((POSIX file (f as text)) as alias) to target
      set outcome to my awaitTransfer(known)
      if outcome is not "finished" then return outcome & ":" & f
    end repeat
  end tell
  return ""
end deliver

on awaitTransfer(known)
  tell application "Messages"
    repeat 120 times
      repeat with t in file transfers
        if (id of t) is not in known then
          if transfer status of t is finished then return "finished"
          if transfer status of t is failed then return "failed"
        end if
      end repeat
      delay 0.5
    end repeat
  end tell
  return "unconfirmed"
end awaitTransfer

on sameMembers(have, wanted)
  if (count of have) is not (count of wanted) then return false
  repeat with h in wanted
    if (h as text) is not in have then return false
  end repeat
  return true
end sameMembers
