#!/bin/bash

# VPS Setup Script for Trading Bot
# Run this on your Ubuntu/Debian server to set up the environment

echo "🚀 Setting up Trading Bot Environment..."

# 1. Update System
echo "🔄 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Python & Utilities
echo "🐍 Installing Python 3, pip, and screen..."
sudo apt-get install -y python3 python3-pip python3-venv screen git

# 3. Create Virtual Environment
echo "🛠 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 4. Install Dependencies
echo "📦 Installing Python libraries..."
# We manually list them to avoid needing to copy requirements.txt first if not present
pip install python-telegram-bot websockets pandas mplfinance TA-Lib six tomli typing_extensions

echo ""
echo "✅ Setup Complete!"
echo "Next Steps:"
echo "1. Upload your bot files (bot.py, config.py, etc.) to this folder."
echo "2. Run './start_bot.sh' to start the bot."
