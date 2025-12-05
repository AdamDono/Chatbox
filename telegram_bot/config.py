import os

# Deriv Credentials
DERIV_APP_ID = 1089  # Public App ID for testing/development
DERIV_API_TOKEN = "9HYOiDPbahTFCeT"

# Telegram Credentials
TELEGRAM_BOT_TOKEN = "8348100670:AAHcTb-5bkl3jv5IS8Ab1oVJuetc6c0gwfg"
ALLOWED_CHAT_IDS = [7292387668] # User's Chat ID

# Trading Settings
STAKE_AMOUNT = 0.35  # Minimum stake
DURATION_SECONDS = 180 # 3 minutes
SYMBOLS = {
    "Boom 1000": "BOOM1000",
    "Boom 500": "BOOM500",
    "Crash 1000": "CRASH1000",
    "Crash 500": "CRASH500",
    "US Tech 100 (Nasdaq)": "OTC_NDX"
}

# Spike Thresholds (Points)
SPIKE_THRESHOLD = 1.0  # Lowered to catch ALL spikes (even small ones)

