# Deriv Trading Bot - Setup & Usage Guide

## 📋 Overview

An automated Telegram bot that monitors **Boom** and **Crash** indices on Deriv, detects spikes/crashes, and sends trading signals with Stop Loss and Take Profit levels.

**Key Features**:
- 🔔 Real-time spike/crash detection
- 📊 M15 chart analysis with technical indicators
- 💰 Automated signals with SL/TP (2:1 Risk/Reward)
- 🔄 Auto-restart on crashes
- 📱 Telegram notifications

---

## 🚀 Quick Start

### 1. Prerequisites

- **macOS** (or Linux/Windows with minor adjustments)
- **Python 3.9+**
- **Deriv Account** with API access
- **Telegram Bot Token**

### 2. Installation

```bash
# Navigate to the project directory
cd /Users/dam1mac89/Desktop/Chatbox/telegram_bot

# Create virtual environment (if not already created)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Edit `config.py` to set your credentials:

```python
# Deriv API Token
DERIV_API_TOKEN = "YOUR_DERIV_API_TOKEN"

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Your Telegram Chat ID
ALLOWED_CHAT_IDS = [YOUR_CHAT_ID]

# Trading Settings
STAKE_AMOUNT = 0.35  # Minimum stake
DURATION_SECONDS = 180  # 3 minutes
SPIKE_THRESHOLD = 5.0  # Sensitivity (points)
```

**How to get your Chat ID**:
1. Start the bot (it will fail to send messages initially)
2. Send any message to your bot on Telegram
3. Check the terminal logs for: `Received message from Chat ID: 123456789`
4. Add that number to `ALLOWED_CHAT_IDS`

### 4. Run the Bot

**Option A: Simple Run**
```bash
source venv/bin/activate
python bot.py
```

**Option B: Auto-Restart (Recommended)**
```bash
./start_bot.sh
```

**Option C: Background Mode (24/7)**
```bash
nohup ./start_bot.sh > bot.log 2>&1 &
```

---

## 📱 Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Start monitoring for signals |
| `/stop` | Stop monitoring |
| `/status` | Check connection status |
| `/prices` | View current prices for all symbols |
| `/nasdaq` | Get M15 chart analysis for Nasdaq |

---

## 🎯 Trading Strategy

### Boom Indices (500, 1000)
- **Trigger**: Price spikes UP > 5 points
- **Action**: **SELL** (3 minutes)
- **Logic**: After a spike, price typically retraces down

### Crash Indices (500, 1000)
- **Trigger**: Price crashes DOWN > 5 points
- **Action**: **BUY** (3 minutes)
- **Logic**: After a crash, price bounces/reverses up

### Signal Format
```
🚨 TRADE SIGNAL 🚨

Symbol: BOOM1000
Direction: SELL (3 min)

Entry: 1234.56
Stop Loss: 1249.56
Take Profit: 1204.56

Risk/Reward: 1:2.0
Spike Size: 8.50 points

⏳ Signal Only - Manual Entry Required
```

---

## ⚙️ Configuration Options

### Auto-Trading vs Signal-Only

**Current Mode**: Signal-Only (manual entry required)

To enable **auto-trading**:
1. Open `bot.py`
2. Change: `AUTO_TRADE = False` to `AUTO_TRADE = True`
3. Restart the bot

⚠️ **Warning**: Auto-trading will execute trades automatically. Test on a demo account first!

### Adjusting Sensitivity

In `config.py`:
```python
SPIKE_THRESHOLD = 5.0  # Lower = more signals, Higher = fewer signals
```

- **5.0** (default): Balanced
- **3.0**: More sensitive (more signals)
- **10.0**: Less sensitive (fewer signals)

---

## 🔧 Troubleshooting

### Bot Not Receiving Messages

**Issue**: "Waiting for data..." on `/prices`

**Solution**:
1. Check if the bot is running: `ps aux | grep bot.py`
2. Check logs: `tail -f bot.log`
3. Restart: `pkill -f bot.py && ./start_bot.sh`

### Connection Errors

**Issue**: "Listen Error: Reconnecting..."

**Solution**: The bot auto-reconnects. If it persists:
1. Check your internet connection
2. Verify Deriv API token is valid
3. Check Deriv API status: https://api.deriv.com

### No Signals Received

**Possible Causes**:
1. Bot is not started (`/start` command not sent)
2. No spikes/crashes detected (wait longer)
3. Spike threshold too high (adjust in `config.py`)

### Bot Crashes

The bot has auto-restart enabled. Check `bot.log` for errors:
```bash
tail -f /Users/dam1mac89/Desktop/Chatbox/telegram_bot/bot.log
```

---

## 📂 Project Structure

```
telegram_bot/
├── bot.py                 # Main bot logic
├── deriv_client.py        # Deriv API WebSocket client
├── chart_analyzer.py      # Chart generation & analysis
├── config.py              # Configuration settings
├── start_bot.sh           # Auto-restart script
├── requirements.txt       # Python dependencies
├── KEEP_RUNNING.md        # 24/7 operation guide
└── README.md              # This file
```

---

## 🛡️ Keeping the Bot Running 24/7

See [KEEP_RUNNING.md](KEEP_RUNNING.md) for detailed instructions on:
- Running in background mode
- Auto-start on Mac boot (LaunchAgent)
- Using `screen` or `tmux`
- Monitoring and logs

---

## 📊 Monitored Symbols

- Boom 1000 Index (`BOOM1000`)
- Boom 500 Index (`BOOM500`)
- Crash 1000 Index (`CRASH1000`)
- Crash 500 Index (`CRASH500`)
- US Tech 100 / Nasdaq (`OTC_NDX`)

---

## ⚠️ Risk Disclaimer

**This bot is for educational purposes only.**

- Trading involves significant risk
- Past performance does not guarantee future results
- Always test on a demo account first
- Never trade with money you can't afford to lose
- The 10% daily profit target is extremely aggressive and unrealistic for consistent trading

---

## 🆘 Support

If you encounter issues:

1. Check the logs: `tail -f bot.log`
2. Verify configuration in `config.py`
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
4. Test Deriv connection manually
5. Check Telegram bot token is valid

---

## 📝 License

This project is for personal use only.

---

**Happy Trading! 🚀**
