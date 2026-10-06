on run argv
  with timeout of 20 seconds
    tell application "Messages"
      set svc to 1st service whose service type = iMessage
      send item 1 of argv to buddy (item 2 of argv) of svc
    end tell
  end timeout
end run
