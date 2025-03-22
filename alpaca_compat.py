"""
Compatibility layer for replacing alpaca-trade-api with alpaca-py
This module provides a wrapper around alpaca-py to maintain compatibility with code
that was written for alpaca-trade-api.
"""

import os
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockQuotesRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import pytz

# Environment variables for API credentials
ALPACA_API_KEY = os.environ.get('ALPACA_API_KEY', 'PKQHK5MA2YWFURXQZR91')
ALPACA_API_SECRET = os.environ.get('ALPACA_API_SECRET', 'a4g6KlQyJXQ9OGGu3H8dz4LbVUc7NQXuVuY0AzMi')

# Create a trading client instance (equivalent to alpaca_trade_api.REST)
trading_client = TradingClient(ALPACA_API_KEY, ALPACA_API_SECRET, paper=True)
data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_API_SECRET)

# Compatibility class to mimic alpaca_trade_api.REST
class REST:
    def __init__(self, key_id=None, secret_key=None, base_url=None):
        self.trading_client = trading_client
        self.data_client = data_client
        
    def get_bars(self, symbols, timeframe, start=None, end=None, limit=None):
        # Handle start/end date parameters
        if start is None:
            start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if end is None:
            end = datetime.now().strftime('%Y-%m-%d')
            
        # Convert string dates to datetime objects if needed
        if isinstance(start, str):
            start = datetime.strptime(start, '%Y-%m-%d')
        if isinstance(end, str):
            end = datetime.strptime(end, '%Y-%m-%d')
            
        # Add timezone if not present
        if start.tzinfo is None:
            start = pytz.timezone('America/New_York').localize(start)
        if end.tzinfo is None:
            end = pytz.timezone('America/New_York').localize(end)
            
        # Handle timeframe parameter
        tf_mapping = {
            '1D': TimeFrame.Day,
            '1H': TimeFrame.Hour,
            '15Min': TimeFrame.Minute,
            'day': TimeFrame.Day,
            'hour': TimeFrame.Hour,
            'minute': TimeFrame.Minute
        }
        tf = tf_mapping.get(timeframe, TimeFrame.Day)
        
        # Create request parameters
        params = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=tf,
            start=start,
            end=end,
            limit=limit
        )
        
        # Execute request
        try:
            bars = self.data_client.get_stock_bars(params)
            return bars
        except Exception as e:
            print(f"Error getting bars: {e}")
            return None

# Mock the websockets functionality
class StreamConn:
    def __init__(self, key_id=None, secret_key=None, base_url=None, data_stream=None):
        self.trading_client = trading_client
        self.data_client = data_client
        self.handlers = {}
        
    def run(self):
        print("Mock StreamConn running - no actual websocket connection in this compatibility layer")
        return
        
    def on(self, event_type):
        def decorator(func):
            self.handlers[event_type] = func
            return func
        return decorator
        
    def register(self, handler, event_type):
        self.handlers[event_type] = handler 