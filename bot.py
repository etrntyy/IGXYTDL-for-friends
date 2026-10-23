"""Telegram bot that downloads Instagram, YouTube and Twitter/X media via yt-dlp."""
import asyncio
import json
import logging
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def update_ytdlp() -> bool:
    """Upgrade yt-dlp from PyPI (YouTube and Instagram change often); True if the installed version changed."""
    from importlib import invalidate_caches, metadata

    try:
        before = metadata.version("yt-dlp")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "-q", "--disable-pip-version-check", "yt-dlp"],
            check=True, capture_output=True, timeout=300,
        )
        invalidate_caches()
        return metadata.version("yt-dlp") != before
    except Exception as e:  # offline or pip blocked: keep running with what is installed
        logging.getLogger("dlbot").warning("yt-dlp update skipped: %s", e)
        return False


AUTO_UPDATE = os.getenv("AUTO_UPDATE_YTDLP", "1") != "0"
if AUTO_UPDATE:  # at every start, before yt-dlp is imported, so the fresh version is the one used
    update_ytdlp()

import httpx
import yt_dlp
from PIL import Image
from telegram import BotCommand, InlineKeyboardButton, InputMediaPhoto, InputMediaVideo, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

if not shutil.which("ffmpeg"):  # no system ffmpeg (e.g. no Homebrew): use the pip-bundled static build
    import static_ffmpeg

    static_ffmpeg.add_paths()
log = logging.getLogger("dlbot")

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API_BASE = os.getenv("TELEGRAM_API_BASE")  # set when using a local Bot API server (2 GB uploads)
_cookies_src = os.getenv("COOKIES_FILE")
COOKIES = None
if _cookies_src and Path(_cookies_src).is_file():  # yt-dlp rewrites its cookie file; work on a copy so read-only secrets and the original stay intact
    COOKIES = str(Path(tempfile.gettempdir()) / "dlbot_cookies.txt")
    shutil.copyfile(_cookies_src, COOKIES)
    os.chmod(COOKIES, 0o600)  # the copy holds a login session; keep it readable by this user only
ALLOWED = {int(x) for x in os.getenv("ALLOWED_USERS", "").split(",") if x.strip()}
ALLOWED_CHATS = {int(x) for x in os.getenv("ALLOWED_CHATS", "").split(",") if x.strip()}  # group/chat IDs (groups are negative)
UPDATE_HOURS = float(os.getenv("YTDLP_UPDATE_HOURS", "24"))  # 0 = only update at start
RESTART = {"now": False, "downloads": 0}  # downloads in progress; restart waits until it is 0
HOST_NAME = os.getenv("HOST_NAME") or socket.gethostname()  # shown by /host
SHARED_HOSTING = os.getenv("SHARED_HOSTING") == "1"  # several devices share one token, one active at a time
REDDIT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
MAX_MB = int(os.getenv("MAX_MB", "2000" if API_BASE else "50"))
MAX_BYTES = MAX_MB * 1024 * 1024
SETTINGS_FILE = Path(os.getenv("SETTINGS_FILE", Path(__file__).with_name("settings.json")))

URL_RE = re.compile(r"https?://[^\s]+")
SITE_RE = re.compile(
    r"^https?://([\w-]+\.)*(instagram\.com|youtube\.com|youtu\.be|twitter\.com|x\.com|t\.co|fxtwitter\.com|vxtwitter\.com|reddit\.com|redd\.it)/",
    re.I,
)
SITES = {  # name -> (domains, auto-download default)
    "instagram": (("instagram.com",), True),
    "x": (("twitter.com", "x.com", "t.co", "fxtwitter.com", "vxtwitter.com"), True),
    "reddit": (("reddit.com", "redd.it"), True),
    "youtube": (("youtube.com", "youtu.be"), True),
}
SITE_ALIASES = {"twitter": "x", "yt": "youtube", "ig": "instagram", "insta": "instagram"}
YOUTUBE_RE = re.compile(r"(youtube\.com|youtu\.be)", re.I)

VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv"}
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ANIM_EXT = {".gif"}
AUDIO_EXT = {".mp3", ".m4a"}  # other audio types (opus, wav, flac) go as documents

# key -> (button label, kind, max height; None = best available)
FORMATS = {
    "best": ("Best quality", "video", None),
    "p1080": ("1080p", "video", 1080),
    "p720": ("720p", "video", 720),
    "p480": ("480p", "video", 480),
    "p360": ("360p", "video", 360),
    "mp3": ("MP3", "audio", None),
}
LADDER = [None, 1440, 1080, 720, 480, 360, 240]  # tried from the chosen quality downwards until the file fits Telegram's limit
MENU_ROWS = [["best", "p1080", "p720"], ["p480", "p360", "mp3"]]
MENU_TEXT = "Pick a quality (photos always come as JPG):"


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
IMG_EXT_RE = re.compile(r"\.(jpe?g|png|webp|gif)(\?|$)", re.I)


def _get(url: str, **kw) -> httpx.Response:
    r = httpx.get(url, headers={"User-Agent": UA}, follow_redirects=True, timeout=30, **kw)
    r.raise_for_status()
    return r


def _twitter_images(path: str) -> list[str]:
    m = re.search(r"^/([^/]+)/status(?:es)?/(\d+)", path)
    if not m:
        return []
    tweet = _get(f"https://api.fxtwitter.com/{m[1]}/status/{m[2]}").json().get("tweet") or {}
    tweet = tweet.get("quote") if not (tweet.get("media") or {}).get("photos") and tweet.get("quote") else tweet
    return [p["url"] for p in (tweet.get("media") or {}).get("photos", [])]


_reddit_token: dict = {"value": None, "exp": 0.0}


def _reddit_json(path: str) -> list:
    """Post JSON via app-only OAuth when REDDIT_CLIENT_ID/SECRET are set (reliable), else the anonymous endpoint (often blocked)."""
    if REDDIT_ID and REDDIT_SECRET:
        if time.time() > _reddit_token["exp"]:
            r = httpx.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(REDDIT_ID, REDDIT_SECRET),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": "telegram-dl-bot/1.0"},
                timeout=30,
            )
            r.raise_for_status()
            _reddit_token.update(value=r.json()["access_token"], exp=time.time() + r.json()["expires_in"] - 60)
        r = httpx.get(
            f"https://oauth.reddit.com{path}?raw_json=1",
            headers={"Authorization": f"bearer {_reddit_token['value']}", "User-Agent": "telegram-dl-bot/1.0"},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
    r = _get(f"https://old.reddit.com{path}.json?raw_json=1")
    if "json" not in r.headers.get("content-type", ""):
        raise RuntimeError("Reddit blocked anonymous access; set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
    return r.json()


def _reddit_post(url: str) -> dict:
    final = httpx.head(url, headers={"User-Agent": UA}, follow_redirects=True, timeout=30).url  # resolves redd.it and /s/ links
    data = _reddit_json(final.path.rstrip("/"))
    post = data[0]["data"]["children"][0]["data"]
    return (post.get("crosspost_parent_list") or [post])[0]


def _reddit_video_source(post: dict) -> str | None:
    """Where the post's video really lives: Reddit's own stream, or a link to YouTube, X and so on."""
    rv = (post.get("secure_media") or post.get("media") or {}).get("reddit_video") or {}
    rv = rv or ((post.get("preview") or {}).get("reddit_video_preview") or {})
    if rv.get("hls_url") or rv.get("fallback_url"):
        return rv.get("hls_url") or rv["fallback_url"]  # the HLS stream has the sound; the fallback file is silent
    link = post.get("url") or ""
    return link if SITE_RE.match(link) and site_of(link) != "reddit" else None


def _reddit_images(url: str) -> list[str]:
    post = _reddit_post(url)
    meta = post.get("media_metadata") or {}
    if post.get("gallery_data"):
        urls = []
        for item in post["gallery_data"]["items"]:
            s = (meta.get(item["media_id"]) or {}).get("s") or {}
            if s.get("u") or s.get("gif"):
                urls.append(s.get("u") or s["gif"])
        return urls
    if IMG_EXT_RE.search(post.get("url") or "") or post.get("post_hint") == "image":
        return [post["url"]]
    # text posts with inline images
    return [(m["s"].get("u") or m["s"].get("gif")) for m in meta.values() if m.get("s") and m.get("status") == "valid"]


def image_urls(url: str) -> list[str]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if re.search(r"(twitter|x|fxtwitter|vxtwitter)\.com$", host):
        return _twitter_images(parsed.path)
    if re.search(r"(reddit\.com|redd\.it)$", host):
        return _reddit_images(url)
    return []


def to_jpg(path: Path) -> Path:
    """Photos always go out as JPG (GIFs and existing JPGs are left alone)."""
    if path.suffix.lower() in {".png", ".webp", ".jpeg"}:
        out = path.with_suffix(".jpg")
        with Image.open(path) as im:
            im.convert("RGB").save(out, "JPEG", quality=95)
        path.unlink()
        return out
    return path


def download_images(url: str, outdir: Path) -> list[Path]:
    files = []
    for i, src in enumerate(image_urls(url)[:10], 1):
        ext = Path(urlparse(src).path).suffix.lower() or ".jpg"
        f = outdir / f"{i:02d}_img{ext}"
        f.write_bytes(_get(src).content)
        files.append(to_jpg(f))
    return files


def _clear(outdir: Path) -> None:
    for p in outdir.iterdir():
        if p.is_file():
            p.unlink()


def _video(url: str, outdir: Path, height: int | None) -> list[Path]:
    """Highest quality first; if the file is over Telegram's limit, step down to the next quality that fits."""
    for h in LADDER[LADDER.index(height):]:
        files = _ytdlp(url, outdir, "video", h)
        if files and all(f.stat().st_size <= MAX_BYTES for f in files if f.suffix.lower() in VIDEO_EXT):
            return files
        _clear(outdir)
    return []


def download(url: str, outdir: Path, fmt: str) -> list[Path]:
    """Video/audio via yt-dlp; if that finds nothing (image posts), extract the post's images as JPG."""
    _, kind, opt = FORMATS[fmt]
    err = None
    files: list[Path] = []
    try:
        files = _ytdlp(url, outdir, "audio", None) if kind == "audio" else _video(url, outdir, opt)
    except yt_dlp.utils.DownloadError as e:
        err = e
    if not files and site_of(url) == "reddit":  # yt-dlp can't read Reddit pages without a login, the API route can
        try:
            src = _reddit_video_source(_reddit_post(url))
            if src:
                files = _ytdlp(src, outdir, "audio", None) if kind == "audio" else _video(src, outdir, opt)
        except Exception as e:
            log.info("reddit video fallback failed: %s", e)
    if not files and kind != "audio":
        try:
            files = download_images(url, outdir)
        except Exception as e:  # best-effort; report the yt-dlp error instead
            log.info("image fallback failed: %s", e)
    if not files and err:
        if site_of(url) == "reddit" and not (REDDIT_ID and REDDIT_SECRET) and not COOKIES:
            raise yt_dlp.utils.DownloadError("Reddit needs a login now. The bot owner has to add Reddit API keys or cookies (see INSTALL.md).")
        raise err
    return [to_jpg(f) if f.suffix.lower() in PHOTO_EXT else f for f in files]


class _YtLog:
    """Collects yt-dlp errors so they can be reported when nothing downloads."""

    def __init__(self):
        self.errors: list[str] = []

    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): self.errors.append(msg)


def _ytdlp(url: str, outdir: Path, kind: str, opt) -> list[Path]:
    lg = _YtLog()
    opts = {
        "outtmpl": str(outdir / "%(autonumber)02d_%(id)s.%(ext)s"),
        "noplaylist": bool(YOUTUBE_RE.search(url)),  # single video from watch?v=..&list=..
        "playlistend": 10,  # Instagram carousels / Twitter multi-video
        "max_filesize": MAX_BYTES,
        "logger": lg,
        "ignoreerrors": "only_download",  # one bad carousel item shouldn't drop the rest
        "restrictfilenames": True,
    }
    if COOKIES:
        opts["cookiefile"] = COOKIES
    if kind == "audio":
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}]
    else:
        cap = f"[height<={opt}]" if opt else ""
        opts["format"] = f"bv*{cap}+ba/b{cap}/b"
        opts["format_sort"] = ["res", "vcodec:h264", "acodec:aac"]  # highest resolution, then the codec every Telegram app plays
        opts["merge_output_format"] = "mp4"
        opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    done = VIDEO_EXT | PHOTO_EXT | ANIM_EXT | AUDIO_EXT
    # skip leftovers of an aborted download (.part files, separate video/audio streams like .f140.m4a)
    files = sorted(p for p in outdir.iterdir() if p.is_file() and p.suffix.lower() in done and not re.search(r"\.f[\w-]+\.\w+$", p.name))
    if not files and lg.errors:
        raise yt_dlp.utils.DownloadError(lg.errors[-1])
    if lg.errors:
        log.warning("some items failed: %s", lg.errors)
    return files


async def send_group(msg, files: list[Path]) -> None:
    """Send photos/videos together as one Telegram album (2-10 items)."""
    handles = [f.open("rb") for f in files]
    try:
        media = [
            InputMediaVideo(h, supports_streaming=True) if f.suffix.lower() in VIDEO_EXT else InputMediaPhoto(h)
            for f, h in zip(files, handles)
        ]
        await msg.reply_media_group(media, read_timeout=600, write_timeout=600)
    finally:
        for h in handles:
            h.close()


async def send_file(msg, path: Path, as_document: bool = False, markup=None, caption=None):
    ext = path.suffix.lower()
    if path.stat().st_size > MAX_BYTES:
        await msg.reply_text(f"{path.name} is over {MAX_MB} MB, can't send it on Telegram.")
        return None
    with path.open("rb") as f:
        if as_document:
            return await msg.reply_document(f, read_timeout=300, write_timeout=300)
        elif ext in VIDEO_EXT:
            return await msg.reply_video(f, supports_streaming=True, reply_markup=markup, caption=caption, read_timeout=300, write_timeout=300)
        elif ext in ANIM_EXT:
            return await msg.reply_animation(f, read_timeout=300, write_timeout=300)
        elif ext in PHOTO_EXT:
            return await msg.reply_photo(f, read_timeout=120, write_timeout=120)
        elif ext in AUDIO_EXT:
            return await msg.reply_audio(f, read_timeout=300, write_timeout=300)
        else:
            return await msg.reply_document(f, read_timeout=300, write_timeout=300)


def site_of(url: str) -> str | None:
    host = urlparse(url).netloc.lower().split(":")[0]
    return next((n for n, (doms, _) in SITES.items() if any(host == d or host.endswith("." + d) for d in doms)), None)


def _load() -> dict:
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except (OSError, ValueError):
        return {}


def auto_enabled(chat_id: int, site: str | None) -> bool:
    """Per-chat, per-site auto-download switch; falls back to the site's default."""
    if site is None:
        return False
    return _load().get(str(chat_id), {}).get("sites", {}).get(site, SITES[site][1])


def set_auto(chat_id: int, sites: list[str], on: bool) -> None:
    data = _load()
    chat = data.setdefault(str(chat_id), {}).setdefault("sites", {})
    for site in sites:
        chat[site] = on
    SETTINGS_FILE.write_text(json.dumps(data))


def auto_status(chat_id: int) -> str:
    return "\n".join(f"{'✅' if auto_enabled(chat_id, n) else '⛔'} {n}" for n in SITES)


async def autodownload_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """/autodownload [instagram|x|reddit|youtube|all] [on|off] — site alone toggles, nothing shows status."""
    if not allowed(update):
        return
    chat_id = update.effective_chat.id
    args = [a.lower() for a in ctx.args or []]
    usage = "Usage: /autodownload <instagram|x|reddit|youtube|all> [on|off]"
    if not args:
        await update.message.reply_text(f"Auto download (✅ on, ⛔ off):\n{auto_status(chat_id)}\n\n{usage}")
        return
    name = SITE_ALIASES.get(args[0], args[0])
    if name != "all" and name not in SITES or len(args) > 2 or (len(args) == 2 and args[1] not in ("on", "off")):
        await update.message.reply_text(usage)
        return
    targets = list(SITES) if name == "all" else [name]
    on = (args[1] == "on") if len(args) == 2 else not auto_enabled(chat_id, targets[0])
    set_auto(chat_id, targets, on)
    await update.message.reply_text(f"{'Auto download ON' if on else 'Auto download OFF (buttons only)'} for {', '.join(targets)}.\n\n{auto_status(chat_id)}")


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me an Instagram, YouTube, Twitter/X or Reddit link and I'll download it in the best quality that fits Telegram.\n"
        "Photo posts come as JPG.\n"
        "/audio <link> gets just the MP3.\n"
        "/autodownload turns instant downloads on or off per site; when off, you pick 1080p/720p/480p/360p or MP3 with buttons.\n"
        f"Upload limit: {MAX_MB} MB."
    )


def allowed(update: Update) -> bool:
    """Open to all unless ALLOWED_USERS / ALLOWED_CHATS is set; then a listed user or a message in a listed chat passes."""
    if not ALLOWED and not ALLOWED_CHATS:
        return True
    user, chat = update.effective_user, update.effective_chat
    return bool((user and user.id in ALLOWED) or (chat and chat.id in ALLOWED_CHATS))


async def id_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Works everywhere so you can find the IDs to put in .env."""
    await update.message.reply_text(f"Chat ID: {update.effective_chat.id}\nYour user ID: {update.effective_user.id}")


def remember(ctx: ContextTypes.DEFAULT_TYPE, msg, url: str) -> None:
    pending = ctx.bot_data.setdefault("pending", {})
    pending[(msg.chat_id, msg.message_id)] = url
    while len(pending) > 500:
        pending.pop(next(iter(pending)))


async def run_download(ctx: ContextTypes.DEFAULT_TYPE, msg, url: str, fmt: str) -> None:
    RESTART["downloads"] += 1
    try:
        await _run_download(ctx, msg, url, fmt)
    finally:
        RESTART["downloads"] -= 1


async def _run_download(ctx: ContextTypes.DEFAULT_TYPE, msg, url: str, fmt: str) -> None:
    status = await msg.reply_text("Downloading…")
    tmp = Path(tempfile.mkdtemp(prefix="dlbot_"))
    try:
        await ctx.bot.send_chat_action(msg.chat_id, ChatAction.UPLOAD_VIDEO)
        files = await asyncio.to_thread(download, url, tmp, fmt)
        if not files:
            await status.edit_text(f"Nothing downloaded (no matching media, or over {MAX_MB} MB).")
            return
        await status.edit_text("Uploading…")
        mp3_button = InlineKeyboardMarkup([[InlineKeyboardButton("🎵 Get MP3 of this", callback_data="f|mp3")]])
        album = [f for f in files if f.suffix.lower() in VIDEO_EXT | PHOTO_EXT and f.stat().st_size <= MAX_BYTES]
        if len(album) > 1:  # carousel: send all photos and videos together, 10 per album
            for i in range(0, len(album), 10):
                chunk = album[i : i + 10]
                await (send_group(msg, chunk) if len(chunk) > 1 else send_file(msg, chunk[0]))
            if any(f.suffix.lower() in VIDEO_EXT for f in album):
                prompt = await msg.reply_text(f"Want the audio from these videos?\n{url}", reply_markup=mp3_button)
                remember(ctx, prompt, url)
            files = [f for f in files if f not in album]
        for f in files:
            sent = await send_file(msg, f, markup=mp3_button, caption=url)
            if sent and f.suffix.lower() in VIDEO_EXT:  # lets the MP3 button on a video find its source link
                remember(ctx, sent, url)
        await status.delete()
    except yt_dlp.utils.DownloadError as e:
        log.warning("download failed: %s", e)
        reason = re.sub(r"\x1b\[[0-9;]*m", "", str(e)).splitlines()[-1][:300]
        await status.edit_text(f"Couldn't download: {reason}")
    except Exception:
        log.exception("unexpected error")
        await status.edit_text("Something went wrong.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE, fmt: str | None = None) -> None:
    if not allowed(update):
        return
    msg = update.effective_message
    urls = [u for u in URL_RE.findall(msg.text or "") if SITE_RE.match(u)]
    if not urls:
        if fmt or update.effective_chat.type == "private":
            await msg.reply_text("Send a valid Instagram, YouTube, Twitter/X or Reddit link.")
        return
    for url in urls[:3]:
        if fmt or auto_enabled(update.effective_chat.id, site_of(url)):
            await run_download(ctx, msg, url, fmt or "best")
            continue
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(FORMATS[k][0], callback_data=f"f|{k}") for k in row] for row in MENU_ROWS]
        )
        menu = await msg.reply_text(f"{url}\n\n{MENU_TEXT}", reply_markup=keyboard, disable_web_page_preview=True)
        remember(ctx, menu, url)


def url_in_message(msg) -> str | None:
    """The menu/video message carries its source link, so a different device can serve the button press."""
    urls = [u for u in URL_RE.findall(msg.text or msg.caption or "") if site_of(u)]
    return urls[0] if urls else None


async def on_format(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not allowed(update):
        await q.answer()
        return
    key = q.data.split("|", 1)[1]
    url = ctx.bot_data.get("pending", {}).get((q.message.chat_id, q.message.message_id)) or url_in_message(q.message)
    if key not in FORMATS or not url:
        await q.answer("This menu expired, send the link again.", show_alert=True)
        return
    await q.answer(f"{FORMATS[key][0]}…")
    await run_download(ctx, q.message, url, key)


async def ytdlp_update_loop() -> None:
    """Every UPDATE_HOURS: upgrade yt-dlp and, if it changed, restart the bot (when idle) so the new version loads."""
    while UPDATE_HOURS > 0:
        await asyncio.sleep(UPDATE_HOURS * 3600)
        if not await asyncio.to_thread(update_ytdlp):
            continue
        log.info("yt-dlp updated; restarting once downloads finish")
        while RESTART["downloads"]:
            await asyncio.sleep(30)
        RESTART["now"] = True
        signal.raise_signal(signal.SIGINT)  # same graceful stop as Ctrl+C (shared hosting releases its claim)
        return


async def host_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Running on: {HOST_NAME}")


async def audio_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await handle(update, ctx, fmt="mp3")


class _Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    do_HEAD = do_GET

    def log_message(self, *args):
        pass


def serve_health() -> None:
    """Hosts like Render need a listening port, and an uptime pinger hitting it keeps free instances awake."""
    port = os.getenv("PORT")
    if port:
        server = HTTPServer(("0.0.0.0", int(port)), _Health)
        threading.Thread(target=server.serve_forever, daemon=True).start()


def main() -> None:
    serve_health()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # its request lines contain the bot token
    builder = Application.builder().token(TOKEN).concurrent_updates(True)
    if API_BASE:
        builder = builder.base_url(f"{API_BASE}/bot").base_file_url(f"{API_BASE}/file/bot").local_mode(True)
    async def post_init(a: Application) -> None:
        if AUTO_UPDATE:
            a.bot_data["ytdlp_task"] = asyncio.create_task(ytdlp_update_loop())
        await a.bot.set_my_commands([
            BotCommand("autodownload", "Choose which sites download instantly"),
            BotCommand("audio", "Download a link's audio as MP3"),
            BotCommand("help", "How to use the bot"),
        ])

    app = builder.post_init(post_init).build()
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("host", host_cmd))
    app.add_handler(CommandHandler("audio", audio_cmd))
    app.add_handler(CommandHandler("autodownload", autodownload_cmd))
    app.add_handler(CallbackQueryHandler(on_format, pattern=r"^f\|"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    if SHARED_HOSTING:
        import hosting

        asyncio.run(hosting.run_with_failover(app, HOST_NAME))
    else:
        app.run_polling()
    if RESTART["now"]:
        log.info("restarting to load the new yt-dlp")
        os.execv(sys.executable, [sys.executable] + sys.argv)


if __name__ == "__main__":
    main()
