#!/bin/bash
# 飞机大战 - Airplane Shooter Launcher
# Uses macOS system Python 3.9+ which has Tkinter

DIR="$(cd "$(dirname "$0")" && pwd)"
HAS_TK="$(python3 -c 'import tkinter; print("ok")' 2>/dev/null)"

if [ "$HAS_TK" = "ok" ]; then
    cd "$DIR" && python3 game.py
else
    # Try macOS system Python
    /usr/bin/python3 "$DIR/game.py"
fi
