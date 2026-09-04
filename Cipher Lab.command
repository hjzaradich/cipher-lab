#!/bin/sh
# macOS: double-click to launch (run `chmod +x "Cipher Lab.command"` once first).
# Linux: works the same from a terminal, or rename to .sh.
cd "$(dirname "$0")" || exit 1
exec python3 main.py
