#!/data/data/com.termux/files/usr/bin/bash
# Sets up the bot on an Android phone inside Termux (install Termux from F-Droid, not the Play Store).
set -e
cd "$(dirname "$0")/.."
pkg update -y
pkg install -y python ffmpeg git python-pillow
pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
chmod 600 .env

# Start automatically after a phone reboot (needs the free "Termux:Boot" app from F-Droid, opened once).
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/igxytdl.sh <<BOOT
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
cd "$PWD"
nohup ./scripts/run-forever.sh > bot.log 2>&1 &
BOOT
chmod +x ~/.termux/boot/igxytdl.sh scripts/run-forever.sh
echo "Done. Put your token in .env (nano .env), then run:  ./scripts/run-forever.sh"
