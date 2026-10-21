#!/usr/bin/env bash
# Thin wrapper so the hook command in .claude/settings.json doesn't have to
# guess which Python interpreter actually works on this machine. The .py
# file itself is stdlib-only (no pip install needed), so any real Python 3
# runs it fine - the only question is finding one. Checked in order:
#   1. This project's own venvs, if someone's already set one up (and on
#      Windows specifically: `python`/`python3` on PATH are often just
#      Microsoft Store shortcut stubs that print an install prompt and exit
#      nonzero rather than running real Python - a project venv is real
#      even when PATH isn't)
#   2. python3 / python on PATH - the normal case on a fresh clone with
#      Python properly installed (most Mac/Linux setups, or Windows via
#      the official python.org installer)
dir="$(dirname "$0")"
for candidate in \
    "$dir/../sdk/.venv/Scripts/python.exe" \
    "$dir/../sdk/.venv/bin/python3" \
    "$dir/../backend/.venv/Scripts/python.exe" \
    "$dir/../backend/.venv/bin/python3" \
    python3 \
    python
do
    if command -v "$candidate" >/dev/null 2>&1; then
        exec "$candidate" "$dir/record_claude_session_trace.py"
    fi
done
exit 0
