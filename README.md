# IGXYTDL

A Telegram bot for a group chat. Drop an Instagram, YouTube, TikTok, X (Twitter) or Reddit link and it sends the video or photos back. It runs on a computer, Raspberry Pi or phone that you keep on, since YouTube and Instagram are far less likely to block a home connection than a cloud server.

<img src="assets/logo-circle.png" width="140" alt="IGXYTDL logo">

## What it does

- Videos come back in the best quality that fits under Telegram's 50 MB limit for bots, with their original proportions (vertical clips stay vertical). If the best version is too big, it tries the next one down, so a long video may end up at 360p.
- A video too long to fit under that limit, even at 240p, comes back as audio only instead of nothing.
- Photo posts and carousels come back as JPG, with a mix of photos and videos sent together as an album.
- Instagram, YouTube, X and Reddit links download as soon as someone posts them. TikTok is off by default, so a TikTok link gets the small menu (best, 1080p, 720p, 480p, 360p, MP3) and nothing happens until someone taps. `/autodownload` changes this per site, for example `/autodownload tiktok on`.
- Files are sent under the video's real title, and an MP3 shows the title and the channel name as well.
- Every video has a button to get its audio as an MP3. The same link's MP3 is sent at most twice per chat, and repeated taps while one is still being prepared do nothing, so nobody can flood the chat.
- If a link can't be downloaded, the bot stays quiet instead of posting an error. The reason is written to the log.
- Share and tracking parts of a link (Instagram's `igsh`, YouTube's `si`, `utm_` and similar) are removed before the bot uses the link, so they aren't sent to the site or repeated in the chat.
- yt-dlp updates itself every day, so YouTube and Instagram changes get picked up without you doing anything.

## Commands

| Command | What it does |
|---|---|
| `/audio <link>` | MP3 straight away |
| `/autodownload` | Shows which sites download instantly in this chat |
| `/autodownload <site> on` or `off` | Changes one site (`instagram`, `x`, `reddit`, `youtube`, `tiktok`, or `all`). Without on/off it flips the current setting |
| `/host` | Says which device is running the bot right now |
| `/id` | Shows the chat ID and your user ID, which you need for the settings file |

## Getting started

[INSTALL.md](INSTALL.md) has step-by-step setup for Windows, Mac, Linux, a Raspberry Pi 4, an Android phone and Docker, plus the settings file, Instagram cookies, updating and troubleshooting.

If a few friends will host the same bot so it stays up when one device is off, read [HOSTING.md](HOSTING.md).

## Good to know

- Reddit needs a login now. Add free API keys (or cookies) and videos, images and galleries all work; the steps are in [INSTALL.md](INSTALL.md#reddit-access).
- X photo and video tweets, YouTube videos and TikTok videos work with no setup. Instagram needs login cookies, covered in [INSTALL.md](INSTALL.md#instagram-login-cookies).
- To send files up to 2 GB instead of 50 MB, see [Files over 50 MB](INSTALL.md#files-over-50-mb). It only works on a single device, not together with shared hosting.
- Set `ALLOWED_CHATS` so only your group can use the bot. The settings are explained in [INSTALL.md](INSTALL.md#the-settings-file).
- Only download things you have the right to, and follow each site's terms.
