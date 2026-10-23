# IGXYTDL

A Telegram bot for a group chat. Drop an Instagram, YouTube, X (Twitter) or Reddit link and it sends the video or photos back. It runs on a computer, Raspberry Pi or phone that you keep on, since YouTube and Instagram are far less likely to block a home connection than a cloud server.

![logo](assets/logo-512.png)

## What it does

- Videos come back in the best quality that fits under Telegram's 50 MB limit for bots. If the best version is too big, it tries the next one down, so a long video may end up at 360p.
- Photo posts and carousels come back as JPG, with a mix of photos and videos sent together as an album.
- All four sites download as soon as someone posts a link. `/autodownload` turns that off per site, and then the link gets a small menu (best, 1080p, 720p, 480p, 360p, MP3) and nothing happens until someone taps.
- Every video has a button to get its audio as an MP3.
- yt-dlp updates itself every day, so YouTube and Instagram changes get picked up without you doing anything.

## Commands

| Command | What it does |
|---|---|
| `/audio <link>` | MP3 straight away |
| `/autodownload` | Shows which sites download instantly in this chat |
| `/autodownload <site> on` or `off` | Changes one site (`instagram`, `x`, `reddit`, `youtube`, or `all`). Without on/off it flips the current setting |
| `/host` | Says which device is running the bot right now |
| `/id` | Shows the chat ID and your user ID, which you need for the settings file |

## Getting started

[INSTALL.md](INSTALL.md) has step-by-step setup for Windows, Mac, Linux, a Raspberry Pi 4, an Android phone and Docker, plus the settings file, Instagram cookies, updating and troubleshooting.

If a few friends will host the same bot so it stays up when one device is off, read [HOSTING.md](HOSTING.md).

## Good to know

- Reddit needs a login now. Add free API keys (or cookies) and videos, images and galleries all work; the steps are in [INSTALL.md](INSTALL.md#reddit-access).
- X photo tweets work with no setup. Instagram needs login cookies, covered in [INSTALL.md](INSTALL.md#instagram-login-cookies).
- To lift the 50 MB limit to 2 GB, run Telegram's own [Bot API server](https://github.com/tdlib/telegram-bot-api) and set `TELEGRAM_API_BASE` to its address.
- Set `ALLOWED_CHATS` so only your group can use the bot. The settings are explained in [INSTALL.md](INSTALL.md#the-settings-file).
- Only download things you have the right to, and follow each site's terms.
