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
    # Also kill other start_bot.sh instances (careful not to kill self if possible, 
    # but pkill might kill us too if we are not careful. 
    # Better approach: rely on user to not run it twice or just kill bot.py is usually enough if we don't have multiple wrappers.
    # Actually, we should just inform the user or use a lockfile.
    # But for now, let's just kill bot.py which effectively stops the logic, 
    # though the wrapper loop might restart it.
    
    # Kill other start_bot.sh instances but NOT this one ($$)
    # We use pgrep to find PIDs and filter out our own PID
    pgrep -f "start_bot.sh" | grep -v $$ | xargs kill 2>/dev/null
    # Wait a bit
    sleep 2
    
    # If we killed ourselves (start_bot.sh), we won't reach here. 
    # But since we are running this script, we want to be the ONE running.
    # A better way is using a lock dir.
    
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
