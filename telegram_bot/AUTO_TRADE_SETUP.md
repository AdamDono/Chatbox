# Auto-Trading Setup Guide - Demo Account

## Step 1: Get Your Demo API Token

1. **Open Deriv**: Go to https://app.deriv.com
2. **Switch to Demo**: 
   - Look at the top right corner
   - Click on your account balance
   - Select "Demo" account (should show virtual money like $10,000)
3. **Go to API Token Settings**:
   - Click the hamburger menu (☰) top left
   - Click "Settings"
   - Click "API Token" in the left sidebar
4. **Create New Token**:
   - Click "Create new token"
   - Name it: "Trading Bot Demo"
   - Select these scopes:
     - ✅ Read
     - ✅ Trade
     - ✅ Trading information
   - Click "Create"
5. **Copy the Token**: 
   - You'll see a long string like: `a1-AbCdEfGh123456789...`
   - **Copy it immediately** (you can't see it again!)

---

## Step 2: Update config.py

Open the file: `/Users/dam1mac89/Desktop/Chatbox/telegram_bot/config.py`

Replace the current `DERIV_API_TOKEN` with your demo token:

```python
# Deriv Credentials
DERIV_APP_ID = 1089
DERIV_API_TOKEN = "PASTE_YOUR_DEMO_TOKEN_HERE"  # ← Replace this
```

**Save the file** (Cmd+S)

---

## Step 3: Enable Auto-Trading

I'll do this for you automatically in the next step.

---

## Step 4: Restart the Bot

I'll restart the bot for you after you provide the demo token.

---

## What to Expect

Once auto-trading is enabled:

1. **Signal Received**: Bot detects a spike/crash
2. **Trade Placed**: Bot automatically places the trade on Deriv
3. **Telegram Alert**: You get a message saying "✅ Trade Auto-Executed"
4. **Check Results**: Go to Deriv → Reports → Statement to see trades

---

## Safety Checks

✅ **Demo Account Only**: Make sure you're using the demo token
✅ **Virtual Money**: Demo account uses fake money ($10,000 virtual)
✅ **No Risk**: You can't lose real money on demo
✅ **Test Period**: Run for at least 1 week before considering real account

---

## Ready?

**Please provide your demo API token** and I'll configure everything for you!

You can paste it here or update `config.py` yourself, then let me know.
