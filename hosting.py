"""Shared hosting: several devices run this bot with the same token, but only one polls Telegram at a time.

The devices coordinate through a small "lease" kept in the bot's own command list for a language nobody
uses (so it never shows in a menu). The active device renews it every RENEW seconds; if it stops (device
off, Wi-Fi gone) the lease expires after TTL seconds and another waiting device takes over.
"""
import asyncio
import logging
import random
import re
import secrets
import signal
import time

from telegram import BotCommand, Update
from telegram.error import BadRequest

log = logging.getLogger("dlbot.hosting")

LEASE_LANG = "ab"  # rarely used language code: the lease entry is invisible to real users
TTL = 90  # seconds without a renewal before another device may take over
RENEW = 30
LEASE_RE = re.compile(r"^h(\d{10})_([a-z0-9_]+)$")


def make_host_id(name: str) -> str:
    clean = re.sub(r"[^a-z0-9]", "", name.lower())[:14] or "host"
    return f"{clean}x{secrets.token_hex(2)}"  # unique per run, fits the 32-char command limit


class Lease:
    def __init__(self, bot, me: str):
        self.bot, self.me = bot, me

    async def read(self) -> tuple[int, str] | None:
        for c in await self.bot.get_my_commands(language_code=LEASE_LANG):
            m = LEASE_RE.match(c.command)
            if m:
                return int(m[1]), m[2]
        return None

    async def write(self, ts: int, owner: str) -> None:
        await self.bot.set_my_commands([BotCommand(f"h{ts:010d}_{owner}", "host lease")], language_code=LEASE_LANG)

    async def try_acquire(self) -> bool:
        cur, now = await self.read(), int(time.time())
        if cur and cur[1] != self.me and now - cur[0] < TTL:
            return False
        await self.write(now, self.me)
        await asyncio.sleep(random.uniform(3, 6))  # let a simultaneous claimant overwrite us, then see who won
        cur = await self.read()
        return bool(cur and cur[1] == self.me)

    async def release(self) -> None:
        try:
            await self.write(0, self.me)  # expired timestamp: the next device takes over immediately
        except Exception as e:
            log.warning("couldn't release lease: %s", e)


async def _sleep(stop: asyncio.Event, seconds: float) -> None:
    try:
        await asyncio.wait_for(stop.wait(), seconds)
    except asyncio.TimeoutError:
        pass


async def run_with_failover(app, host_name: str) -> None:
    me = make_host_id(host_name)
    lease = Lease(app.bot, me)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # Windows: Ctrl+C raises KeyboardInterrupt instead
            pass

    await app.initialize()
    await app.start()
    active, solo, last_ok = False, False, 0.0
    log.info("shared hosting: %s waiting for the lease", me)
    try:
        while not stop.is_set():
            if not active:
                try:
                    got = solo or await lease.try_acquire()
                except BadRequest as e:  # Telegram refused the lease trick: just poll like a normal single bot
                    log.warning("lease unavailable (%s); running without failover", e)
                    solo = got = True
                except Exception as e:
                    log.warning("lease check failed: %s", e)
                    got = False
                if got:
                    await app.updater.start_polling()
                    active, last_ok = True, time.time()
                    log.info("this device (%s) is now the active host", me)
                else:
                    await _sleep(stop, 10 + random.uniform(0, 10))
                continue
            await _sleep(stop, RENEW)
            if stop.is_set() or solo:
                continue
            try:
                cur, now = await lease.read(), int(time.time())
                if cur and cur[1] != me and now - cur[0] < TTL:
                    raise RuntimeError(f"lease taken by {cur[1]}")
                await lease.write(now, me)
                last_ok = time.time()
            except Exception as e:
                log.warning("lease renewal problem: %s", e)
                if time.time() - last_ok > TTL - RENEW or "taken by" in str(e):
                    log.warning("stepping down")
                    await app.updater.stop()
                    active = False
    finally:
        if active:
            await app.updater.stop()
            if not solo:
                await lease.release()
        await app.stop()
        await app.shutdown()
