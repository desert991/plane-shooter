#!/bin/bash
# macOS Finder double-click launcher
DIR="$(cd "$(dirname "$0")" && pwd)"
HAS_TK="$(python3 -c 'import tkinter; print("ok")' 2>/dev/null)"
if [ "$HAS_TK" = "ok" ]; then
    cd "$DIR" && python3 game.py
else
    /usr/bin/python3 "$DIR/game.py"
fi
