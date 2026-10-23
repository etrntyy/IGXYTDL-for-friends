# Installation guide

Step-by-step setup for **Windows**, **Linux** and the **Raspberry Pi 4 Model B (4 GB)**. Pick your system:

- [Before you start (all systems)](#before-you-start-all-systems)
- [Windows 10 / 11](#windows-10--11)
- [Linux (Ubuntu, Debian, Mint, Fedora, Arch)](#linux)
- [Raspberry Pi 4 Model B, 4 GB](#raspberry-pi-4-model-b-4-gb)
- [Running on more than one device: who is active?](#running-on-more-than-one-device-who-is-active)
- [The settings file (.env)](#the-settings-file-env)
- [Updating, stopping, uninstalling](#updating-stopping-uninstalling)
- [Troubleshooting](#troubleshooting)

For running the bot on several devices at once, see [HOSTING.md](HOSTING.md).

---

## Before you start (all systems)

You need four things:

1. **A bot token.** In Telegram, message **@BotFather**, send `/newbot` and follow the questions. It replies with a token like `123456:ABC-DEF...`. Keep it secret: anyone who has it controls the bot.
2. **Group privacy turned off.** In @BotFather: `/mybots` → your bot → **Bot Settings → Group Privacy → Turn off**. Without this the bot cannot see links sent in a group.
3. **Your group's ID.** Add the bot to your group and send `/id` there. It replies with a negative number such as `-1001234567890`.
4. **The code.** Either `git clone` the repository, or download the ZIP from the repository page (**Code → Download ZIP**) and unzip it.

Optional: your own Telegram user ID (send `/id` to the bot in a private chat) if you want to use the bot outside the group, and a cookies file if you want Instagram (see the README).

You do **not** need to open any ports or change your router. The bot only makes outgoing connections.

---

## Windows 10 / 11

**1. Install Python**
1. Go to python.org/downloads and download the latest **Python 3.12** (or newer) installer for Windows.
2. Run it. On the first screen **tick "Add python.exe to PATH"**, then click **Install Now**.
3. Check it worked: press `Win+R`, type `cmd`, press Enter, and run `python --version`. It should print a version number.

**2. Get the code**
1. Unzip the download into a simple folder such as `C:\IGXYTDL`. Avoid folders that sync to OneDrive.

**3. First run**
1. Open the folder and double-click **`run.bat`**.
2. The first time, it creates a private Python environment and installs everything (a few minutes, needs internet). The bot fetches its own copy of ffmpeg if none is installed.
3. Notepad opens with the settings file. Fill it in as described in [The settings file](#the-settings-file-env), save, close Notepad, and press any key in the black window.
4. The bot starts. You will see "Application started". Send `/start` to the bot in Telegram to test.

Leave the window open; you can minimise it. If the bot crashes, `run.bat` restarts it after 10 seconds. Press `Ctrl+C` or close the window to stop it.

**4. Start automatically when Windows starts**
1. Right-click `run.bat` → **Show more options → Create shortcut**.
2. Press `Win+R`, type `shell:startup`, press Enter.
3. Move the shortcut into the folder that opens.

**5. Stop the PC from sleeping**
1. **Settings → System → Power & battery → Screen and sleep.**
2. Set "When plugged in, put my device to sleep after" to **Never**.
3. Laptops: **Control Panel → Power Options → Choose what closing the lid does → When I close the lid: Do nothing** (for plugged in).

**Optional: install ffmpeg yourself.** If video merging or MP3 fails, open Command Prompt and run `winget install Gyan.FFmpeg`, then restart `run.bat`.

---

## Linux

Tested approach for Ubuntu, Debian and Linux Mint (anything with `apt`). Fedora and Arch commands are below.

**1. Open a terminal and get the code**
```bash
sudo apt-get install -y git
git clone https://github.com/etrntyy/IGXYTDL-for-friends.git igxytdl
cd igxytdl
```
If you downloaded a ZIP instead: `unzip igxytdl-for-friend.zip && cd igxytdl`.

**2. Install and start as a service**
```bash
./scripts/install.sh --service
```
The script:
- installs `ffmpeg`, `python3-venv` and `python3-pip` (asks for your sudo password),
- creates a private Python environment and installs the bot's packages,
- asks for your **bot token** (paste it, press Enter; nothing shows as you type),
- creates a system service that starts at every boot and restarts after a crash.

**3. Fill in the settings**
```bash
nano .env
```
Set the lines described in [The settings file](#the-settings-file-env). Save with `Ctrl+O`, `Enter`, exit with `Ctrl+X`, then:
```bash
sudo systemctl restart igxytdl
```

**4. Check it**
```bash
journalctl -u igxytdl -f
```
Look for "Application started". Press `Ctrl+C` to leave the log. Then send `/start` to the bot.

**Other distributions (no `apt`)**

Fedora:
```bash
sudo dnf install -y git python3 python3-pip
```
Arch / Manjaro:
```bash
sudo pacman -S --needed git python python-pip ffmpeg
```
Then, on either, from inside the `igxytdl` folder:
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cp .env.example .env
```
Edit `.env` (`nano .env`), then run the bot with `./scripts/run-forever.sh`. Without a system ffmpeg, the bot downloads its own copy on first start. To make it start on boot, copy `deploy/igxytdl.service` to `/etc/systemd/system/`, replace `__USER__` with your username and `__DIR__` with the full path of the folder, then `sudo systemctl enable --now igxytdl`.

**Run it without a service (testing):** `./scripts/run-forever.sh` in the folder.

---

## Raspberry Pi 4 Model B, 4 GB

The 4 GB model is more than enough: the bot uses roughly 70–100 MB of memory when idle and a few hundred MB while downloading, with almost no CPU use between downloads. You do not need to change swap or overclock anything.

**What you need**
- Raspberry Pi 4 Model B (4 GB) and the **official 5V 3A USB-C power supply** (cheap chargers cause random crashes).
- A microSD card, 16 GB or more, A1/A2 rated if possible.
- A network cable (more reliable than Wi-Fi) or your Wi-Fi details.
- A heatsink or small fan (optional but recommended).
- A computer to prepare the card.

**1. Write the operating system to the card**
1. On your computer install **Raspberry Pi Imager** (raspberrypi.com/software) and open it.
2. **Device:** Raspberry Pi 4. **Operating system:** *Raspberry Pi OS (other)* → **Raspberry Pi OS Lite (64-bit)**. **Storage:** your card.
3. Click **Next**, then **Edit Settings** (customisation):
   - **Hostname:** `igxytdl-pi`
   - **Username and password:** choose a username (this guide writes it as `YOURUSER`) and a strong password.
   - **Wi-Fi:** your network name and password (skip if you use a cable).
   - **Services → Enable SSH → Use password authentication.**
4. Save, confirm, and write. Wait for it to finish.

**2. Boot the Pi and connect**
1. Put the card in the Pi, connect the cable (if any), then connect power. Wait about 2 minutes for the first boot.
2. On your computer open a terminal (Terminal on Mac/Linux; **Windows Terminal** or PowerShell on Windows) and connect:
   ```bash
   ssh YOURUSER@igxytdl-pi.local
   ```
   Type `yes` the first time, then your password. If `igxytdl-pi.local` is not found, look up the Pi's IP address in your router's device list and use `ssh YOURUSER@THAT-IP`.

**3. Update the system** (a few minutes)
```bash
sudo apt-get update && sudo apt-get full-upgrade -y
```

**4. Get the code onto the Pi**

Option A, from GitHub (needs access to the repository):
```bash
sudo apt-get install -y git
git clone https://github.com/etrntyy/IGXYTDL-for-friends.git igxytdl
cd igxytdl
```
Option B, from the ZIP file. On **your computer** (not the Pi):
```bash
scp ~/Downloads/igxytdl-for-friend.zip YOURUSER@igxytdl-pi.local:~
```
Then on the Pi:
```bash
sudo apt-get install -y unzip
unzip igxytdl-for-friend.zip
cd igxytdl
```

**5. Install and start**
```bash
./scripts/install.sh --service
```
It installs ffmpeg and the packages, asks for your bot token, and sets up a service that starts at boot and restarts on crashes. This takes a few minutes on the Pi.

**6. Fill in the settings**
```bash
nano .env
```
Set the lines in [The settings file](#the-settings-file-env). Save with `Ctrl+O`, `Enter`, exit with `Ctrl+X`, then:
```bash
sudo systemctl restart igxytdl
```

**7. Check it**
```bash
journalctl -u igxytdl -f
```
You should see "Application started". Press `Ctrl+C` to leave. In Telegram send `/start` to your bot, then a YouTube link in the group.

**8. Test that it survives a reboot**
```bash
sudo reboot
```
Wait two minutes, then send `/start` to the bot again. If it answers, the Pi is set up for good.

**Raspberry Pi tips**
- Keep it plugged in, ideally by cable, in a spot with some airflow.
- Under heavy use a heatsink or fan stops the Pi 4 from slowing itself down.
- Heavy use writes temporary video files; a good card (or a USB SSD) lasts longer.
- If downloads stop working, update yt-dlp first: see [Updating](#updating-stopping-uninstalling).
- To use it on several devices at once, set `SHARED_HOSTING=1` and a different `HOST_NAME` on each ([HOSTING.md](HOSTING.md), section F).

---

## Running on more than one device: who is active?

You can run the bot on several devices with the same token (set `SHARED_HOSTING=1` and a different `HOST_NAME` on each; see [HOSTING.md](HOSTING.md), section F). Only one of them answers at a time. Here is how they take turns:

- **There is no priority.** Whichever device claims the bot first stays in charge until it stops, and the others wait as backups. No device is better than another, and the bot does not pick the faster one.
- **One starts first:** it becomes the active host. The second one starts, sees the claim, and waits.
- **Both start at the same moment:** each writes its claim, waits a few seconds, and checks who won. The last claim wins, which is essentially random.
- **The active device stays active** even if the other one is faster or comes online later. It only hands over when the active one stops, crashes or loses internet, and then within about 90 seconds (or under half a minute after a clean shutdown).
- **Resources are not shared.** Telegram lets only one program fetch the bot's messages at a time, so only one device handles links. The backup does nothing, so a second device adds reliability, not extra speed.
- **Instagram:** only the active device uses its own cookies, so Instagram links work only while a device with working cookies is the active one. Send `/host` in the group to see which device is answering.

---

## The settings file (.env)

The settings live in a file named `.env` in the bot's folder. The installer creates it from `.env.example`. These are the lines that matter:

```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...     # required: from @BotFather
ALLOWED_CHATS=-1001234567890             # only this group can use the bot
ALLOWED_USERS=                           # optional: your Telegram user IDs, comma-separated, to also allow private chat
COOKIES_FILE=                            # optional: full path to your Instagram cookies.txt
HOST_NAME=igxytdl-pi                     # optional: name shown by /host
SHARED_HOSTING=                          # set to 1 only if several devices run this bot with the same token
```

Notes:
- Use no spaces around `=` and no quotes. The `# ...` explanations after each line are optional; you can delete them.
- If `ALLOWED_CHATS` and `ALLOWED_USERS` are both empty, **anyone** who finds the bot can use it.
- Restart the bot after changing the file.

---

## Updating, stopping, uninstalling

| | Windows | Linux / Raspberry Pi |
|---|---|---|
| **Update yt-dlp** (do this when downloads break) | `.venv\Scripts\pip install -U yt-dlp`, then restart `run.bat` | `cd ~/igxytdl && .venv/bin/pip install -U yt-dlp && sudo systemctl restart igxytdl` |
| **Update the bot code** | Download the new ZIP, copy over your `.env` | `cd ~/igxytdl && git pull && .venv/bin/pip install -U -r requirements.txt && sudo systemctl restart igxytdl` |
| **Stop** | Close the window or `Ctrl+C` | `sudo systemctl stop igxytdl` |
| **Restart** | Close and double-click `run.bat` | `sudo systemctl restart igxytdl` |
| **Logs** | The black window | `journalctl -u igxytdl -f` |
| **Uninstall** | Delete the folder and the startup shortcut | `sudo systemctl disable --now igxytdl && sudo rm /etc/systemd/system/igxytdl.service`, then delete the folder |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognised (Windows) | Reinstall Python and tick **Add python.exe to PATH**. |
| `ssh: Could not resolve hostname igxytdl-pi.local` | Wait a minute and retry, or use the Pi's IP address from your router. |
| Bot does not react to links in the group | Group Privacy is still on, the bot was not re-added after turning it off, or `ALLOWED_CHATS` has the wrong ID (send `/id` in the group). |
| `Conflict: terminated by other getUpdates request` | Another copy is running with the same token. Stop it, or set `SHARED_HOSTING=1` on all copies. |
| YouTube: "Sign in to confirm you're not a bot" | Update yt-dlp, try again later, or use a YouTube `cookies.txt`. |
| Instagram: "empty media response" | Cookies are missing or expired. Export fresh ones (see the README). |
| Videos over 50 MB are skipped | Telegram's limit for bots. The bot picks a lower quality automatically; very long videos may only fit at 360p or less. |
| Service will not start (Linux/Pi) | Run `journalctl -u igxytdl -n 50` and read the last lines. A missing or wrong token in `.env` is the usual cause. |
