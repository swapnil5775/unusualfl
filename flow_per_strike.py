from flask import Blueprint, render_template_string, request
from common import get_api_data, MENU_BAR
import logging
import yfinance as yf
from datetime import datetime
import pytz
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

flow_per_strike_bp = Blueprint('flow_per_strike', __name__, url_prefix='/')

def get_options_flow(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        # Get all available expiration dates
        expirations = stock.options
        
        if not expirations:
            return []
            
        # Use the nearest expiration date
        expiration = expirations[0]
        
        # Get options chain
        opt = stock.option_chain(expiration)
        
        # Combine calls and puts data
        flow_data = []
        
        # Process calls
        calls = opt.calls
        for _, row in calls.iterrows():
            flow_data.append({
                'strike': row['strike'],
                'call_volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                'call_premium': round(row['lastPrice'] * row['volume'], 2) if pd.notna(row['volume']) else 0,
                'put_volume': 0,
                'put_premium': 0,
                'timestamp': datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S')
            })
            
        # Process puts
        puts = opt.puts
        for _, row in puts.iterrows():
            # Find if strike price already exists
            existing = next((item for item in flow_data if item['strike'] == row['strike']), None)
            if existing:
                existing['put_volume'] = int(row['volume']) if pd.notna(row['volume']) else 0
                existing['put_premium'] = round(row['lastPrice'] * row['volume'], 2) if pd.notna(row['volume']) else 0
            else:
                flow_data.append({
                    'strike': row['strike'],
                    'call_volume': 0,
                    'call_premium': 0,
                    'put_volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                    'put_premium': round(row['lastPrice'] * row['volume'], 2) if pd.notna(row['volume']) else 0,
                    'timestamp': datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by strike price
        flow_data.sort(key=lambda x: x['strike'])
        return flow_data
        
    except Exception as e:
        logger.error(f"Error fetching options data for {ticker}: {str(e)}")
        return []

@flow_per_strike_bp.route('/flow-per-strike')
def flow_per_strike():
    ticker = request.args.get('ticker', '').upper()
    
    flow_data = []
    if ticker:
        flow_data = get_options_flow(ticker)
    
    html = """
    {{ style }}
    <div class="container">
        <h1>Flow Per Strike</h1>
        """ + MENU_BAR + """
        
        <div class="card">
            <div class="search-container">
                <form action="/flow-per-strike" method="get">
                    <input type="text" name="ticker" placeholder="Enter ticker symbol" value="{{ ticker }}" required>
                    <button type="submit" class="btn">Search</button>
                </form>
            </div>
            
            {% if ticker %}
                {% if flow_data %}
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Strike</th>
                                <th>Call Volume</th>
                                <th>Call Premium ($)</th>
                                <th>Put Volume</th>
                                <th>Put Premium ($)</th>
                                <th>Timestamp (EST)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for item in flow_data %}
                            <tr>
                                <td>${{ "%.2f"|format(item.strike) }}</td>
                                <td class="positive">{{ "{:,}".format(item.call_volume) }}</td>
                                <td class="positive">${{ "{:,.2f}"|format(item.call_premium) }}</td>
                                <td class="negative">{{ "{:,}".format(item.put_volume) }}</td>
                                <td class="negative">${{ "{:,.2f}"|format(item.put_premium) }}</td>
                                <td>{{ item.timestamp }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="alert alert-warning">
                    No options data available for {{ ticker }}. Please check if the ticker is correct and has options trading.
                </div>
                {% endif %}
            {% else %}
            <div class="instructions">
                <p>Enter a ticker symbol to view options flow data.</p>
                <p class="example">Example tickers: AAPL, MSFT, TSLA, SPY</p>
            </div>
            {% endif %}
        </div>
    </div>
    
    <style>
        .search-container {
            margin-bottom: 20px;
        }
        
        .search-container form {
            display: flex;
            gap: 10px;
        }
        
        .search-container input {
            flex: 1;
            padding: 12px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--background);
            color: var(--text);
            font-size: 16px;
        }
        
        .table-container {
            margin-top: 20px;
            overflow-x: auto;
        }
        
        .instructions {
            text-align: center;
            padding: 40px;
            color: var(--text);
        }
        
        .example {
            color: var(--accent-color);
            font-size: 0.9em;
            margin-top: 10px;
        }
        
        .alert {
            padding: 16px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .alert-warning {
            background-color: rgba(255, 193, 7, 0.1);
            border: 1px solid rgba(255, 193, 7, 0.2);
            color: #856404;
        }
    </style>
    """
    
    return render_template_string(html, ticker=ticker, flow_data=flow_data) 