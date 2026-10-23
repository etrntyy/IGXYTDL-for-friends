#!/usr/bin/env bash
# macOS: run the bot when you log in and keep it running (a launchd "login agent").
#   ./scripts/mac-service.sh install     start now and at every login, restart after crashes
#   ./scripts/mac-service.sh uninstall   stop it and remove the agent
#   ./scripts/mac-service.sh restart     restart it (after changing .env, for example)
#   ./scripts/mac-service.sh status      is it running? shows the last log lines
#   ./scripts/mac-service.sh logs        follow the log (Ctrl+C to leave)
set -euo pipefail
cd "$(dirname "$0")/.."
DIR=$PWD
LABEL=com.igxytdl.bot
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/igxytdl.log"
DOMAIN="gui/$(id -u)"

write_plist() {
  cat <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-is</string>
    <string>$DIR/scripts/run-forever.sh</string>
  </array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
PLIST
}

case "${1:-}" in
  install)
    [ -x .venv/bin/python ] && [ -f .env ] || { echo "Run ./scripts/install.sh first (it creates the environment and .env)."; exit 1; }
    mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
    write_plist > "$PLIST"
    launchctl bootout "$DOMAIN" "$PLIST" 2>/dev/null || true
    launchctl bootstrap "$DOMAIN" "$PLIST"
    echo "Installed. The bot is starting and will start at every login."
    echo "Check it with: ./scripts/mac-service.sh status"
    ;;
  uninstall)
    launchctl bootout "$DOMAIN" "$PLIST" 2>/dev/null || true
    rm -f "$PLIST"
    echo "Stopped and removed."
    ;;
  restart)
    launchctl kickstart -k "$DOMAIN/$LABEL"
    echo "Restarted."
    ;;
  status)
    launchctl list | grep "$LABEL" || echo "Not running (run: ./scripts/mac-service.sh install)"
    [ -f "$LOG" ] && tail -n 5 "$LOG"
    ;;
  logs)
    tail -f "$LOG"
    ;;
  print)  # show the agent file without installing it
    write_plist
    ;;
  *)
    echo "Usage: $0 install | uninstall | restart | status | logs"; exit 1
    ;;
esac
