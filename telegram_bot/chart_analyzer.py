import asyncio
import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np

class ChartAnalyzer:
    def __init__(self, deriv_client):
        self.client = deriv_client
    
    async def get_candles(self, symbol, count=50):
        """Fetch M15 candles from Deriv API"""
        req = {
            "ticks_history": symbol,
            "adjust_start_time": 1,
            "count": count,
            "end": "latest",
            "start": 1,
            "style": "candles",
            "granularity": 900  # 900 seconds = 15 minutes
        }
        
        await self.client.send(req)
        
        # Wait for response (simplified - in production, use proper async handling)
        await asyncio.sleep(2)
        
        # For now, return mock data structure
        # In real implementation, we'd capture the response in handle_message
        return None
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum()/period
        down = -seed[seed < 0].sum()/period
        rs = up/down if down != 0 else 0
        rsi = np.zeros_like(prices)
        rsi[:period] = 100. - 100./(1. + rs)

        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(period - 1) + upval)/period
            down = (down*(period - 1) + downval)/period
            rs = up/down if down != 0 else 0
            rsi[i] = 100. - 100./(1. + rs)

        return rsi
    
    def calculate_sma(self, prices, period):
        """Calculate Simple Moving Average"""
        return np.convolve(prices, np.ones(period)/period, mode='valid')
    
    def generate_chart(self, symbol, candles_data, output_path):
        """Generate M15 chart with indicators"""
        # Mock implementation - will be enhanced with real data
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
        
        # Price chart
        ax1.set_title(f'{symbol} - M15 Analysis', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # RSI chart
        ax2.set_ylabel('RSI', fontsize=10)
        ax2.set_xlabel('Time', fontsize=10)
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5)
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def analyze_trend(self, prices):
        """Analyze trend and generate recommendation"""
        if len(prices) < 20:
            return "NEUTRAL", "Insufficient data"
        
        sma_20 = self.calculate_sma(prices, 20)
        current_price = prices[-1]
        sma_current = sma_20[-1]
        
        rsi = self.calculate_rsi(np.array(prices))
        current_rsi = rsi[-1]
        
        # Simple trend logic
        if current_price > sma_current and current_rsi < 70:
            trend = "BULLISH 🟢"
            action = "BUY"
        elif current_price < sma_current and current_rsi > 30:
            trend = "BEARISH 🔴"
            action = "SELL"
        else:
            trend = "NEUTRAL ⚪"
            action = "WAIT"
        
        return trend, action, current_rsi

chart_analyzer = None  # Will be initialized in bot.py
