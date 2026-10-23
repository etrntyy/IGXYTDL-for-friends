# Installing the bot

Read the first three sections, then jump to your system: [Windows](#windows), [Mac](#mac), [Linux](#linux), [Raspberry Pi 4](#raspberry-pi-4), [Android](#android-termux) or [Docker](#docker). Instagram cookies, Reddit access, updating and troubleshooting come after.

Nothing here needs open ports or router changes. The bot only connects outward.

## Before you start

1. In Telegram, message @BotFather and send `/newbot`. Answer its questions and it gives you a token that looks like `123456:ABC-DEF...`. Whoever has the token controls the bot, so keep it out of chats and screenshots.
2. Still in @BotFather, send `/mybots`, pick your bot, then Bot Settings, Group Privacy, Turn off. If you skip this the bot can't see links in a group.
3. Add the bot to your group and send `/id` there. It answers with the group's ID, a negative number like `-1001234567890`.

## Get the code

Clone it, or download the ZIP from the repository page (Code, then Download ZIP) and unzip it. The rest of this guide calls the folder `igxytdl`.

```bash
git clone https://github.com/etrntyy/IGXYTDL-for-friends.git igxytdl
cd igxytdl
```

## The settings file

The bot reads its settings from a file called `.env` inside that folder. The installers create it for you from `.env.example`, and you open it in any text editor (`nano .env` on Mac, Linux and Pi, Notepad on Windows). A working one looks like this, without the explanations after the `#`:

```
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...     # from @BotFather
ALLOWED_CHATS=-1001234567890             # the group ID from /id; only this group can use the bot
ALLOWED_USERS=                           # your own user ID (send /id to the bot privately) if you want private chat too
COOKIES_FILE=                            # path to your Instagram cookies.txt, see below
REDDIT_CLIENT_ID=                        # free Reddit API key, see Reddit access below
REDDIT_CLIENT_SECRET=
HOST_NAME=                               # name that /host shows, defaults to the computer's name
SHARED_HOSTING=                          # 1 only when several devices run the bot with one token
```

Write the lines with no spaces around `=` and no quotes. If `ALLOWED_CHATS` and `ALLOWED_USERS` are both empty, anyone who finds the bot can use it. Restart the bot after any change; the command for each system is in [Starting, stopping and updating](#starting-stopping-and-updating).

## Windows

1. Install Python 3.12 or newer from python.org/downloads. On the first screen of the installer tick "Add python.exe to PATH". Afterwards, `python --version` in Command Prompt should print a version.
2. Put the unzipped code in a plain folder such as `C:\IGXYTDL`. Avoid folders that sync to OneDrive.
3. Double-click `run.bat`. The first run builds a private Python environment and installs everything, which takes a few minutes. Then Notepad opens the settings file. Fill it in, save, close Notepad and press a key in the black window.
4. When you see "Application started", send `/start` to the bot. Leave the window open (minimising is fine). If the bot crashes, `run.bat` starts it again after 10 seconds.
5. To start with Windows, make a shortcut to `run.bat` (right-click, Show more options, Create shortcut), press `Win+R`, type `shell:startup` and drop the shortcut into that folder.
6. To keep the laptop from sleeping, open Settings, System, Power & battery and set sleep to Never while plugged in. For the lid, use Control Panel, Power Options, "Choose what closing the lid does" and pick Do nothing.

The bot downloads its own ffmpeg if none is installed. If video merging or MP3 still fails, run `winget install Gyan.FFmpeg` and restart `run.bat`.

## Mac

1. You need Python 3.10 or newer. The installer from python.org works, or `brew install python` if you use Homebrew. Check with `python3 --version`.
2. In the `igxytdl` folder run the installer. It makes the environment, installs the packages and asks for your token (paste it and press Enter, nothing shows as you type):
   ```bash
   ./scripts/install.sh
   ```
3. Fill in the rest of `.env`.
4. To run the bot in the background, start it at every login and restart it after crashes:
   ```bash
   ./scripts/mac-service.sh install
   ```
5. Send `/start` to the bot. If nothing comes back, `./scripts/mac-service.sh logs` shows what it's doing.

The service also stops the Mac from idle-sleeping while it's plugged in. A closed MacBook lid still puts it to sleep, and the bot picks up again when you open it. For a lid-closed setup you need an external display and power (clamshell mode). To try the bot without installing anything, use `./scripts/run-forever.sh` in a Terminal window instead of step 4.

If the log says "Operation not permitted", macOS is blocking background jobs from that folder. Move the `igxytdl` folder into your home folder and run step 4 again.

To remove the service: `./scripts/mac-service.sh uninstall`.

## Linux

This is written for Ubuntu, Debian and Mint. Other distributions are covered at the end.

1. Install git with `sudo apt-get install -y git`, get the code as described earlier, then run this inside the folder:
   ```bash
   ./scripts/install.sh --service
   ```
   It installs ffmpeg and Python's venv support (it asks for your sudo password), builds the environment, asks for your token, and creates a system service that starts at boot and restarts after a crash.
2. Edit `.env` and restart the service.
3. Follow the log with `journalctl -u igxytdl -f` until you see "Application started", then press Ctrl+C and send `/start` to the bot.

Running it by hand is also fine for a test: `./scripts/run-forever.sh`.

On Fedora, install `git python3 python3-pip` with dnf. On Arch or Manjaro, run `sudo pacman -S --needed git python python-pip ffmpeg`. Then, inside the folder:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cp .env.example .env
```

Edit `.env` and start the bot with `./scripts/run-forever.sh`. To make it start at boot, copy `deploy/igxytdl.service` to `/etc/systemd/system/`, replace `__USER__` and `__DIR__` with your username and the folder's full path, and run `sudo systemctl enable --now igxytdl`. Without a system ffmpeg the bot fetches its own on first start.

## Raspberry Pi 4

A 4 GB Pi 4 Model B is far more than the bot needs, and there's nothing to tune. What helps is the right hardware around it:

- the official 5V 3A USB-C power supply, since weak chargers cause random crashes
- a microSD card of 16 GB or more, A1 or A2 rated (a USB SSD lasts longer under heavy use but isn't required)
- a network cable if you can, because it's steadier than Wi-Fi
- a cheap heatsink or fan, so the Pi doesn't slow itself down when busy

Getting it running:

1. On another computer, install Raspberry Pi Imager from raspberrypi.com/software. Choose Raspberry Pi 4, then Raspberry Pi OS (other), then Raspberry Pi OS Lite (64-bit), then your card.
2. Click Next, then Edit Settings. Set a hostname (`igxytdl-pi` is used below), a username and password, your Wi-Fi if you're not using a cable, and under Services turn on SSH with password login. Write the card.
3. Put the card in the Pi, plug in network and power, and wait about two minutes. Then connect from your computer, with your own username in place of `YOURUSER`:
   ```bash
   ssh YOURUSER@igxytdl-pi.local
   ```
   If that name isn't found, take the Pi's IP address from your router's device list and use it instead.
4. Update the system:
   ```bash
   sudo apt-get update && sudo apt-get full-upgrade -y
   ```
5. Get the code onto the Pi. With access to the repository, `sudo apt-get install -y git` and clone it as shown earlier. With a ZIP file, copy it over from your own computer and unpack it on the Pi:
   ```bash
   scp ~/Downloads/igxytdl-for-friend.zip YOURUSER@igxytdl-pi.local:~
   ```
   ```bash
   sudo apt-get install -y unzip && unzip igxytdl-for-friend.zip
   ```
6. From here it's the same as [Linux](#linux): run `./scripts/install.sh --service` inside the folder, edit `.env`, restart the service and watch the log.
7. Run `sudo reboot`, wait two minutes and send `/start` again. If the bot answers, it will survive power cuts.

## Android (Termux)

1. Install Termux and Termux:Boot from F-Droid (f-droid.org). The Play Store versions are out of date.
2. In Termux, run `pkg install -y git`, fetch the code the same way, and run the setup script in the folder:
   ```bash
   ./scripts/termux-setup.sh
   ```
3. Run `nano .env`, paste your token and the other settings, save with Ctrl+O and Enter, and leave with Ctrl+X.
4. Start the bot with the same keep-alive script as on Linux, `./scripts/run-forever.sh`.
5. So Android doesn't kill it, open Settings, Apps, Termux, Battery and set it to Unrestricted (the wording differs by brand), keep Termux's notification showing, and leave the phone plugged in and on Wi-Fi.
6. Open the Termux:Boot app once. After that the bot starts by itself when the phone reboots.

## Docker

Install Docker first (Docker Desktop on Windows and Mac, `curl -fsSL https://get.docker.com | sh` on Linux and Pi). Then, in the `igxytdl` folder:

```bash
cp .env.example .env
mkdir -p data
docker compose up -d --build
```

Fill in `.env` before the last command. Settings and the cookies file live in `./data`, and Docker brings the bot back after crashes and reboots. The cookies path inside the container is `/data/cookies.txt`.

## Instagram login cookies

Instagram refuses almost every download from something that isn't logged in, and the bot can't log in on its own. You give it a copy of a login session (cookies) taken from your browser. YouTube, X and Reddit don't need this.

Use a throwaway Instagram account, not your main one. The cookies file is a full login: whoever holds it can use that account until the session is logged out, with no password or 2FA code.

Export the cookies from Chrome, on any computer:

1. Log in to instagram.com with the throwaway account and make sure you can see the feed. Use the Chrome profile that has that account, so you don't export your main one by accident.
2. In the Chrome Web Store, search for "Get cookies.txt LOCALLY", click Add to Chrome, then Add extension.
3. Click the puzzle-piece icon in the toolbar and pin the extension.
4. Open an instagram.com tab and click the extension's icon.
5. Choose the Netscape format, which is the one the bot reads.
6. Click Export. Chrome saves `www.instagram.com_cookies.txt` in Downloads.

Move the file next to the bot, name it `cookies.txt`, and delete the original from Downloads so only one copy exists:

| System | Command or step |
|---|---|
| Mac, Linux | `mv ~/Downloads/www.instagram.com_cookies.txt ~/igxytdl/cookies.txt && chmod 600 ~/igxytdl/cookies.txt` |
| Raspberry Pi | From your own computer: `scp ~/Downloads/www.instagram.com_cookies.txt YOURUSER@igxytdl-pi.local:~/igxytdl/cookies.txt`, then on the Pi `chmod 600 ~/igxytdl/cookies.txt` |
| Windows | Move the file into `C:\IGXYTDL` and rename it `cookies.txt` |
| Docker | Put it in the `data` folder as `cookies.txt` (no `.env` change needed) |

Then point `COOKIES_FILE` in `.env` at the full path, for example `/home/YOURUSER/igxytdl/cookies.txt` or `C:\IGXYTDL\cookies.txt`, and restart the bot.

Cookies expire after a while. When Instagram links start failing with "empty media response", export fresh ones and replace the file.

A few rules for the cookies file:

- Don't send it in a chat or email, and keep it out of repositories, zips and synced folders such as Drive, Dropbox or iCloud. It's already in `.gitignore`.
- Everyone who hosts the bot uses their own account and their own file. A device with no cookies still serves the other three sites.
- Turn on two-factor login for the throwaway account. It won't stop a stolen cookies file from working, but it stops anyone from signing in with the password or changing the password and email, so you can still recover the account.
- Only people with access to the device can read the file, so treat the device accordingly.
- If it leaks, or you stop using it, change that account's password and then log out every session (Instagram, Settings, Accounts Center, Password and security, Where you're logged in). The old cookies stop working straight away. Delete the file afterwards.
- Every Instagram link sent to the group is fetched as that account. If the account follows private accounts, anyone in the group can download their posts, and Instagram sees the activity coming from the host's connection. Follow nobody private with it.
- Run only the code from this repository. A modified copy could send your cookies somewhere else.

## Reddit access

Reddit now wants a login before it shows most posts, so a Reddit link can fail with "Account authentication is required". A free API key lets the bot fetch Reddit videos, images and galleries through Reddit's official API instead.

1. Log in to reddit.com, open reddit.com/prefs/apps and click "create another app".
2. Give it any name, choose "script", and enter `http://localhost:8080` as the redirect URI (it's never used).
3. Click create. The client ID is the short string under the app's name, and the secret is labelled "secret".
4. Put them in `.env` as `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`, then restart the bot.

Reddit has started reviewing new apps, so it may ask for approval or refuse. The other way in is cookies: export reddit.com the same way as Instagram above, then paste the new lines into the same `cookies.txt` underneath the existing ones (leave out the `# Netscape` header line). Use a spare Reddit account for this, and the same rules apply as for Instagram.

## Starting, stopping and updating

yt-dlp keeps itself current. The bot runs `pip install -U yt-dlp` each time it starts and again every 24 hours. If a newer version arrived, it waits until no download is running, shuts down cleanly and starts itself again to load it. That restart doesn't depend on the service, `run.bat` or Docker. If the update fails (no internet, say), it logs a warning and carries on with the version it has. `AUTO_UPDATE_YTDLP=0` in `.env` turns this off, and `YTDLP_UPDATE_HOURS=12` changes the interval (`0` means only at start).

Everyday jobs:

| | Windows | Mac | Linux and Pi |
|---|---|---|---|
| Logs | the black window | `./scripts/mac-service.sh logs` | `journalctl -u igxytdl -f` |
| Restart | close the window, double-click `run.bat` | `./scripts/mac-service.sh restart` | `sudo systemctl restart igxytdl` |
| Stop | close the window | `./scripts/mac-service.sh uninstall` | `sudo systemctl stop igxytdl` |
| Remove it | delete the folder and the startup shortcut | `./scripts/mac-service.sh uninstall`, delete the folder | `sudo systemctl disable --now igxytdl && sudo rm /etc/systemd/system/igxytdl.service`, delete the folder |

To update yt-dlp right away, run `pip install -U yt-dlp` from inside the folder and restart the bot. The pip command lives at `.venv/bin/pip` on Mac, Linux and Pi, at `.venv\Scripts\pip` on Windows, and is plain `pip` in Termux. To update the bot itself, run `git pull` (or unpack a new ZIP and keep your `.env`) and restart. In Termux, "restart" means Ctrl+C and `./scripts/run-forever.sh` again. With Docker, `docker compose up -d --build` rebuilds the image and `docker compose logs -f` follows the log.

## Troubleshooting

| What you see | What to do |
|---|---|
| `python` isn't recognised on Windows | Reinstall Python with "Add python.exe to PATH" ticked |
| `Could not resolve hostname igxytdl-pi.local` | Give the Pi another minute to boot, or connect by IP address as described in the Pi section |
| The bot ignores links in the group | Group Privacy is still on (turn it off, then remove and re-add the bot), or `ALLOWED_CHATS` holds the wrong ID. Send `/id` in the group to check |
| `Conflict: terminated by other getUpdates request` | Another copy is running with the same token. Stop it, or set `SHARED_HOSTING=1` on all of them |
| YouTube says "Sign in to confirm you're not a bot" | Force a yt-dlp update, wait a while, or add cookies from a YouTube login |
| Instagram says "empty media response" | The cookies are missing, expired or from a logged-out session. Export new ones |
| Reddit says "Account authentication is required" or "needs a login" | Add Reddit API keys or cookies, see [Reddit access](#reddit-access) |
| A video is missing or low quality | Telegram limits bots to 50 MB, so very long videos only fit at 360p or lower |
| The service won't start on Linux or Pi | `journalctl -u igxytdl -n 50` shows why. A wrong or empty token in `.env` is the usual cause |
