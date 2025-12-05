#!/bin/bash

# Trading Bot Startup Script with Auto-Restart
# This script will keep the bot running even if it crashes

cd "$(dirname "$0")"

echo "🤖 Starting Trading Bot with Auto-Restart..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    source venv/bin/activate
    python bot.py
    
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
