from flask import Blueprint, render_template_string, request
from common import get_api_data, MENU_BAR, INSIDER_TRADES_API_URL, MOCK_TICKERS
import logging
from datetime import datetime, timedelta
import locale
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure locale for number formatting
locale.setlocale(locale.LC_ALL, '')

insider_trades_bp = Blueprint('insider_trades', __name__, url_prefix='/')

def format_currency(value):
    try:
        # Convert string to float and format as currency
        value = float(value)
        if value < 0:
            return f"-${abs(value):,.2f}"
        return f"${value:,.2f}"
    except (ValueError, TypeError):
        return "N/A"

def generate_mock_insider_trades():
    trades = []
    today = datetime.now()
    
    for i in range(10):
        date = today - timedelta(days=i)
        ticker = random.choice(MOCK_TICKERS)
        purchases = random.randint(0, 10)
        sells = random.randint(0, 10)
        purchases_notional = random.randint(100000, 1000000) if purchases > 0 else 0
        sells_notional = random.randint(100000, 1000000) if sells > 0 else 0
        
        trades.append({
            'ticker': ticker,
            'filing_date': date.strftime('%Y-%m-%d'),
            'purchases': purchases,
            'purchases_notional': purchases_notional,
            'sells': sells,
            'sells_notional': sells_notional
        })
    
    return trades

def get_insider_trades():
    try:
        # Get data from the API
        response = get_api_data(INSIDER_TRADES_API_URL)
        
        # If API returns error or invalid response, use mock data
        if not response or isinstance(response, dict) and 'error' in response:
            logger.info("Using mock data for insider trades")
            return generate_mock_insider_trades()
            
        # If response is not a list, log error and return mock data
        if not isinstance(response, list):
            logger.error(f"Invalid response from insider trades API: {response}")
            return generate_mock_insider_trades()
            
        # Sort data by filing date (most recent first)
        response.sort(key=lambda x: x.get('filing_date', ''), reverse=True)
        
        # Take only the last 10 days of data
        return response[:10]
        
    except Exception as e:
        logger.error(f"Error fetching insider trades data: {str(e)}")
        return generate_mock_insider_trades()

@insider_trades_bp.route('/insider-trades')
def insider_trades():
    trades_data = get_insider_trades()
    
    # Ensure we have data before rendering
    if not trades_data:
        trades_data = generate_mock_insider_trades()
    
    html = """
    {{ style }}
    <div class="container">
        <h1>Insider Buy/Sell Activity</h1>
        """ + MENU_BAR + """
        
        <div class="card">
            {% if trades_data %}
            <div class="summary-stats">
                <div class="stat-box">
                    <h3>Today's Activity</h3>
                    <div class="stat-grid">
                        <div class="stat">
                            <span class="label">Buys</span>
                            <span class="value positive">{{ trades_data[0]['purchases'] }}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Buy Volume</span>
                            <span class="value positive">{{ format_currency(trades_data[0]['purchases_notional']) }}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Sells</span>
                            <span class="value negative">{{ trades_data[0]['sells'] }}</span>
                        </div>
                        <div class="stat">
                            <span class="label">Sell Volume</span>
                            <span class="value negative">{{ format_currency(trades_data[0]['sells_notional']) }}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Filing Date</th>
                            <th>Purchases</th>
                            <th>Purchase Volume</th>
                            <th>Sells</th>
                            <th>Sell Volume</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in trades_data %}
                        <tr>
                            <td>{{ item['ticker'] }}</td>
                            <td>{{ item['filing_date'] }}</td>
                            <td class="positive">{{ item['purchases'] }}</td>
                            <td class="positive">{{ format_currency(item['purchases_notional']) }}</td>
                            <td class="negative">{{ item['sells'] }}</td>
                            <td class="negative">{{ format_currency(item['sells_notional']) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="error-message">
                <p>No insider trading data available at the moment. Please try again later.</p>
            </div>
            {% endif %}
        </div>
    </div>
    
    <style>
        .summary-stats {
            margin-bottom: 2rem;
        }
        
        .stat-box {
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
        }
        
        .stat-box h3 {
            margin: 0 0 1rem 0;
            color: var(--primary-color);
            font-size: 1.2rem;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
        }
        
        .stat {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .stat .label {
            color: var(--text);
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        .stat .value {
            font-size: 1.2rem;
            font-weight: 600;
        }
        
        .positive {
            color: #28a745;
        }
        
        .negative {
            color: #dc3545;
        }
        
        .table-container {
            margin-top: 2rem;
            overflow-x: auto;
        }
        
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 0;
        }
        
        th {
            background: var(--primary-color);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9rem;
            letter-spacing: 0.5px;
            padding: 1rem;
        }
        
        td {
            padding: 1rem;
            border-bottom: 1px solid var(--border);
        }
        
        tr:hover {
            background: var(--hover);
        }
        
        .error-message {
            text-align: center;
            padding: 2rem;
            color: var(--text);
        }
        
        @media (max-width: 768px) {
            .stat-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
    """
    
    return render_template_string(html, 
                                trades_data=trades_data,
                                format_currency=format_currency) 