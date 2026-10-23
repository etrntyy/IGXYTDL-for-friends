# Telegram Downloader Bot

Send a YouTube, Instagram, Twitter/X or Reddit link; the bot replies with the video/photos. `/audio <link>` returns MP3.

**Running it on your own always-on device (Pi, Android phone, laptop, Docker, or shared between several people): see [HOSTING.md](HOSTING.md) (includes hardware needs and Raspberry Pi tips).**

## Setup

```bash
brew install ffmpeg            # needed for merging video+audio and for /audio
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env           # then put your @BotFather token in it
python bot.py
```

## Notes

- Telegram bots can upload at most 50 MB; larger files are skipped. Videos are capped at 720p to stay under it. Run a [local Bot API server](https://github.com/tdlib/telegram-bot-api) and set `TELEGRAM_API_BASE` for up to 2 GB.
- Instagram usually needs login cookies: export `cookies.txt` from a logged-in browser and set `COOKIES_FILE`. Use a throwaway account, as heavy use can get it flagged.
- Image posts: Twitter/X photos use the fxtwitter API (no setup). Reddit images and galleries need `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` (free "script" app at reddit.com/prefs/apps); anonymous access is blocked on many networks. Instagram photos and carousels go through yt-dlp and need `COOKIES_FILE`.
- Keep yt-dlp current (`pip install -U yt-dlp`); these sites change often.
- Set `ALLOWED_USERS` and/or `ALLOWED_CHATS` (send `/id` in a group to get its ID) to keep the bot private. With only `ALLOWED_CHATS` set, the bot works for everyone in that group and nowhere else.
- Only download content you have the right to; respect each platform's terms.

## Commands

- `/autodownload`: shows which sites download instantly in this chat.
- `/autodownload <instagram|x|reddit|youtube|all> [on|off]`: change one site (no on/off toggles it). Defaults: all four sites on. When a site is off, its links only get format buttons and nothing downloads until someone presses one. Saved per chat in `settings.json`.
- `/audio <link>`: MP3 straight away.

## Hosting on Render (free)

1. Push this repo to GitHub, then on render.com choose **New → Blueprint** and pick the repo (`render.yaml` sets everything up).
2. When asked, enter `TELEGRAM_BOT_TOKEN` and `ALLOWED_USERS`.
3. In the service's **Environment → Secret Files**, add a file named `cookies.txt` with your exported Instagram cookies.
4. Free web services sleep after ~15 minutes without web traffic. Create a free [UptimeRobot](https://uptimerobot.com) HTTP monitor on the service URL (check every 5 minutes) to keep it awake.
5. Stop any copy of the bot running on your computer: two instances with one token conflict.

Free instances have no persistent disk, so `/autodownload` settings reset on each restart or deploy.
