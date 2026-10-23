# Setting up the bot on a Raspberry Pi 4 (for a friend hosting it)

You are going to keep a copy of the group's download bot running on your Raspberry Pi. When your Pi is on and online it serves the group; when it is off, someone else's device takes over. It is lightweight (about 70 MB of memory) and only needs the Pi to stay powered and connected to the internet.

**You need from the person who runs the group (send these privately, never in the group chat):**
1. The **bot token** (a long string like `123456:ABC...`). Treat it like a password: anyone with it controls the bot.
2. The **group ID** (a negative number like `-100…`).
3. The code, as `igxytdl-for-friend.zip` or a GitHub invite.

Instagram is optional. Without it your copy still handles YouTube, X and Reddit (Instagram links just fail while your Pi is the active host). If you want Instagram too, add **your own** cookies in the optional step below. Never ask anyone else for their Instagram cookies, and never share yours.

---

## 1. Get the Pi ready (skip if it already runs Raspberry Pi OS)

1. On your computer install **Raspberry Pi Imager** (raspberrypi.com/software).
2. Pick **Raspberry Pi 4**, **Raspberry Pi OS Lite (64-bit)**, your memory card.
3. Click **Next → Edit Settings**: set a hostname (for example `igxytdl-pi`), a username and password, your Wi-Fi (skip for a cable), and turn on **Enable SSH**.
4. Write the card, put it in the Pi, power it on, wait 2 minutes.
5. Open a terminal on your computer and connect (use your own hostname and username):
   ```bash
   ssh YOURUSER@igxytdl-pi.local
   ```
   (Or plug in a keyboard and screen and use the Pi directly.)

## 2. Get the code onto the Pi

**If you received the zip file**, on your computer (replace the names with yours):
```bash
scp ~/Downloads/igxytdl-for-friend.zip YOURUSER@igxytdl-pi.local:~
```
Then on the Pi:
```bash
sudo apt-get install -y unzip
unzip igxytdl-for-friend.zip
cd igxytdl
```

**If you were invited to the GitHub repository**, on the Pi:
```bash
sudo apt-get install -y git
git clone https://github.com/etrntyy/IGXYTDL-for-friends.git igxytdl
cd igxytdl
```
(GitHub asks for your username and a personal access token with read access to the repository as the password.)

## 3. Install

Still in the `igxytdl` folder:
```bash
./scripts/install.sh --service
```
- It asks for your sudo password (to install ffmpeg), then for the **bot token**: paste it and press Enter.
- It installs everything and starts the bot as a background service that also starts on every boot and restarts after crashes.

## 4. Settings

```bash
nano .env
```
Make sure these lines are set (the token line is already filled in):
```
ALLOWED_CHATS=PUT-THE-GROUP-ID-HERE
SHARED_HOSTING=1
HOST_NAME=PUT-A-NAME-HERE        # for example: sam-pi
```
Leave `COOKIES_FILE` empty. Save with `Ctrl+O`, `Enter`; exit with `Ctrl+X`. Then restart:
```bash
sudo systemctl restart igxytdl
```

## 5. Check that it works

```bash
journalctl -u igxytdl -f
```
Within a minute you should see a line saying this device is the active host, or that it is waiting (another device is active). Press `Ctrl+C` to leave the log.

In the group, send `/host`. The bot answers **Running on: …** with the name of whichever device is currently active. To confirm yours works, ask the other host to stop theirs for a moment: `/host` should then show your `HOST_NAME` within about 90 seconds.

## Optional: Instagram with your own login

Use a **throwaway Instagram account**, not your main one. The cookie file is a full login for that account: anyone who has the file can act as that account until you log out of it or change its password.

1. In Chrome, log in to instagram.com with the throwaway account. Make sure you can see the feed.
2. Open the Chrome Web Store and search for **Get cookies.txt LOCALLY**. Click **Add to Chrome**, then **Add extension**.
3. Click the puzzle-piece icon in Chrome's toolbar and pin the extension, so its icon is visible.
4. Open an instagram.com tab and click the extension's icon.
5. Choose the **Netscape** format. This is the format the bot can read.
6. Click **Export**. Chrome saves a file in your Downloads folder, usually named `www.instagram.com_cookies.txt`.
7. Copy it to the Pi (use your own names), then delete it from your Downloads folder:
   ```bash
   scp ~/Downloads/www.instagram.com_cookies.txt YOURUSER@igxytdl-pi.local:~/igxytdl/cookies.txt
   ```
8. On the Pi, lock the file down and point the bot at it:
   ```bash
   chmod 600 ~/igxytdl/cookies.txt
   nano ~/igxytdl/.env
   ```
   Set `COOKIES_FILE=/home/YOURUSER/igxytdl/cookies.txt` (your real username), save, then `sudo systemctl restart igxytdl`.
9. Cookies expire after a while. If Instagram links start failing with "empty media response", export fresh ones and repeat.

Keep the file private: never send it in a chat, never put it in a repo or cloud folder. If it leaks, change that account's password, which logs out every session using it.

## Day to day

| Task | Command |
|---|---|
| See what it's doing | `journalctl -u igxytdl -f` |
| Restart | `sudo systemctl restart igxytdl` |
| Stop | `sudo systemctl stop igxytdl` |
| Update yt-dlp (do this if downloads break) | `cd ~/igxytdl && .venv/bin/pip install -U yt-dlp && sudo systemctl restart igxytdl` |

## Good to know

- **Two copies only if both use `SHARED_HOSTING=1`.** A copy without it will fight the others over the token.
- **Protect the token.** Don't paste it in chats, screenshots or public repos. If you stop hosting, tell the group owner so they can revoke it.
- **The bot only works in the group** named in `ALLOWED_CHATS` (and for the owner's own accounts).
- **Taking turns:** only one device answers at a time. Whichever claimed the bot first stays active until it stops or goes offline, then another takes over within about 90 seconds. Your Pi being on does not make it faster or slower, and it will not share work with the other device.
- **Pi tips:** use the official 5V 3A power adapter, add a cheap heatsink or fan, and use a network cable if you can. The bot itself needs only about 2% of a 4 GB Pi's memory and almost no CPU while idle (see HOSTING.md, section A).
- **Your home connection** is what downloads videos, and your upload speed sends them, so large clips can take a while.
