from flask import Blueprint, render_template_string, request, jsonify
import asyncio
import websockets
import json
import threading
import time
import pandas as pd
from datetime import datetime, timedelta
import pytz
import random
from common import MENU_BAR
import requests

# Import MOCK_TICKERS or create our own if it's not available
try:
    from common import MOCK_TICKERS
except ImportError:
    MOCK_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "WMT"]

# Global variables to store data
premium_trades_data = []
premium_threshold = 10000  # Default threshold is $10,000
connected = False
websocket_task = None
stop_event = threading.Event()
use_mock_data = True  # Set to True to use mock data instead of real API

# Alpaca API credentials for paper trading
ALPACA_API_KEY = "AK49TL9A4OLPKO9PAUH3"
ALPACA_API_SECRET = "0744CcGjrhPXvsORtWJpSMNWpEYuDTegOlE0OgLV"
ALPACA_API_URL = "https://api.alpaca.markets"
ALPACA_WS_URL = "wss://stream.data.alpaca.markets/v1beta1/options"

# Blueprint configuration
premium_options_bp = Blueprint('premium_options', __name__)

# Helper function to convert timestamp to readable format
def format_time(timestamp):
    if isinstance(timestamp, str):
        try:
            # Parse RFC-3339 formatted timestamp (e.g. "2024-03-11T13:35:35.13312256Z")
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            eastern = pytz.timezone('US/Eastern')
            dt = dt.astimezone(eastern)
            return dt.strftime('%H:%M:%S')
        except:
            return timestamp
    
    # Handle numeric timestamp (milliseconds since epoch)
    dt = datetime.fromtimestamp(timestamp / 1000, tz=pytz.UTC)
    eastern = pytz.timezone('US/Eastern')
    dt = dt.astimezone(eastern)
    return dt.strftime('%H:%M:%S')

# WebSocket client to connect to Alpaca's options data stream
async def connect_to_alpaca_websocket():
    global connected, premium_trades_data
    premium_trades_data = []  # Clear previous data when reconnecting
    
    # Connect to Alpaca's WebSocket
    uri = ALPACA_WS_URL
    
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        async with websockets.connect(uri, extra_headers=headers) as websocket:
            # Authentication message
            auth_msg = {
                "action": "auth",
                "key": ALPACA_API_KEY,
                "secret": ALPACA_API_SECRET
            }
            await websocket.send(json.dumps(auth_msg))
            auth_response = await websocket.recv()
            auth_response = json.loads(auth_response)
            
            if auth_response.get('T') == 'success' and auth_response.get('msg') == 'authenticated':
                connected = True
                print("Authentication successful")
                
                # Subscribe to all options trades
                subscription_msg = {
                    "action": "subscribe",
                    "trades": ["*"]  # Subscribe to all options trades
                }
                await websocket.send(json.dumps(subscription_msg))
                print("Subscription request sent")
                
                # Receive subscription confirmation
                sub_response = await websocket.recv()
                print(f"Subscription response: {sub_response}")
                
                while not stop_event.is_set():
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        print(f"Received message: {message[:100]}...")  # Print first 100 chars for debugging
                        data = json.loads(message)
                        
                        # Process each trade message based on the new format
                        if isinstance(data, dict) and data.get('T') == 't':
                            process_trade_message(data)
                    except asyncio.TimeoutError:
                        # Just a timeout, continue the loop
                        continue
                    except Exception as e:
                        print(f"Error receiving message: {e}")
                        break
            else:
                print(f"Authentication failed: {auth_response}")
                connected = False
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        connected = False
    finally:
        connected = False
        print("WebSocket connection closed")

def process_trade_message(message):
    global premium_trades_data
    
    try:
        # Extract data from the message based on Alpaca API schema
        # T = message type, S = symbol, t = timestamp, p = price, s = size, x = exchange, c = condition
        symbol = message.get('S', '')        # option symbol
        price = float(message.get('p', 0))   # price
        size = int(message.get('s', 0))      # size
        timestamp = message.get('t', '')     # timestamp in RFC-3339 format
        exchange = message.get('x', '')      # exchange code
        condition = message.get('c', '')     # trade condition
        
        # Calculate premium (price × size × 100)
        premium = price * size * 100
        
        # If premium exceeds our threshold, store the trade
        if premium >= premium_threshold:
            # Parse the option symbol to extract ticker, expiration, type, strike
            # Format is typically: AAPL240621C00220000
            if len(symbol) >= 16:  # Basic validation
                ticker = ''
                for char in symbol:
                    if char.isdigit():
                        break
                    ticker += char
                
                # Extract the option details
                date_part = symbol[len(ticker):len(ticker)+6]
                option_type = symbol[len(ticker)+6:len(ticker)+7]
                strike_part = symbol[len(ticker)+7:]
                
                # Format the expiration (YYMMDD -> YYYY-MM-DD)
                try:
                    year = int("20" + date_part[0:2])
                    month = int(date_part[2:4])
                    day = int(date_part[4:6])
                    expiration = f"{year}-{month:02d}-{day:02d}"
                except:
                    expiration = date_part
                
                # Format the strike price (remove trailing zeros)
                try:
                    strike = float(strike_part) / 1000
                except:
                    strike = strike_part
            else:
                ticker = symbol
                expiration = "Unknown"
                option_type = "?"
                strike = 0

            # Format time from RFC-3339 timestamp
            formatted_time = format_time(timestamp)
            
            trade_data = {
                'symbol': symbol,
                'ticker': ticker,
                'strike': strike,
                'expiration': expiration,
                'option_type': option_type,
                'price': price,
                'size': size,
                'premium': premium,
                'time': formatted_time,
                'exchange': exchange,
                'condition': condition
            }
            
            # Prepend to the list so newest trades appear at the top
            premium_trades_data.insert(0, trade_data)
            
            # Keep only the most recent 100 trades to avoid memory issues
            if len(premium_trades_data) > 100:
                premium_trades_data = premium_trades_data[:100]
            
            print(f"Premium trade detected: {trade_data['symbol']} - ${premium:,.2f}")
    except Exception as e:
        print(f"Error processing trade message: {e}")

# Generate mock option data for testing
def generate_mock_trades():
    global premium_trades_data, connected
    
    # Common strike prices
    strikes = [100, 105, 110, 115, 120, 125, 130, 140, 150, 160, 170, 180, 190, 200, 
              210, 220, 230, 240, 250, 300, 350, 400, 450, 500, 550, 600]
    
    # Common option types (C = Call, P = Put)
    option_types = ['C', 'P']
    
    # Common exchanges
    exchanges = ['N', 'C', 'A', 'P', 'Q']
    
    # Expiration dates (next few months)
    current_date = datetime.now()
    expirations = []
    for i in range(1, 7):  # Next 6 months
        # Options typically expire on the third Friday of the month
        year = current_date.year
        month = current_date.month + i
        if month > 12:
            month = month - 12
            year += 1
        
        # Find the third Friday
        day = 1
        date = datetime(year, month, day)
        while date.weekday() != 4:  # Friday is 4
            day += 1
            date = datetime(year, month, day)
        third_friday = day + 14  # Add two weeks to get the third Friday
        
        # Format as YYMMDD
        exp_date = f"{str(year)[-2:]}{month:02d}{third_friday:02d}"
        expirations.append(exp_date)
    
    connected = True
    
    # Generate a random number of trades (1-3)
    num_trades = random.randint(1, 3)
    
    for _ in range(num_trades):
        ticker = random.choice(MOCK_TICKERS)
        strike = random.choice(strikes)
        option_type = random.choice(option_types)
        expiration = random.choice(expirations)
        exchange = random.choice(exchanges)
        
        # Generate a relatively high price and size to meet the premium threshold
        price = random.uniform(2.0, 50.0)
        size_min = max(1, int(premium_threshold / (price * 100)))
        size = random.randint(size_min, size_min * 5)
        
        premium = price * size * 100
        
        # Create the option symbol (e.g. AAPL240621C00150000)
        option_symbol = f"{ticker}{expiration}{option_type}{strike:08d}"
        
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")
        
        trade_data = {
            'symbol': option_symbol,
            'strike': strike,
            'expiration': expiration,
            'option_type': option_type,
            'price': price,
            'size': size,
            'premium': premium,
            'time': time_str,
            'exchange': exchange,
        }
        
        # Prepend to the list so newest trades appear at the top
        premium_trades_data.insert(0, trade_data)
        
        # Keep only the most recent 100 trades to avoid memory issues
        if len(premium_trades_data) > 100:
            premium_trades_data = premium_trades_data[:100]
        
        print(f"Mock premium trade generated: {trade_data['symbol']} - ${premium:,.2f}")

# Function to generate mock data at regular intervals
def mock_data_generator():
    global stop_event
    
    while not stop_event.is_set():
        generate_mock_trades()
        time.sleep(random.uniform(2, 5))  # Random interval between 2-5 seconds

# Function to start the WebSocket connection in a separate thread
def start_websocket_connection():
    global websocket_task, stop_event
    
    if use_mock_data:
        # Use mock data instead of real API
        mock_data_generator()
        return
    
    # Create a new event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Set up the WebSocket task
    websocket_task = loop.create_task(connect_to_alpaca_websocket())
    
    try:
        # Run the event loop until the stop event is set
        loop.run_until_complete(websocket_task)
    except asyncio.CancelledError:
        print("WebSocket task was cancelled")
    finally:
        loop.close()

# Start the WebSocket connection thread
def start_websocket_thread():
    global stop_event
    
    # Reset the stop event
    stop_event.clear()
    
    # Start the thread
    thread = threading.Thread(target=start_websocket_connection)
    thread.daemon = True
    thread.start()
    print("WebSocket thread started")

# Routes for the premium options Blueprint
@premium_options_bp.route('/premium-options')
def premium_options_page():
    return render_template_string("""
        {{ style }}
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <div class="container">
            <h1>Premium Options Flow</h1>
            """ + MENU_BAR + """
            
            <div class="card main-card">
                <div class="tabs">
                    <button class="tab-btn active" data-tab="all">All Premiums</button>
                    <button class="tab-btn" data-tab="filtered">Filtered View</button>
                    <button class="tab-btn" data-tab="stats">Statistics</button>
                </div>
                
                <div class="controls">
                    <div class="input-group">
                        <label for="premium-threshold">Premium Threshold ($):</label>
                        <input type="number" id="premium-threshold" value="10000" min="1000" step="1000">
                    </div>
                    
                    <div class="search-container">
                        <input type="text" id="ticker-search" placeholder="Search by ticker...">
                        <button id="search-btn" class="btn">Filter</button>
                        <button id="clear-filter-btn" class="btn btn-secondary">Clear</button>
                    </div>
                    
                    <div class="connection-status">
                        <span id="connection-status">Disconnected</span>
                        <button id="connect-btn" class="btn">Connect</button>
                        <button id="disconnect-btn" class="btn btn-danger" disabled>Disconnect</button>
                    </div>
                </div>
                
                <div class="stats-container">
                    <div class="stat-card">
                        <div class="stat-title">Total Trades</div>
                        <div id="total-trades" class="stat-value">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">Highest Premium</div>
                        <div id="highest-premium" class="stat-value">$0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">Average Premium</div>
                        <div id="average-premium" class="stat-value">$0</div>
                    </div>
                    <div class="stat-card ticker-stats">
                        <div class="stat-title">Filtered Ticker</div>
                        <div id="filtered-ticker" class="stat-value">-</div>
                    </div>
                </div>
                
                <div class="ticker-stats-container" style="display: none;">
                    <div class="stat-card">
                        <div class="stat-title">Ticker Trades</div>
                        <div id="ticker-trades" class="stat-value">0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">Ticker Highest Premium</div>
                        <div id="ticker-highest-premium" class="stat-value">$0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">Ticker Average Premium</div>
                        <div id="ticker-average-premium" class="stat-value">$0</div>
                    </div>
                </div>
                
                <div id="tab-content-all" class="tab-content active">
                    <div class="table-container">
                        <table id="premium-trades-table">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Symbol</th>
                                    <th>Strike</th>
                                    <th>Type</th>
                                    <th>Expiration</th>
                                    <th>Price</th>
                                    <th>Size</th>
                                    <th>Premium ($)</th>
                                </tr>
                            </thead>
                            <tbody id="trades-tbody">
                                <tr>
                                    <td colspan="8" class="empty-table">No premium trades yet. Connect to start receiving data.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div id="tab-content-filtered" class="tab-content">
                    <div class="table-container">
                        <table id="filtered-trades-table">
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Symbol</th>
                                    <th>Strike</th>
                                    <th>Type</th>
                                    <th>Expiration</th>
                                    <th>Price</th>
                                    <th>Size</th>
                                    <th>Premium ($)</th>
                                </tr>
                            </thead>
                            <tbody id="filtered-tbody">
                                <tr>
                                    <td colspan="8" class="empty-table">Search for a ticker to filter trades.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div id="tab-content-stats" class="tab-content">
                    <div class="chart-container">
                        <canvas id="premium-distribution-chart"></canvas>
                    </div>
                    <div class="chart-container">
                        <canvas id="ticker-distribution-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <style>
            .main-card {
                padding: 0;
                overflow: hidden;
                background-color: #191919;
                border: 1px solid #333;
            }
            
            .tabs {
                display: flex;
                background-color: #121212;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid #333;
            }
            
            .tab-btn {
                flex: 1;
                padding: 15px;
                background: none;
                border: none;
                color: #999;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
                font-size: 14px;
            }
            
            .tab-btn:hover {
                background-color: #242424;
                color: #fff;
            }
            
            .tab-btn.active {
                background-color: #242424;
                color: #fff;
                border-bottom: 2px solid #00c805;
            }
            
            .tab-content {
                display: none;
                padding: 20px;
                background-color: #191919;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .controls {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px;
                flex-wrap: wrap;
                gap: 15px;
                border-bottom: 1px solid #333;
                background-color: #191919;
            }
            
            .input-group {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .input-group label {
                color: #ccc;
                font-weight: normal;
            }
            
            .search-container {
                display: flex;
                gap: 10px;
                flex: 1;
                max-width: 400px;
            }
            
            .search-container input {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #333;
                border-radius: 4px;
                background: #242424;
                color: #fff;
                font-size: 14px;
            }
            
            input[type="number"], input[type="text"] {
                border: 1px solid #333;
                background: #242424;
                color: #fff;
                padding: 8px 12px;
                border-radius: 4px;
            }
            
            input[type="number"]::placeholder, input[type="text"]::placeholder {
                color: #777;
            }
            
            .connection-status {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            #connection-status {
                padding: 5px 10px;
                border-radius: 20px;
                background-color: #ff4d4d;
                color: #fff;
                font-weight: bold;
                font-size: 12px;
            }
            
            #connection-status.connected {
                background-color: #00c805;
                color: #fff;
            }
            
            .btn {
                display: inline-block;
                padding: 8px 16px;
                background-color: #00c805;
                color: #fff;
                text-decoration: none;
                border-radius: 4px;
                transition: background-color 0.2s ease;
                border: none;
                cursor: pointer;
                font-weight: bold;
                font-size: 13px;
            }
            
            .btn:hover {
                background-color: #00a504;
                color: #fff;
            }
            
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            
            .btn-danger {
                background-color: #ff4d4d;
                color: #fff;
            }
            
            .btn-danger:hover {
                background-color: #ff3333;
                color: #fff;
            }
            
            .btn-secondary {
                background-color: #444;
                color: #fff;
            }
            
            .btn-secondary:hover {
                background-color: #555;
                color: #fff;
            }
            
            .table-container {
                overflow-x: auto;
                margin-top: 10px;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                color: #fff;
                font-size: 14px;
            }
            
            th, td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #333;
            }
            
            th {
                background-color: #121212;
                color: #999;
                position: sticky;
                top: 0;
                font-weight: normal;
                text-transform: uppercase;
                font-size: 12px;
            }
            
            tbody tr {
                background-color: #191919;
                transition: background-color 0.2s;
            }
            
            tbody tr:hover {
                background-color: #242424;
            }
            
            td {
                color: #fff;
            }
            
            .empty-table {
                text-align: center;
                padding: 40px;
                color: #777;
                font-style: italic;
            }
            
            .stats-container {
                display: flex;
                justify-content: space-between;
                padding: 20px;
                flex-wrap: wrap;
                gap: 15px;
                border-bottom: 1px solid #333;
                color: #ccc;
                background-color: #191919;
            }
            
            .ticker-stats-container {
                display: flex;
                justify-content: space-between;
                padding: 0 20px 20px;
                flex-wrap: wrap;
                gap: 15px;
                border-bottom: 1px solid #333;
                background-color: #191919;
            }
            
            .stat-card {
                flex: 1;
                min-width: 150px;
                background-color: #242424;
                padding: 15px;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                text-align: center;
                border: 1px solid #333;
                color: #ccc;
            }
            
            .stat-title {
                font-size: 0.9em;
                color: #999;
                margin-bottom: 5px;
                text-transform: uppercase;
                font-size: 11px;
            }
            
            .stat-value {
                font-size: 1.5em;
                font-weight: bold;
                color: #fff;
            }
            
            .premium-value {
                color: #00c805; /* Green for premium values */
            }
            
            .chart-container {
                height: 300px;
                margin-bottom: 30px;
                background-color: #191919;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 15px;
            }
            
            .ticker-stats {
                display: none;
            }
            
            @media (max-width: 768px) {
                .controls {
                    flex-direction: column;
                    align-items: flex-start;
                }
                
                .search-container {
                    max-width: 100%;
                    width: 100%;
                }
                
                .stat-card {
                    min-width: 100%;
                }
            }
        </style>

        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const connectBtn = document.getElementById('connect-btn');
                const disconnectBtn = document.getElementById('disconnect-btn');
                const connectionStatus = document.getElementById('connection-status');
                const premiumThresholdInput = document.getElementById('premium-threshold');
                const tradesTbody = document.getElementById('trades-tbody');
                const filteredTbody = document.getElementById('filtered-tbody');
                const totalTradesEl = document.getElementById('total-trades');
                const highestPremiumEl = document.getElementById('highest-premium');
                const averagePremiumEl = document.getElementById('average-premium');
                const tickerSearchInput = document.getElementById('ticker-search');
                const searchBtn = document.getElementById('search-btn');
                const clearFilterBtn = document.getElementById('clear-filter-btn');
                const filteredTickerEl = document.getElementById('filtered-ticker');
                const tickerTradesEl = document.getElementById('ticker-trades');
                const tickerHighestPremiumEl = document.getElementById('ticker-highest-premium');
                const tickerAveragePremiumEl = document.getElementById('ticker-average-premium');
                const tabButtons = document.querySelectorAll('.tab-btn');
                const tabContents = document.querySelectorAll('.tab-content');
                const tickerStatsEl = document.querySelector('.ticker-stats');
                const tickerStatsContainer = document.querySelector('.ticker-stats-container');
                
                let isConnected = false;
                let updateInterval = null;
                let currentTicker = '';
                let allTrades = [];
                let premiumChart = null;
                let tickerChart = null;
                
                // Tab switching functionality
                tabButtons.forEach(button => {
                    button.addEventListener('click', function() {
                        const tab = this.dataset.tab;
                        
                        // Update active state for buttons
                        tabButtons.forEach(btn => btn.classList.remove('active'));
                        this.classList.add('active');
                        
                        // Update active state for content
                        tabContents.forEach(content => content.classList.remove('active'));
                        document.getElementById(`tab-content-${tab}`).classList.add('active');
                        
                        // If switching to stats tab, initialize charts
                        if (tab === 'stats') {
                            initializeCharts();
                        }
                    });
                });
                
                // Function to initialize charts
                function initializeCharts() {
                    if (premiumChart) {
                        premiumChart.destroy();
                    }
                    
                    if (tickerChart) {
                        tickerChart.destroy();
                    }
                    
                    // Only create charts if we have data
                    if (allTrades.length === 0) {
                        return;
                    }
                    
                    const premiumCtx = document.getElementById('premium-distribution-chart').getContext('2d');
                    const tickerCtx = document.getElementById('ticker-distribution-chart').getContext('2d');
                    
                    // Premium distribution chart
                    const premiumRanges = [
                        '10k-25k', '25k-50k', '50k-100k', '100k-250k', '250k-500k', '500k+'
                    ];
                    
                    const premiumCounts = [
                        allTrades.filter(t => t.premium >= 10000 && t.premium < 25000).length,
                        allTrades.filter(t => t.premium >= 25000 && t.premium < 50000).length,
                        allTrades.filter(t => t.premium >= 50000 && t.premium < 100000).length,
                        allTrades.filter(t => t.premium >= 100000 && t.premium < 250000).length,
                        allTrades.filter(t => t.premium >= 250000 && t.premium < 500000).length,
                        allTrades.filter(t => t.premium >= 500000).length
                    ];
                    
                    premiumChart = new Chart(premiumCtx, {
                        type: 'bar',
                        data: {
                            labels: premiumRanges,
                            datasets: [{
                                label: 'Premium Distribution',
                                data: premiumCounts,
                                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                                borderColor: 'rgba(75, 192, 192, 1)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: 'Number of Trades'
                                    }
                                },
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Premium Range ($)'
                                    }
                                }
                            },
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Distribution of Premium Trades by Size',
                                    font: {
                                        size: 16
                                    }
                                }
                            }
                        }
                    });
                    
                    // Ticker distribution chart
                    const tickerCounts = {};
                    allTrades.forEach(trade => {
                        const ticker = trade.symbol.slice(0, trade.symbol.indexOf('2')); // Extract ticker from option symbol
                        tickerCounts[ticker] = (tickerCounts[ticker] || 0) + 1;
                    });
                    
                    // Sort by count and get top 10
                    const sortedTickers = Object.entries(tickerCounts)
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, 10);
                    
                    tickerChart = new Chart(tickerCtx, {
                        type: 'bar',
                        data: {
                            labels: sortedTickers.map(t => t[0]),
                            datasets: [{
                                label: 'Trades by Ticker',
                                data: sortedTickers.map(t => t[1]),
                                backgroundColor: 'rgba(153, 102, 255, 0.6)',
                                borderColor: 'rgba(153, 102, 255, 1)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    title: {
                                        display: true,
                                        text: 'Number of Trades'
                                    }
                                },
                                x: {
                                    title: {
                                        display: true,
                                        text: 'Ticker'
                                    }
                                }
                            },
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Top 10 Tickers by Trade Count',
                                    font: {
                                        size: 16
                                    }
                                }
                            }
                        }
                    });
                }
                
                // Function to update connection UI
                function updateConnectionUI(connected) {
                    isConnected = connected;
                    if (connected) {
                        connectionStatus.textContent = 'Connected';
                        connectionStatus.classList.add('connected');
                        connectBtn.disabled = true;
                        disconnectBtn.disabled = false;
                    } else {
                        connectionStatus.textContent = 'Disconnected';
                        connectionStatus.classList.remove('connected');
                        connectBtn.disabled = false;
                        disconnectBtn.disabled = true;
                    }
                }
                
                // Format currency values with green color
                function formatCurrency(value) {
                    const formattedValue = '$' + value.toLocaleString('en-US', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });
                    return `<span class="premium-value">${formattedValue}</span>`;
                }
                
                // Function to update ticker stats
                function updateTickerStats() {
                    if (!currentTicker) {
                        tickerStatsEl.style.display = 'none';
                        tickerStatsContainer.style.display = 'none';
                        filteredTickerEl.textContent = '-';
                        return;
                    }
                    
                    tickerStatsEl.style.display = 'block';
                    tickerStatsContainer.style.display = 'flex';
                    filteredTickerEl.textContent = currentTicker;
                    
                    // Filter trades for the current ticker
                    const tickerTrades = allTrades.filter(trade => 
                        trade.symbol.startsWith(currentTicker)
                    );
                    
                    // Update filtered table
                    if (tickerTrades.length > 0) {
                        let tableHTML = '';
                        tickerTrades.forEach(trade => {
                            tableHTML += `
                                <tr>
                                    <td>${trade.time}</td>
                                    <td>${trade.symbol}</td>
                                    <td>${trade.strike}</td>
                                    <td>${trade.option_type}</td>
                                    <td>${trade.expiration}</td>
                                    <td>$${trade.price.toFixed(2)}</td>
                                    <td>${trade.size}</td>
                                    <td>${formatCurrency(trade.premium)}</td>
                                </tr>
                            `;
                        });
                        filteredTbody.innerHTML = tableHTML;
                        
                        // Update ticker stats
                        tickerTradesEl.textContent = tickerTrades.length;
                        
                        const premiums = tickerTrades.map(t => t.premium);
                        const highestPremium = Math.max(...premiums);
                        const avgPremium = premiums.reduce((a, b) => a + b, 0) / premiums.length;
                        
                        tickerHighestPremiumEl.innerHTML = formatCurrency(highestPremium);
                        tickerAveragePremiumEl.innerHTML = formatCurrency(avgPremium);
                    } else {
                        filteredTbody.innerHTML = `
                            <tr>
                                <td colspan="8" class="empty-table">No trades found for ${currentTicker}.</td>
                            </tr>
                        `;
                        
                        tickerTradesEl.textContent = '0';
                        tickerHighestPremiumEl.textContent = '$0';
                        tickerAveragePremiumEl.textContent = '$0';
                    }
                }
                
                // Function to fetch premium trades data
                async function fetchPremiumTrades() {
                    try {
                        const response = await fetch('/premium-options/data');
                        const data = await response.json();
                        
                        // Store all trades
                        allTrades = data.trades;
                        
                        // Update connection status
                        updateConnectionUI(data.connected);
                        
                        // Update trades table
                        if (data.trades.length > 0) {
                            let tableHTML = '';
                            data.trades.forEach(trade => {
                                tableHTML += `
                                    <tr>
                                        <td>${trade.time}</td>
                                        <td>${trade.symbol}</td>
                                        <td>${trade.strike}</td>
                                        <td>${trade.option_type}</td>
                                        <td>${trade.expiration}</td>
                                        <td>$${trade.price.toFixed(2)}</td>
                                        <td>${trade.size}</td>
                                        <td>${formatCurrency(trade.premium)}</td>
                                    </tr>
                                `;
                            });
                            tradesTbody.innerHTML = tableHTML;
                            
                            // Update overall stats
                            totalTradesEl.textContent = data.trades.length;
                            
                            const premiums = data.trades.map(t => t.premium);
                            const highestPremium = Math.max(...premiums);
                            const avgPremium = premiums.reduce((a, b) => a + b, 0) / premiums.length;
                            
                            highestPremiumEl.innerHTML = formatCurrency(highestPremium);
                            averagePremiumEl.innerHTML = formatCurrency(avgPremium);
                            
                            // Update ticker-specific stats if a ticker is selected
                            if (currentTicker) {
                                updateTickerStats();
                            }
                            
                        } else {
                            tradesTbody.innerHTML = `
                                <tr>
                                    <td colspan="8" class="empty-table">No premium trades yet. Connect to start receiving data.</td>
                                </tr>
                            `;
                            
                            filteredTbody.innerHTML = `
                                <tr>
                                    <td colspan="8" class="empty-table">No trades found.</td>
                                </tr>
                            `;
                            
                            // Reset stats
                            totalTradesEl.textContent = '0';
                            highestPremiumEl.textContent = '$0';
                            averagePremiumEl.textContent = '$0';
                            tickerTradesEl.textContent = '0';
                            tickerHighestPremiumEl.textContent = '$0';
                            tickerAveragePremiumEl.textContent = '$0';
                        }
                        
                    } catch (error) {
                        console.error('Error fetching premium trades:', error);
                    }
                }
                
                // Connect button click handler
                connectBtn.addEventListener('click', async function() {
                    const threshold = parseInt(premiumThresholdInput.value, 10);
                    
                    if (isNaN(threshold) || threshold < 1000) {
                        alert('Please enter a valid threshold (minimum $1,000)');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/premium-options/connect', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ threshold: threshold })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            updateConnectionUI(true);
                            
                            // Start periodic updates
                            if (updateInterval) {
                                clearInterval(updateInterval);
                            }
                            updateInterval = setInterval(fetchPremiumTrades, 2000);
                            
                        } else {
                            alert('Failed to connect: ' + data.error);
                        }
                    } catch (error) {
                        console.error('Error connecting to WebSocket:', error);
                        alert('Failed to connect to data stream');
                    }
                });
                
                // Disconnect button click handler
                disconnectBtn.addEventListener('click', async function() {
                    try {
                        const response = await fetch('/premium-options/disconnect', {
                            method: 'POST'
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            updateConnectionUI(false);
                            
                            // Stop periodic updates
                            if (updateInterval) {
                                clearInterval(updateInterval);
                                updateInterval = null;
                            }
                        } else {
                            alert('Failed to disconnect: ' + data.error);
                        }
                    } catch (error) {
                        console.error('Error disconnecting from WebSocket:', error);
                        alert('Failed to disconnect from data stream');
                    }
                });
                
                // Search button click handler
                searchBtn.addEventListener('click', function() {
                    const ticker = tickerSearchInput.value.trim().toUpperCase();
                    
                    if (ticker) {
                        currentTicker = ticker;
                        updateTickerStats();
                        
                        // Automatically switch to the filtered tab
                        tabButtons.forEach(btn => btn.classList.remove('active'));
                        tabContents.forEach(content => content.classList.remove('active'));
                        
                        document.querySelector('[data-tab="filtered"]').classList.add('active');
                        document.getElementById('tab-content-filtered').classList.add('active');
                    }
                });
                
                // Clear filter button click handler
                clearFilterBtn.addEventListener('click', function() {
                    tickerSearchInput.value = '';
                    currentTicker = '';
                    tickerStatsEl.style.display = 'none';
                    tickerStatsContainer.style.display = 'none';
                    filteredTickerEl.textContent = '-';
                    
                    filteredTbody.innerHTML = `
                        <tr>
                            <td colspan="8" class="empty-table">Search for a ticker to filter trades.</td>
                        </tr>
                    `;
                });
                
                // Initial data fetch
                fetchPremiumTrades();
            });
        </script>
    """)

@premium_options_bp.route('/premium-options/data')
def get_premium_trades_data():
    return jsonify({
        'trades': premium_trades_data,
        'connected': connected
    })

@premium_options_bp.route('/premium-options/connect', methods=['POST'])
def connect_to_stream():
    global premium_threshold, stop_event
    
    # Get threshold from request
    try:
        data = request.get_json()
        threshold = data.get('threshold', 10000)
        if threshold < 1000:
            threshold = 1000  # Minimum threshold
        
        premium_threshold = threshold
        
        # If already connected, disconnect first
        if connected:
            stop_event.set()
            time.sleep(1)  # Give time for the thread to stop
        
        # Start the WebSocket connection thread
        start_websocket_thread()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@premium_options_bp.route('/premium-options/disconnect', methods=['POST'])
def disconnect_from_stream():
    global stop_event
    
    try:
        # Set the stop event to terminate the WebSocket connection
        stop_event.set()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Function to fetch historical options data from Alpaca API
def get_historical_options_data(symbols, start_date, end_date, limit=1000):
    base_url = "https://data.alpaca.markets/v1beta1/options/trades"
    
    params = {
        "symbols": ",".join(symbols),
        "start": start_date,
        "end": end_date,
        "limit": limit,
        "sort": "desc"
    }
    
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_API_SECRET
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        
        return response.json()
    except Exception as e:
        print(f"Error fetching historical options data: {e}")
        return {"error": str(e)}

# Route to fetch historical options data
@premium_options_bp.route('/premium-options/historical', methods=['GET'])
def get_historical_data():
    symbols = request.args.get('symbols', '')
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    limit = request.args.get('limit', 1000)
    
    if not symbols or not start_date or not end_date:
        return jsonify({
            "error": "Missing required parameters (symbols, start, end)"
        }), 400
    
    symbols_list = symbols.split(',')
    
    historical_data = get_historical_options_data(symbols_list, start_date, end_date, limit)
    
    return jsonify(historical_data) 