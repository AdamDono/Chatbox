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
AUTO_TRADE = False  # New: Control auto-trading
APP_INSTANCE = None
chart_analyzer = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global IS_RUNNING
    IS_RUNNING = True
    await update.message.reply_text(f"Bot Started! Monitoring Boom/Crash for spikes.\nStake: ${config.STAKE_AMOUNT}\nDuration: {config.DURATION_SECONDS}s")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global IS_RUNNING
    IS_RUNNING = False
    await update.message.reply_text("Bot Stopped. No new trades will be placed.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = "RUNNING" if IS_RUNNING else "STOPPED"
    await update.message.reply_text(f"Status: {status_msg}\nConnected: {deriv_client.authorized}")

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

async def strategy_callback(symbol, price, history):
    if not IS_RUNNING:
        print(f"⏸ Strategy paused (IS_RUNNING=False). Send /start to begin.")  # Debug
        return

    if len(history) < 2:
        return

    current_price = history[-1]
    prev_price = history[-2]
    diff = current_price - prev_price
    
    print(f"📊 {symbol}: diff={diff:.2f}, threshold={config.SPIKE_THRESHOLD}")  # Debug

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
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr_ratio = reward / risk if risk > 0 else 0
        
        msg = f"🚨 *TRADE SIGNAL* 🚨\n\n"
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

async def main():
    global APP_INSTANCE, chart_analyzer
    
    # Initialize chart analyzer
    chart_analyzer = ChartAnalyzer(deriv_client)
    
    # Register callback
    deriv_client.add_tick_callback(strategy_callback)

    global APP_INSTANCE
    # Telegram Application
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    APP_INSTANCE = app

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("prices", prices))
    app.add_handler(CommandHandler("nasdaq", analyze_nasdaq))
    # app.add_handler(CommandHandler("test", test_alert)) # Removed test
    # app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)) # Removed echo

    print("Initializing Bot...")
    
    # Start Deriv Connection properly
    async def start_deriv_service():
        await deriv_client.connect()
        await deriv_client.listen()
    
    asyncio.create_task(start_deriv_service())
    
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
