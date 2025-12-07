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

# Daily trade counter
daily_trade_count = 0
current_date = datetime.now().date()

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

async def reset_daily_counter():
    """Reset daily counter and send summary"""
    global daily_trade_count, current_date
    
    if not APP_INSTANCE:
        return
    
    # Send daily summary
    yesterday = current_date
    msg = f"📈 *Daily Summary - {yesterday.strftime('%Y-%m-%d')}* 📈\n\n"
    msg += f"Total Trades: `{daily_trade_count}`\n\n"
    
    if daily_trade_count == 0:
        msg += "No trades were executed today."
    else:
        msg += f"Great job! {daily_trade_count} trading signals were sent."
    
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
        global daily_trade_count
        
        # Increment daily counter
        daily_trade_count += 1
        
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
    # app.add_handler(CommandHandler("test", test_alert)) # Removed test
    # app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)) # Removed echo

    print("Initializing Bot...")
    
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
