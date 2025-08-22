#!/bin/bash
# Minimal clickable script to locate and open any folder in Terminal

# Ask Finder to pick a folder
SELECTED_DIR=$(osascript <<'APPLESCRIPT'
tell application "System Events"
    activate
    set chosenFolder to choose folder with prompt "Select a folder to open in Terminal:"
    return POSIX path of chosenFolder
end tell
APPLESCRIPT
)

# Open a new Terminal window in that folder
open -a Terminal "$SELECTED_DIR"
