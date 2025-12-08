#!/bin/bash

# Trading Bot Startup Script with Auto-Restart
# This script will keep the bot running even if it crashes

cd "$(dirname "$0")"

echo "🤖 Starting Trading Bot with Auto-Restart..."
echo "Press Ctrl+C to stop"
echo ""

# Kill any existing bot instances to prevent duplicates
echo "🔍 Checking for existing bot instances..."
if pgrep -f "bot.py" > /dev/null; then
    echo "⚠️  Found existing bot instances. Killing them..."
    pkill -f "bot.py"
    sleep 2
    echo "✅ Old instances terminated"
else
    echo "✅ No existing instances found"
fi

echo ""
echo "🚀 Starting fresh bot instance..."
echo ""

while true; do
    source venv/bin/activate
    python3 bot.py 2>> bot_error.log
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Bot exited normally."
        break
    else
        echo ""
        echo "❌ Bot crashed with exit code $EXIT_CODE"
        echo "🔄 Restarting in 10 seconds..."
        echo "   (Press Ctrl+C to cancel)"
        sleep 10
    fi
done

echo "Bot stopped."
