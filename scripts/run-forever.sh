#!/usr/bin/env bash
# Runs the bot and restarts it ten seconds after any crash. Works on Linux, macOS and Termux.
cd "$(dirname "$0")/.."
PY=.venv/bin/python
[ -x "$PY" ] || PY=python
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock  # keep Android from sleeping the CPU
while true; do
  "$PY" bot.py || true
  echo "Bot stopped, restarting in 10 seconds (Ctrl+C to quit)..."
  sleep 10
done
