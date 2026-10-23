# Hosting and sharing the bot

Setup for a single device is in [INSTALL.md](INSTALL.md). This page is about choosing where to run it, what it costs your hardware, and what changes when several people run it together.

## Why not a cloud server

YouTube and Instagram block the address ranges that cloud providers use far more often than ordinary home connections. Free hosts also tend to put the app to sleep. A Raspberry Pi, an old laptop or a spare phone at home avoids both problems, and nothing needs to be exposed to the internet because the bot only makes outgoing connections.

## What it asks of the machine

The bot spends nearly all its time waiting. These are estimates, since they depend on the videos people send.

| | Typical use |
|---|---|
| Memory, idle | 70 to 100 MB |
| Memory, downloading | a few hundred MB at peak |
| CPU | close to nothing when idle, one core busy for seconds to a couple of minutes per video |
| Disk | about 1 GB free for temporary files, which are deleted after sending |
| Internet | 5 Mbps upload at the very least, 20 or more is comfortable |

A Pi 3, any phone from the last several years or any laptop is enough, and a Pi 4 with 4 GB has plenty of room. Three or four downloads at once are fine. The real limit is the connection: a long video can be a big download, and each video sent is up to 50 MB of upload.

## Several devices, one bot

A few people can each run the bot on their own device, all with the same bot token. Whoever is online serves the group, and if that device drops off, another one takes over.

Telegram only lets one program fetch a bot's messages at a time, so the devices take turns. The active one renews a small marker every 30 seconds. If it stops, the next device in line claims the marker. Send `/host` in the group to see which device is answering.

How the turns work:

- Nobody has priority. Whichever device claims the bot first keeps it, and a faster or later device doesn't take over.
- If two start at the same moment, each makes a claim, waits a few seconds and checks who won. The last claim wins, which is basically random.
- The active device only gives up when it stops, crashes or loses its connection. The next one takes over within about 90 seconds, or under half a minute after a normal shutdown.
- The devices don't share work. Only the active one handles links and the rest sit idle, so a second device adds reliability, not speed.
- Links sent during a gap are waiting for the next device when it takes over. A download that was half done on the device that dropped is lost, so resend that link.
- If Telegram ever rejects the marker (the log says "lease unavailable"), the bot carries on as a normal single bot with no failover.

To set it up, every host does the same thing:

1. Use the same bot token and the same `ALLOWED_CHATS`.
2. Add `SHARED_HOSTING=1` and a different `HOST_NAME` (like `alice-pi`) to `.env`.
3. Install it as described in [INSTALL.md](INSTALL.md).

Never run a copy without `SHARED_HOSTING=1` next to the others. Two plain copies fight over the token and neither works properly.

Things to agree on first:

- The token gives full control of the bot, so only share it with people you trust, and not in the group chat. If someone leaves, revoke the token in @BotFather (`/mybots`, your bot, API Token, Revoke) and send the new one to the rest.
- `/autodownload` choices and Instagram cookies live on each device. After a handover the bot uses the new device's settings, so it helps if everyone starts from the same `.env`.
- Instagram works only while the active device has working cookies of its own. Each host who wants Instagram sets up their own throwaway account, as described in [INSTALL.md](INSTALL.md#instagram-login-cookies).
