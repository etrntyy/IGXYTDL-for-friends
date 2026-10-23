#!/usr/bin/env bash
# Sets up the bot on Linux (Raspberry Pi, laptops, servers) or macOS.
#   ./scripts/install.sh            install dependencies and create .env
#   ./scripts/install.sh --service  also install + start a systemd service (Linux): runs at boot, restarts on crash
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}

if command -v apt-get >/dev/null 2>&1; then
  echo "Installing system packages (asks for your sudo password)..."
  sudo apt-get update -qq
  sudo apt-get install -y ffmpeg python3-venv python3-pip
fi
"$PY" -c 'import sys; sys.exit(sys.version_info < (3, 10))' || { echo "Python 3.10 or newer is required."; exit 1; }
command -v ffmpeg >/dev/null 2>&1 || echo "Note: no system ffmpeg found; the bot will use a bundled copy."

"$PY" -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env

read -rsp "Telegram bot token from @BotFather (Enter to fill in .env yourself later): " tok; echo
if [ -n "$tok" ]; then
  TOK="$tok" .venv/bin/python - <<'PY'
import os, pathlib, re
p = pathlib.Path(".env")
p.write_text(re.sub(r"(?m)^TELEGRAM_BOT_TOKEN=.*$", lambda m: "TELEGRAM_BOT_TOKEN=" + os.environ["TOK"], p.read_text()))
PY
fi
chmod 600 .env

if [ "${1:-}" = "--service" ]; then
  sed -e "s|__USER__|$(id -un)|" -e "s|__DIR__|$PWD|g" deploy/igxytdl.service | sudo tee /etc/systemd/system/igxytdl.service >/dev/null
  sudo systemctl daemon-reload
  sudo systemctl enable --now igxytdl
  echo "Service installed and running. Logs: journalctl -u igxytdl -f"
else
  echo "Done. Edit .env if needed, then run:  ./scripts/run-forever.sh"
fi
