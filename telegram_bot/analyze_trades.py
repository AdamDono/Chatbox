#!/usr/bin/env python3
"""
Trade Log Analyzer
Analyzes bot logs to identify successful trades (3-minute duration without same pair re-triggering)
"""

import re
from datetime import datetime, timedelta
from collections import defaultdict

def parse_log_file(log_file_path):
    """Parse the log file and extract trade signals"""
    trades = []
    
    with open(log_file_path, 'r') as f:
        for line in f:
            # Look for spike/crash detection messages
            if 'Spike Detected' in line or 'Crash Detected' in line:
                # Extract timestamp, symbol, and type
                match = re.search(r'(Spike|Crash) Detected on (\w+)! Diff: ([-\d.]+)', line)
                if match:
                    trade_type = match.group(1)
                    symbol = match.group(2)
                    diff = float(match.group(3))
                    
                    # Try to extract timestamp from log line
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if timestamp_match:
                        timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                    else:
                        timestamp = None
                    
                    trades.append({
                        'timestamp': timestamp,
                        'symbol': symbol,
                        'type': trade_type,
                        'diff': diff,
                        'raw_line': line.strip()
                    })
    
    return trades

def analyze_successful_trades(trades, duration_minutes=3):
    """
    Analyze trades to find successful ones
    A successful trade is one where the same symbol doesn't trigger again within the duration
    """
    successful_trades = []
    failed_trades = []
    
    for i, trade in enumerate(trades):
        if trade['timestamp'] is None:
            continue
            
        # Check if same symbol triggered within duration_minutes
        is_successful = True
        end_time = trade['timestamp'] + timedelta(minutes=duration_minutes)
        
        for j, other_trade in enumerate(trades[i+1:], start=i+1):
            if other_trade['timestamp'] is None:
                continue
                
            # If same symbol triggers before duration ends, it's a failed trade
            if (other_trade['symbol'] == trade['symbol'] and 
                other_trade['timestamp'] < end_time):
                is_successful = False
                failed_trades.append({
                    **trade,
                    'failed_at': other_trade['timestamp'],
                    'duration': (other_trade['timestamp'] - trade['timestamp']).total_seconds() / 60
                })
                break
        
        if is_successful:
            successful_trades.append(trade)
    
    return successful_trades, failed_trades

def print_report(trades, successful_trades, failed_trades):
    """Print analysis report"""
    print("=" * 80)
    print("TRADE LOG ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nTotal Signals Found: {len(trades)}")
    print(f"Successful Trades (3-min duration): {len(successful_trades)}")
    print(f"Failed Trades (re-triggered before 3 min): {len(failed_trades)}")
    
    if len(trades) > 0:
        success_rate = (len(successful_trades) / len(trades)) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    # Group by symbol
    symbol_stats = defaultdict(lambda: {'total': 0, 'successful': 0, 'failed': 0})
    
    for trade in trades:
        symbol_stats[trade['symbol']]['total'] += 1
    
    for trade in successful_trades:
        symbol_stats[trade['symbol']]['successful'] += 1
    
    for trade in failed_trades:
        symbol_stats[trade['symbol']]['failed'] += 1
    
    print("\n" + "=" * 80)
    print("STATISTICS BY SYMBOL")
    print("=" * 80)
    for symbol, stats in sorted(symbol_stats.items()):
        print(f"\n{symbol}:")
        print(f"  Total Signals: {stats['total']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        if stats['total'] > 0:
            print(f"  Success Rate: {(stats['successful'] / stats['total']) * 100:.1f}%")
    
    if successful_trades:
        print("\n" + "=" * 80)
        print("SUCCESSFUL TRADES (3-min duration without re-trigger)")
        print("=" * 80)
        for i, trade in enumerate(successful_trades, 1):
            print(f"\n{i}. {trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {trade['symbol']}")
            print(f"   Type: {trade['type']}")
            print(f"   Diff: {trade['diff']:.2f}")
    
    if failed_trades:
        print("\n" + "=" * 80)
        print("FAILED TRADES (re-triggered before 3 min)")
        print("=" * 80)
        for i, trade in enumerate(failed_trades, 1):
            print(f"\n{i}. {trade['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {trade['symbol']}")
            print(f"   Type: {trade['type']}")
            print(f"   Duration before re-trigger: {trade['duration']:.2f} minutes")

if __name__ == "__main__":
    import sys
    
    log_file = sys.argv[1] if len(sys.argv) > 1 else 'bot_error.log'
    
    print(f"Analyzing log file: {log_file}\n")
    
    trades = parse_log_file(log_file)
    
    if not trades:
        print("No trade signals found in the log file.")
        print("\nNote: The bot needs to be running with /start command to generate trade signals.")
        print("Check that:")
        print("  1. Bot is running (./start_bot.sh)")
        print("  2. You've sent /start command in Telegram")
        print("  3. Market is open and generating signals")
    else:
        successful_trades, failed_trades = analyze_successful_trades(trades)
        print_report(trades, successful_trades, failed_trades)
