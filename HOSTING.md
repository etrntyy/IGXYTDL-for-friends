# Hosting the bot on your own device

The bot runs on any device that stays on and online. Instagram and YouTube work best from a home internet connection, which is why this guide skips cloud servers.

**You need first**
1. A bot token: in Telegram, message **@BotFather**, send `/newbot` (or `/mybots` → your bot → **API Token**).
2. Your group's ID: add the bot to the group, send `/id` there (a negative number like `-1001234567890`).
3. In @BotFather: `/mybots` → your bot → **Bot Settings → Group Privacy → Turn off**, then remove and re-add the bot to the group. Without this the bot can't see links in the group.

**The settings** live in a file named `.env` in the bot folder (created from `.env.example`):

```
TELEGRAM_BOT_TOKEN=123456:ABC...        # required
ALLOWED_CHATS=-1001234567890            # only this group can use the bot
ALLOWED_USERS=123456789                 # optional: also allow these people in private chat (get your ID with /id)
COOKIES_FILE=/full/path/to/cookies.txt  # optional: Instagram login cookies (see README)
```

Pick your device:

| Device | Section |
|---|---|
| Raspberry Pi, Linux laptop or server | [A](#a-raspberry-pi--linux) |
| Android phone | [B](#b-android-phone-termux) |
| Windows laptop | [C](#c-windows-laptop) |
| Mac | [D](#d-mac) |
| Anything with Docker | [E](#e-docker-any-device) |

Several people hosting the same bot: see [F](#f-several-people-hosting-the-same-bot).

---

## A. Raspberry Pi / Linux

Works on Raspberry Pi OS, Ubuntu, Debian.

```bash
git clone https://github.com/etrntyy/IGXYTDL.git igxytdl
cd igxytdl
./scripts/install.sh --service
```

The script installs ffmpeg and Python packages, asks for your bot token, and starts the bot as a system service. It starts at every boot and restarts after crashes.

Then edit the rest of the settings and restart:

```bash
nano .env
sudo systemctl restart igxytdl
```

- Watch logs: `journalctl -u igxytdl -f`
- Stop it: `sudo systemctl stop igxytdl`
- Update: `cd igxytdl && git pull && .venv/bin/pip install -U -r requirements.txt yt-dlp && sudo systemctl restart igxytdl`

### What hardware it needs

The bot is light. A Raspberry Pi 4 with 4 GB is plenty (these are estimates; they depend on the videos).

| | Typical use |
|---|---|
| RAM, idle | about 70–100 MB (about 2% of 4 GB) |
| RAM, while downloading | a few hundred MB at peak |
| CPU, idle | about 0% |
| CPU, one download | one core busy for seconds to a minute or two |
| Free disk | about 1 GB (temporary files are deleted after sending) |
| Internet | 5 Mbps upload at the least, 20+ Mbps comfortable |

Three or four downloads at once fit comfortably. The real limit is your internet connection: long videos can mean a large download, and each video sent is up to 50 MB of upload.

### Raspberry Pi tips

- **Power supply:** use the official 5V 3A adapter. A weak charger causes random crashes when the Pi is busy.
- **Cooling:** a cheap heatsink or small case fan stops the Pi 4 throttling under load. Idle, it stays cool.
- **Storage:** a decent A1/A2 memory card is fine. A USB SSD lasts longer under heavy use but isn't required.
- **Keep it online:** a wired network cable is more reliable than Wi-Fi. Restart the router if the bot goes silent after a power cut; the bot reconnects by itself.
- **Updates:** if downloads break, update yt-dlp first (see the command above), since YouTube and Instagram change often.

## B. Android phone (Termux)

1. Install **Termux** and **Termux:Boot** from **F-Droid** (f-droid.org). Do not use the Play Store versions, they are outdated.
2. Open Termux and run:
   ```bash
   pkg install -y git
   git clone https://github.com/etrntyy/IGXYTDL.git igxytdl
   cd igxytdl
   ./scripts/termux-setup.sh
   nano .env
   ```
   Paste your token after `TELEGRAM_BOT_TOKEN=`, save with `Ctrl+O`, `Enter`, exit with `Ctrl+X`.
3. Start the bot: `./scripts/run-forever.sh`
4. Stop Android from killing it:
   - Settings → Apps → Termux → Battery → **Unrestricted** (wording varies by brand).
   - Pull down the notification shade and keep Termux's notification (it holds the wake lock).
   - Keep the phone plugged in and on Wi-Fi.
5. Open the **Termux:Boot** app once. After that the bot starts by itself when the phone reboots.
6. Update later: `cd igxytdl && git pull && pip install -U -r requirements.txt yt-dlp`, then stop (`Ctrl+C`) and start again.

## C. Windows laptop

1. Install **Python 3.10+** from python.org. Tick **Add python.exe to PATH** in the installer.
2. Download the bot: on github.com/etrntyy/IGXYTDL click **Code → Download ZIP**, then unzip it (or `git clone` if you have git).
3. Double-click **`run.bat`**. First run sets everything up and opens `.env` in Notepad: paste your token, save, close, press a key.
4. Leave the window open. It restarts the bot if it crashes.
5. Start with Windows: press `Win+R`, type `shell:startup`, and put a shortcut to `run.bat` in that folder.
6. Stop the laptop sleeping: Settings → System → Power → Screen and sleep → set **Sleep** to **Never** (when plugged in). Closing the lid: Control Panel → Power Options → "Choose what closing the lid does" → **Do nothing**.

## D. Mac

```bash
git clone https://github.com/etrntyy/IGXYTDL.git igxytdl
cd igxytdl
./scripts/install.sh
nano .env            # check the settings
caffeinate -is ./scripts/run-forever.sh
```

`caffeinate` keeps the Mac awake while the bot runs. A closed MacBook lid still sleeps the machine; use clamshell mode (power + external display) or keep the lid open. To start at login, add a launch agent or use the Login Items setting to open a Terminal running that last command.

## E. Docker (any device)

Needs Docker (Docker Desktop on Windows/Mac, `curl -fsSL https://get.docker.com | sh` on Linux/Pi).

```bash
git clone https://github.com/etrntyy/IGXYTDL.git igxytdl
cd igxytdl
cp .env.example .env     # then edit .env and add your token
mkdir -p data            # put cookies.txt in here if you use Instagram cookies
docker compose up -d --build
```

- Logs: `docker compose logs -f`
- Stop: `docker compose down`
- Update: `git pull && docker compose up -d --build`

Settings and cookies live in `./data`. Docker restarts the bot after crashes and reboots.

---

## F. Several people hosting the same bot

Idea: a few group members each run the bot on their own device. Whoever is online serves the group; if that device goes offline, another one takes over within about 90 seconds.

**How it works.** Telegram only lets one program fetch a bot's messages at a time, so the devices take turns. The active device renews a small marker every 30 seconds; if it stops, the next waiting device claims it. Run `/host` in the group to see which device is answering.

**Which device is active, and can they share the work?**

- There is no priority. The first device to claim the bot stays in charge, and the others wait as backups. A faster or later-starting device does not take over.
- If two devices start at the same moment, each makes a claim, waits a few seconds, and checks who won. The last claim wins, so it is effectively random.
- The active device hands over only when it stops, crashes or loses internet: within about 90 seconds, or under half a minute after a clean shutdown.
- The devices do not share resources. Telegram lets only one program fetch the bot's messages at a time, so only the active device handles links and the backups do nothing. A second device adds reliability, not speed.
- Instagram uses the cookies of whichever device is active (see the cookie notes above), so Instagram links work only while a device with its own cookies is active.

**Setup (every host does the same)**
1. Everyone uses the **same bot token** and the same `ALLOWED_CHATS`.
2. Each host adds to their own `.env`:
   ```
   SHARED_HOSTING=1
   HOST_NAME=alice-pi        # a different name per person, shown by /host
   ```
3. Install and run as described above (sections A to E).
4. Don't run a second copy *without* `SHARED_HOSTING=1`: two plain copies fight over the token and neither works reliably.

**Know before you do this**
- **The token is full control of the bot.** Anyone who has it can read what the bot receives and act as the bot. Share it only with people you trust, and not in the group chat. If someone leaves the group, revoke the token in @BotFather (`/mybots` → API Token → Revoke) and send the new one to the remaining hosts.
- **Failover is not instant.** If the active device crashes, links sent during the gap (up to about 90 seconds) wait and are handled when the next device takes over. If it shuts down normally, the handover takes under half a minute.
- **Each device has its own settings.** `/autodownload` choices and Instagram cookies are stored on the device, so after a handover the bot may behave per that device's settings. Agree on the same choices, and give every host the same `.env`.
- **Instagram cookies:** every host who wants Instagram needs their own `cookies.txt` from their own browser.
- **Downloads in progress** are lost if the device handling them goes offline; resend the link.
- If Telegram refuses the marker the bot uses (the log says "lease unavailable"), it continues as a normal single bot without failover.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Bot doesn't react to links in the group | Group Privacy still on (see top), or the bot was not re-added after turning it off, or `ALLOWED_CHATS` has the wrong ID. |
| `Conflict: terminated by other getUpdates request` in logs | Another copy is running with the same token. Stop it, or set `SHARED_HOSTING=1` on all of them. |
| YouTube says "Sign in to confirm you're not a bot" | Update yt-dlp (`pip install -U yt-dlp`), try again later, or add a YouTube `cookies.txt`. |
| Instagram "empty media response" | Cookies missing, expired or from a logged-out session. Export them again. |
| Files over 50 MB are skipped | Telegram's bot limit. A local Bot API server (`TELEGRAM_API_BASE`) raises it to 2 GB. |
| Nothing works after a router/power cut | The device must reconnect to the internet; the service or `run-forever.sh` restarts the bot. |
