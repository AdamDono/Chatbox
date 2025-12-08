import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import config
from deriv_client import deriv_client
from chart_analyzer import ChartAnalyzer
from datetime import datetime
import os

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Global state
IS_RUNNING = False
AUTO_TRADE = True  # ENABLED: Bot will auto-trade on demo account
APP_INSTANCE = None
chart_analyzer = None
last_prediction_time = {}  # Track last prediction time per symbol
last_trade_time = {}  # Track last trade signal time per symbol

# Daily trade counter with persistence
COUNTER_FILE = '/Users/dam1mac89/Desktop/Chatbox/telegram_bot/daily_counter.txt'

def load_daily_counter():
    """Load daily counter from file"""
    try:
        if os.path.exists(COUNTER_FILE):
            with open(COUNTER_FILE, 'r') as f:
                data = f.read().strip().split(',')
                if len(data) == 2:
                    saved_date = data[0]
                    saved_count = int(data[1])
                    # Check if it's still the same day
                    if saved_date == str(datetime.now().date()):
                        return saved_count
        return 0
    except:
        return 0

def save_daily_counter(count):
    """Save daily counter to file"""
    try:
        with open(COUNTER_FILE, 'w') as f:
            f.write(f"{datetime.now().date()},{count}")
    except Exception as e:
        print(f"Error saving counter: {e}")

daily_trade_count = load_daily_counter()
current_date = datetime.now().date()

# Trade tracking for success rate with persistence
TRADE_HISTORY_FILE = '/Users/dam1mac89/Desktop/Chatbox/telegram_bot/trade_history.json'

def load_trade_history():
    """Load trade history from JSON file"""
    try:
        if os.path.exists(TRADE_HISTORY_FILE):
            import json
            with open(TRADE_HISTORY_FILE, 'r') as f:
                data = json.load(f)
                # Convert timestamp strings back to datetime objects
                for trade in data:
                    trade['timestamp'] = datetime.fromisoformat(trade['timestamp'])
                # Only keep today's trades
                today = datetime.now().date()
                return [t for t in data if t['timestamp'].date() == today]
        return []
    except Exception as e:
        print(f"Error loading trade history: {e}")
        return []

def save_trade_history(history):
    """Save trade history to JSON file"""
    try:
        import json
        # Convert datetime objects to strings for JSON
        data = []
        for trade in history:
            trade_copy = trade.copy()
            trade_copy['timestamp'] = trade['timestamp'].isoformat()
            data.append(trade_copy)
        with open(TRADE_HISTORY_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving trade history: {e}")

trade_history = load_trade_history()  # Load from file
active_trades = {}  # Trades waiting for 3-min validation {symbol: trade_data}

print(f"📊 Loaded {len(trade_history)} trades from history file")

def calculate_streak(history):
    """Calculate current win streak"""
    streak = 0
    # Sort by timestamp descending
    sorted_history = sorted(history, key=lambda x: x['timestamp'], reverse=True)
    
    for trade in sorted_history:
        if trade['status'] == 'success':
            streak += 1
        elif trade['status'] == 'failed':
            break  # Streak broken
        # Ignore pending trades
            
    return streak

def format_duration(seconds):
    """Format seconds into 2m 30s"""
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global IS_RUNNING
    IS_RUNNING = True
    await update.message.reply_text(f"Bot Started! Monitoring Boom/Crash for spikes.\nStake: ${config.STAKE_AMOUNT}\nDuration: {config.DURATION_SECONDS}s")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global IS_RUNNING
    IS_RUNNING = False
    await update.message.reply_text("Bot Stopped. No new trades will be placed.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display daily trade statistics"""
    global daily_trade_count, current_date
    
    msg = f"📊 *Daily Trade Statistics* 📊\n\n"
    msg += f"Date: `{current_date.strftime('%Y-%m-%d')}`\n"
    msg += f"Trades Today: `{daily_trade_count}`\n\n"
    
    if daily_trade_count == 0:
        msg += "No trades yet today. Waiting for signals..."
    else:
        msg += f"Average: `{daily_trade_count / max(1, (datetime.now().hour * 60 + datetime.now().minute) / 60):.1f}` trades/hour"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def tradestats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display trade success statistics"""
    global trade_history
    
    # Filter today's trades
    today = datetime.now().date()
    today_trades = [t for t in trade_history if t['timestamp'].date() == today]
    
    successful = [t for t in today_trades if t['status'] == 'success']
    failed = [t for t in today_trades if t['status'] == 'failed']
    pending = [t for t in today_trades if t['status'] == 'pending']
    
    total = len(today_trades)
    
    msg = f"📈 *Trade Success Statistics* 📈\n\n"
    msg += f"Date: `{today.strftime('%Y-%m-%d')}`\n\n"
    msg += f"Total Signals: `{total}`\n"
    msg += f"✅ Successful (3-min): `{len(successful)}`\n"
    msg += f"❌ Failed (re-triggered): `{len(failed)}`\n"
    msg += f"⏳ Pending: `{len(pending)}`\n\n"
    
    if total > 0:
        completed = len(successful) + len(failed)
        if completed > 0:
            success_rate = (len(successful) / completed) * 100
            msg += f"Success Rate: `{success_rate:.1f}%`\n\n"
        else:
            msg += "Success Rate: Waiting for trades to complete...\n\n"
            
    # Add Streak Info
    streak = calculate_streak(today_trades)
    if streak > 0:
        msg += f"🔥 Current Streak: *{streak} WINS*\n\n"
    
    # Group by symbol
    if today_trades:
        from collections import defaultdict
        symbol_stats = defaultdict(lambda: {'total': 0, 'success': 0, 'failed': 0})
        
        for trade in today_trades:
            symbol_stats[trade['symbol']]['total'] += 1
            if trade['status'] == 'success':
                symbol_stats[trade['symbol']]['success'] += 1
            elif trade['status'] == 'failed':
                symbol_stats[trade['symbol']]['failed'] += 1
        
        msg += "*By Symbol:*\n"
        for symbol, stats in sorted(symbol_stats.items()):
            completed_sym = stats['success'] + stats['failed']
            if completed_sym > 0:
                rate = (stats['success'] / completed_sym) * 100
                msg += f"{symbol}: {stats['success']}/{completed_sym} ({rate:.0f}%)\n"
            else:
                msg += f"{symbol}: {stats['total']} pending\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def reset_daily_counter():
    """Reset daily counter and send summary"""
    global daily_trade_count, current_date, trade_history
    
    if not APP_INSTANCE:
        return
    
    # Calculate success rate for the day
    yesterday = current_date
    yesterday_trades = [t for t in trade_history if t['timestamp'].date() == yesterday]
    successful = [t for t in yesterday_trades if t['status'] == 'success']
    failed = [t for t in yesterday_trades if t['status'] == 'failed']
    
    # Send daily summary
    msg = f"📈 *Daily Summary - {yesterday.strftime('%Y-%m-%d')}* 📈\n\n"
    msg += f"Total Trades: `{daily_trade_count}`\n"
    
    if daily_trade_count == 0:
        msg += "\nNo trades were executed today."
    else:
        completed = len(successful) + len(failed)
        if completed > 0:
            success_rate = (len(successful) / completed) * 100
            msg += f"✅ Successful: `{len(successful)}`\n"
            msg += f"❌ Failed: `{len(failed)}`\n"
            msg += f"Success Rate: `{success_rate:.1f}%`\n\n"
            msg += f"Great job! {daily_trade_count} trading signals were sent."
        else:
            msg += f"\nAll {daily_trade_count} trades are still pending validation."
    
    for chat_id in config.ALLOWED_CHAT_IDS:
        try:
            await APP_INSTANCE.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        except Exception as e:
            print(f"Failed to send daily summary to {chat_id}: {e}")
    
    # Reset counter
    daily_trade_count = 0
    current_date = datetime.now().date()
    print(f"✅ Daily counter reset. New date: {current_date}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = "RUNNING" if IS_RUNNING else "STOPPED"
    await update.message.reply_text(f"Status: {status_msg}\nConnected: {deriv_client.authorized}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check current account balance"""
    await deriv_client.get_balance()
    await asyncio.sleep(0.5)  # Wait for balance update
    msg = f"💰 *Account Balance*\n\n"
    msg += f"Balance: `${deriv_client.balance:.2f} USD`"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 *Current Prices* 📊\n"
    for name, code in config.SYMBOLS.items():
        history = deriv_client.tick_history.get(code, [])
        if history:
            price = history[-1]
            msg += f"{name}: `{price}`\n"
        else:
            msg += f"{name}: Waiting for data...\n"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def analyze_nasdaq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Enhanced M15 Analysis with chart
    code = config.SYMBOLS["US Tech 100 (Nasdaq)"]
    history = deriv_client.tick_history.get(code, [])
    
    if not history or len(history) < 20:
        await update.message.reply_text("Not enough data for Nasdaq analysis yet. Wait a few seconds.")
        return

    trend, action, rsi = chart_analyzer.analyze_trend(history)
    current = history[-1]
    
    # Generate chart
    chart_path = f"/tmp/nasdaq_m15_{int(datetime.now().timestamp())}.png"
    chart_analyzer.generate_chart("US Tech 100 (Nasdaq)", None, chart_path)
    
    msg = f"📈 *Nasdaq (US Tech 100) M15 Analysis* 📈\n\n"
    msg += f"Current Price: `{current:.2f}`\n"
    msg += f"Trend: {trend}\n"
    msg += f"RSI(14): `{rsi:.1f}`\n\n"
    msg += f"💡 Recommendation: *{action}*"
    
    # Send chart image
    try:
        with open(chart_path, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption=msg, parse_mode='Markdown')
        os.remove(chart_path)
    except Exception as e:
        await update.message.reply_text(msg, parse_mode='Markdown')
        print(f"Chart send error: {e}")

async def trade_result_callback(contract, profit):
    """Called when a trade closes"""
    if not APP_INSTANCE:
        return
    
    contract_id = contract.get('contract_id', 'N/A')
    symbol = contract.get('display_name', 'Unknown')
    buy_price = contract.get('buy_price', 0)
    sell_price = contract.get('sell_price', 0)
    status = contract.get('status', 'unknown')
    
    # Determine win/loss
    is_win = profit > 0
    emoji = "✅ WIN" if is_win else "❌ LOSS"
    
    msg = f"{emoji} *Trade Closed*\n\n"
    msg += f"Symbol: *{symbol}*\n"
    msg += f"Contract ID: `{contract_id}`\n\n"
    msg += f"Buy Price: `${buy_price:.2f}`\n"
    msg += f"Sell Price: `${sell_price:.2f}`\n"
    msg += f"Profit/Loss: `${profit:.2f}`\n\n"
    msg += f"💰 Balance: `${deriv_client.balance:.2f}`"
    
    for chat_id in config.ALLOWED_CHAT_IDS:
        try:
            await APP_INSTANCE.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        except Exception as e:
            print(f"Failed to send result to {chat_id}: {e}")

def calculate_acceleration(history):
    """Calculate price acceleration (rate of change of velocity)"""
    if len(history) < 3:
        return 0
    
    # Get last 3 prices
    p1, p2, p3 = history[-3], history[-2], history[-1]
    
    # Calculate velocities
    v1 = p2 - p1  # velocity between tick 1 and 2
    v2 = p3 - p2  # velocity between tick 2 and 3
    
    # Acceleration is change in velocity
    acceleration = abs(v2 - v1)
    return acceleration

def detect_momentum(history, symbol):
    """Detect if price has building momentum in one direction"""
    if len(history) < config.MOMENTUM_WINDOW:
        return False
    
    recent_prices = history[-config.MOMENTUM_WINDOW:]
    
    # Check if prices are consistently moving in one direction
    if "BOOM" in symbol:
        # For Boom, look for upward momentum
        increasing = sum(1 for i in range(1, len(recent_prices)) if recent_prices[i] > recent_prices[i-1])
        return increasing >= (config.MOMENTUM_WINDOW - 2)  # At least 3 out of 5 increasing
    elif "CRASH" in symbol:
        # For Crash, look for downward momentum
        decreasing = sum(1 for i in range(1, len(recent_prices)) if recent_prices[i] < recent_prices[i-1])
        return decreasing >= (config.MOMENTUM_WINDOW - 2)  # At least 3 out of 5 decreasing
    
    return False

async def send_early_warning(symbol, acceleration, current_price):
    """Send early warning alert for potential spike"""
    if not APP_INSTANCE:
        return
    
    momentum_level = "HIGH" if acceleration > 0.5 else "MEDIUM"
    
    msg = f"⚠️ *SPIKE BUILDING* ⚠️\n\n"
    msg += f"Symbol: *{symbol}*\n"
    msg += f"Momentum: {momentum_level}\n"
    msg += f"Acceleration: `{acceleration:.2f}` pts/tick\n"
    msg += f"Current Price: `{current_price:.2f}`\n\n"
    msg += "🔔 Potential spike in 5-15 seconds\n"
    msg += "Prepare for entry!"
    
    for chat_id in config.ALLOWED_CHAT_IDS:
        try:
            await APP_INSTANCE.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        except Exception as e:
            print(f"Failed to send early warning to {chat_id}: {e}")

async def strategy_callback(symbol, price, history):
    global last_prediction_time
    
    if not IS_RUNNING:
        print(f"⏸ Strategy paused (IS_RUNNING=False). Send /start to begin.")  # Debug
        return

    if len(history) < config.MOMENTUM_WINDOW + 2:
        return

    current_price = history[-1]
    prev_price = history[-2]
    diff = current_price - prev_price
    
    print(f"📊 {symbol}: diff={diff:.2f}, threshold={config.SPIKE_THRESHOLD}")  # Debug

    # ===== PREDICTIVE DETECTION (Early Warning) =====
    if config.PREDICTION_ENABLED and len(history) >= config.MOMENTUM_WINDOW:
        acceleration = calculate_acceleration(history)
        has_momentum = detect_momentum(history, symbol)
        
        print(f"DEBUG PREDICT {symbol}: accel={acceleration:.3f}, momentum={has_momentum}, threshold={config.ACCELERATION_THRESHOLD}")
        
        # Check cooldown
        current_time = datetime.now().timestamp()
        last_time = last_prediction_time.get(symbol, 0)
        cooldown_passed = (current_time - last_time) > config.PREDICTION_COOLDOWN
        
        if acceleration > config.ACCELERATION_THRESHOLD and has_momentum and cooldown_passed:
            # Send early warning
            print(f"🔔 PREDICTION TRIGGERED for {symbol}!")
            await send_early_warning(symbol, acceleration, current_price)
            last_prediction_time[symbol] = current_time
        elif acceleration > config.ACCELERATION_THRESHOLD:
            print(f"DEBUG: High accel but no momentum or cooldown for {symbol}")
        elif has_momentum:
            print(f"DEBUG: Has momentum but low accel for {symbol}")

    # ===== REACTIVE DETECTION (Trade Signal) =====
    signal_detected = False
    direction = ""
    entry = current_price
    sl = 0
    tp = 0
    
    # Strategy Logic with SL/TP calculation
    # Boom Indices: Spike UP -> SELL (PUT)
    if "BOOM" in symbol: 
        if diff > config.SPIKE_THRESHOLD:
            print(f"Spike Detected on {symbol}! Diff: {diff}")
            signal_detected = True
            direction = "SELL"
            entry = current_price
            sl = entry + 15  # Stop loss above entry
            tp = entry - 30  # Take profit below entry (2:1 RR)
            
            if AUTO_TRADE:
                await deriv_client.propose_trade(symbol, "PUT")
    
    # Crash Indices: Crash DOWN -> BUY (expecting bounce/reversal)
    elif "CRASH" in symbol:
        if diff < -config.SPIKE_THRESHOLD:
            print(f"Crash Detected on {symbol}! Diff: {diff}")
            signal_detected = True
            direction = "BUY"
            entry = current_price
            sl = entry - 15  # Stop loss below entry
            tp = entry + 30  # Take profit above entry (2:1 RR)
            
            if AUTO_TRADE:
                await deriv_client.propose_trade(symbol, "CALL")

    # Send enhanced signal
    if signal_detected and APP_INSTANCE:
        global daily_trade_count, trade_history, active_trades, last_trade_time
        
        # Check cooldown for trade signals (prevent duplicates)
        current_time = datetime.now().timestamp()
        last_time = last_trade_time.get(symbol, 0)
        cooldown_passed = (current_time - last_time) > config.TRADE_SIGNAL_COOLDOWN
        
        if not cooldown_passed:
            time_remaining = int(config.TRADE_SIGNAL_COOLDOWN - (current_time - last_time))
            print(f"⏳ Trade signal cooldown for {symbol}: {time_remaining}s remaining")
            return
        
        # Update last trade time
        last_trade_time[symbol] = current_time
        
        # Increment daily counter
        daily_trade_count += 1
        save_daily_counter(daily_trade_count)  # Persist to file
        
        # Record trade for success tracking
        trade_data = {
            'id': daily_trade_count,
            'timestamp': datetime.now(),
            'symbol': symbol,
            'direction': direction,
            'entry': entry,
            'status': 'pending',  # pending, success, failed
            'diff': diff
        }
        trade_history.append(trade_data)
        save_trade_history(trade_history)  # Persist to file
        
        # Check if same symbol already has an active trade
        if symbol in active_trades:
            # Mark the previous trade as failed (re-triggered before 3 min)
            prev_trade = active_trades[symbol]
            for t in trade_history:
                if t['id'] == prev_trade['id']:
                    t['status'] = 'failed'
                    duration = (datetime.now() - prev_trade['timestamp']).total_seconds()
                    print(f"❌ Trade #{prev_trade['id']} ({symbol}) FAILED - Re-triggered after {duration:.1f}s")
                    save_trade_history(trade_history)  # Save updated status
                    
                    # Send failure notification
                    msg = f"❌ *TRADE #{prev_trade['id']} FAILED* ❌\n"
                    msg += f"Symbol: {symbol}\n"
                    msg += f"Reason: Re-triggered (Stop Loss hit)\n"
                    msg += f"Duration: {format_duration(duration)}"
                    
                    asyncio.create_task(send_async_msg(msg))
                    break
        
        # Set this as the active trade for this symbol
        active_trades[symbol] = trade_data
        
        # Schedule success check after 3 minutes
        asyncio.create_task(check_trade_success(trade_data['id'], symbol))
        
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr_ratio = reward / risk if risk > 0 else 0
        
        msg = f"🚨 *TRADE SIGNAL #{daily_trade_count}* 🚨\n\n"
        msg += f"Symbol: *{symbol}*\n"
        msg += f"Direction: *{direction}* (3 min)\n\n"
        msg += f"Entry: `{entry:.2f}`\n"
        msg += f"Stop Loss: `{sl:.2f}`\n"
        msg += f"Take Profit: `{tp:.2f}`\n\n"
        msg += f"Risk/Reward: `1:{rr_ratio:.1f}`\n"
        msg += f"Spike Size: `{abs(diff):.2f}` points\n\n"
        
        if AUTO_TRADE:
            msg += "✅ *Trade Auto-Executed*"
        else:
            msg += "⏳ *Signal Only - Manual Entry Required*"
        
        for chat_id in config.ALLOWED_CHAT_IDS:
            try:
                await APP_INSTANCE.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
            except Exception as e:
                print(f"Failed to send signal to {chat_id}: {e}")
        
        print(f"📊 Daily trade count: {daily_trade_count}")

async def check_trade_success(trade_id, symbol):
    """Check if trade was successful after 3 minutes"""
    global trade_history, active_trades
    
    # Wait 3 minutes
    await asyncio.sleep(180)
    
    # Find the trade
    trade = None
    for t in trade_history:
        if t['id'] == trade_id:
            trade = t
            break
    
    if not trade:
        return
    
    # If still pending, mark as successful
    if trade['status'] == 'pending':
        trade['status'] = 'success'
        save_trade_history(trade_history)  # Save updated status
        
        # Calculate streak
        streak = calculate_streak(trade_history)
        streak_msg = f"\n🔥 *{streak} WIN STREAK!*" if streak > 1 else ""
        
        print(f"✅ Trade #{trade_id} ({symbol}) SUCCESS - Completed 3 minutes")
        
        # Send success notification
        msg = f"✅ *TRADE #{trade_id} WON!* 🏆\n"
        msg += f"Symbol: {symbol}\n"
        msg += f"Result: Held 3 mins safely\n"
        msg += f"Status: WIN ✅{streak_msg}"
        
        await send_async_msg(msg)
        
        # Remove from active trades if it's still the active one
        if symbol in active_trades and active_trades[symbol]['id'] == trade_id:
            del active_trades[symbol]

async def send_async_msg(text):
    """Helper to send message to all users"""
    if not APP_INSTANCE:
        return
    for chat_id in config.ALLOWED_CHAT_IDS:
        try:
            await APP_INSTANCE.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
        except Exception as e:
            print(f"Failed to send msg to {chat_id}: {e}")

async def main():
    global APP_INSTANCE, chart_analyzer
    
    # Initialize chart analyzer
    chart_analyzer = ChartAnalyzer(deriv_client)
    
    # Register callbacks
    deriv_client.add_tick_callback(strategy_callback)
    deriv_client.set_result_callback(trade_result_callback)
    
    # Request initial balance
    await asyncio.sleep(2)  # Wait for connection
    await deriv_client.get_balance()

    global APP_INSTANCE
    # Telegram Application
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    APP_INSTANCE = app

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("prices", prices))
    app.add_handler(CommandHandler("nasdaq", analyze_nasdaq))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("tradestats", tradestats))
    # app.add_handler(CommandHandler("test", test_alert)) # Removed test
    # app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)) # Removed echo

    print("Initializing Bot...")
    
    # Set up bot commands menu
    async def setup_commands():
        from telegram import BotCommand
        commands = [
            BotCommand("start", "🟢 Start trading bot"),
            BotCommand("stop", "🔴 Stop trading bot"),
            BotCommand("status", "📊 Check bot status"),
            BotCommand("balance", "💰 View account balance"),
            BotCommand("prices", "📈 Current market prices"),
            BotCommand("stats", "📊 Daily trade count"),
            BotCommand("tradestats", "🎯 Trade success rate"),
            BotCommand("nasdaq", "📉 Nasdaq analysis"),
        ]
        await app.bot.set_my_commands(commands)
        print("✅ Bot commands menu set up")
    
    # Start Deriv Connection properly
    async def start_deriv_service():
        await deriv_client.connect()
        await deriv_client.listen()
    
    asyncio.create_task(start_deriv_service())
    
    # Start midnight checker task
    async def check_midnight():
        """Check if it's midnight and reset counter"""
        global current_date
        while True:
            await asyncio.sleep(60)  # Check every minute
            now = datetime.now()
            today = now.date()
            
            # Check if date has changed
            if today != current_date:
                print(f"🕛 Midnight detected! Resetting daily counter...")
                await reset_daily_counter()
    
    asyncio.create_task(check_midnight())
    
    await app.initialize()
    await setup_commands()  # Set up command menu
    await app.start()
    await app.updater.start_polling()
    
    print("Bot Started. Press Ctrl+C to stop.")
    
    # Keep the script running
    try:
        # We can use a future or just sleep loop
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    while True:
        try:
            print("Starting bot...")
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            print(f"\n❌ Bot crashed: {e}")
            print("🔄 Restarting in 10 seconds...")
            import time
            time.sleep(10)
