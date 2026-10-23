# Hosting the group's bot on your Pi

Thanks for helping out. You'll run a copy of the group's download bot on your Raspberry Pi. While your Pi is on and online it answers the group, and when it's off another device takes over. It barely uses any of the Pi's resources.

The person who runs the group needs to send you three things, privately and never in the group chat:

- the bot token, a long string like `123456:ABC...`
- the group ID, a negative number like `-100...`
- the code, either as `igxytdl-for-friend.zip` or as an invite to the GitHub repository

Then:

1. Follow the [Raspberry Pi 4 section of INSTALL.md](INSTALL.md#raspberry-pi-4). It takes you from a blank memory card to a bot that starts by itself at every boot.
2. When you reach the settings file, make sure `.env` contains these three lines, with your own name in the last one (something like `sam-pi`):
   ```
   ALLOWED_CHATS=the-group-id
   SHARED_HOSTING=1
   HOST_NAME=sam-pi
   ```
3. Restart the bot and send `/host` in the group. It replies "Running on:" followed by the name of whichever device is currently answering. To see yours take over, ask the other host to stop their copy for a moment. It should show your name within about 90 seconds.

How the devices take turns is explained in [HOSTING.md](HOSTING.md#several-devices-one-bot). The short version: only one answers at a time, whoever claimed the bot first keeps it until it goes offline, and nothing is shared between them.

Instagram and Reddit links need a login on your Pi too. Set both up with your own spare accounts: [Instagram login cookies](INSTALL.md#instagram-login-cookies) and [Reddit access](INSTALL.md#reddit-access). Don't ask anyone for their cookies and don't share yours.

Keep the token to yourself, and if you stop hosting, tell the group owner so they can replace it.
