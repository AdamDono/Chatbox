# Keeping the Bot Running 24/7

## Option 1: Use the Auto-Restart Script (Recommended)

The bot now has built-in auto-restart capabilities:

```bash
cd /Users/dam1mac89/Desktop/Chatbox/telegram_bot
./start_bot.sh
```

This script will:
- ✅ Automatically restart if the bot crashes
- ✅ Reconnect to Deriv if connection is lost
- ✅ Keep running until you press Ctrl+C

**To run in background:**
```bash
nohup ./start_bot.sh > bot.log 2>&1 &
```

**To check if it's running:**
```bash
ps aux | grep bot.py
```

**To stop it:**
```bash
pkill -f bot.py
```

## Option 2: macOS LaunchAgent (Runs on Startup)

To make the bot start automatically when your Mac boots:

1. Create a LaunchAgent file:
```bash
nano ~/Library/LaunchAgents/com.tradingbot.plist
```

2. Paste this content:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tradingbot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/dam1mac89/Desktop/Chatbox/telegram_bot/start_bot.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/dam1mac89/Desktop/Chatbox/telegram_bot/bot.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/dam1mac89/Desktop/Chatbox/telegram_bot/bot_error.log</string>
</dict>
</plist>
```

3. Load the LaunchAgent:
```bash
launchctl load ~/Library/LaunchAgents/com.tradingbot.plist
```

4. Start it:
```bash
launchctl start com.tradingbot
```

**To stop:**
```bash
launchctl stop com.tradingbot
```

**To disable auto-start:**
```bash
launchctl unload ~/Library/LaunchAgents/com.tradingbot.plist
```

## Option 3: Screen/tmux (Terminal Session)

Keep a terminal session running even when you close the window:

```bash
# Install screen (if not installed)
brew install screen

# Start a screen session
screen -S tradingbot

# Run the bot
cd /Users/dam1mac89/Desktop/Chatbox/telegram_bot
./start_bot.sh

# Detach: Press Ctrl+A, then D
# Reattach: screen -r tradingbot
```

## Monitoring

**View logs:**
```bash
tail -f /Users/dam1mac89/Desktop/Chatbox/telegram_bot/bot.log
```

**Check bot status:**
The bot will send you a Telegram message if it restarts after a crash.
