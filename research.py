from flask import Blueprint, render_template_string, request
from common import get_api_data, get_live_stock_price, MENU_BAR
import logging
import yfinance as yf
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

research_bp = Blueprint('research', __name__, url_prefix='/')

@research_bp.route('/research')
def research():
    ticker = request.args.get('ticker', '').upper()
    stock_data = None
    error = None
    
    if ticker:
        try:
            # Verify ticker exists using yfinance
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info.get('regularMarketPrice'):
                error = f"Invalid ticker symbol: {ticker}"
            else:
                # Get historical data
                hist = stock.history(period="1y")
                if not hist.empty:
                    current_price = info.get('regularMarketPrice', 0)
                    prev_close = info.get('regularMarketPreviousClose', 0)
                    day_change = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
                    
                    # Calculate key metrics
                    stock_data = {
                        'name': info.get('longName', ticker),
                        'sector': info.get('sector', 'N/A'),
                        'industry': info.get('industry', 'N/A'),
                        'market_cap': info.get('marketCap', 0),
                        'pe_ratio': info.get('trailingPE', 0),
                        'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                        'current_price': current_price,
                        'day_change': day_change,
                        'volume': info.get('volume', 0),
                        'avg_volume': info.get('averageVolume', 0),
                        'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                        'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                        'beta': info.get('beta', 0),
                        'description': info.get('longBusinessSummary', 'No description available.'),
                        # Historical data for charts
                        'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                        'prices': hist['Close'].tolist(),
                        'volumes': hist['Volume'].tolist()
                    }
        except Exception as e:
            error = str(e)
            logger.error(f"Error fetching data for {ticker}: {e}")

    html = """
    {{ style }}
    <div class="container">
        <h1>Stock Research</h1>
        """ + MENU_BAR + """
        
        <div class="card">
            <form method="GET" class="search-form">
                <div class="input-group">
                    <i class="fas fa-search"></i>
                    <input type="text" name="ticker" value="{{ ticker or '' }}" 
                           placeholder="Enter ticker symbol (e.g., AAPL, MSFT)" required>
                </div>
                <button type="submit" class="btn">Research</button>
            </form>
        </div>

        {% if error %}
        <div class="alert alert-error">
            <i class="fas fa-exclamation-circle"></i>
            {{ error }}
        </div>
        {% endif %}

        {% if stock_data %}
        <div class="card">
            <div class="stock-header">
                <div class="stock-title">
                    <h2>{{ stock_data.name }} ({{ ticker }})</h2>
                    <div class="stock-price">
                        <span class="price">${{ "%.2f"|format(stock_data.current_price) }}</span>
                        <span class="change {{ 'positive' if stock_data.day_change > 0 else 'negative' }}">
                            <i class="fas fa-{{ 'caret-up' if stock_data.day_change > 0 else 'caret-down' }}"></i>
                            {{ "%.2f"|format(stock_data.day_change) }}%
                        </span>
                    </div>
                </div>
                <div class="stock-meta">
                    <span><i class="fas fa-industry"></i> {{ stock_data.sector }}</span>
                    <span><i class="fas fa-building"></i> {{ stock_data.industry }}</span>
                </div>
            </div>

            <div class="charts-container">
                <div class="chart-wrapper">
                    <canvas id="priceChart"></canvas>
                </div>
                <div class="chart-wrapper">
                    <canvas id="volumeChart"></canvas>
                </div>
            </div>

            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>Market Cap</h3>
                    <p>${{ "{:,.0f}".format(stock_data.market_cap) }}</p>
                </div>
                <div class="metric-card">
                    <h3>P/E Ratio</h3>
                    <p>{{ "%.2f"|format(stock_data.pe_ratio) if stock_data.pe_ratio else 'N/A' }}</p>
                </div>
                <div class="metric-card">
                    <h3>Dividend Yield</h3>
                    <p>{{ "%.2f"|format(stock_data.dividend_yield) }}%</p>
                </div>
                <div class="metric-card">
                    <h3>Beta</h3>
                    <p>{{ "%.2f"|format(stock_data.beta) }}</p>
                </div>
                <div class="metric-card">
                    <h3>Volume</h3>
                    <p>{{ "{:,.0f}".format(stock_data.volume) }}</p>
                </div>
                <div class="metric-card">
                    <h3>Avg Volume</h3>
                    <p>{{ "{:,.0f}".format(stock_data.avg_volume) }}</p>
                </div>
                <div class="metric-card">
                    <h3>52W High</h3>
                    <p>${{ "%.2f"|format(stock_data.fifty_two_week_high) }}</p>
                </div>
                <div class="metric-card">
                    <h3>52W Low</h3>
                    <p>${{ "%.2f"|format(stock_data.fifty_two_week_low) }}</p>
                </div>
            </div>

            <div class="description-card">
                <h3>Company Description</h3>
                <p>{{ stock_data.description }}</p>
            </div>
        </div>
        {% endif %}
    </div>

    <style>
        .search-form {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .input-group {
            position: relative;
            flex: 1;
        }

        .input-group i {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text);
        }

        .input-group input {
            width: 100%;
            padding-left: 35px;
        }

        .stock-header {
            margin-bottom: 2rem;
        }

        .stock-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }

        .stock-price {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .price {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--text);
        }

        .change {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            font-weight: bold;
        }

        .stock-meta {
            display: flex;
            gap: 1rem;
            color: var(--text);
            opacity: 0.8;
        }

        .stock-meta span {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .charts-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin: 2rem 0;
        }

        .chart-wrapper {
            background: var(--background);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border);
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }

        .metric-card {
            background: var(--background);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border);
            text-align: center;
        }

        .metric-card h3 {
            color: var(--text);
            opacity: 0.8;
            margin: 0 0 0.5rem 0;
            font-size: 0.9rem;
        }

        .metric-card p {
            color: var(--text);
            font-size: 1.1rem;
            font-weight: bold;
            margin: 0;
        }

        .description-card {
            background: var(--background);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--border);
            margin-top: 2rem;
        }

        .description-card h3 {
            color: var(--text);
            margin: 0 0 1rem 0;
        }

        .description-card p {
            color: var(--text);
            opacity: 0.9;
            line-height: 1.6;
            margin: 0;
        }

        @media (max-width: 768px) {
            .search-form {
                flex-direction: column;
            }
            
            .input-group {
                width: 100%;
            }
            
            .stock-title {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            
            .stock-meta {
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .charts-container {
                grid-template-columns: 1fr;
            }
        }
    </style>

    {% if stock_data %}
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Price Chart
        const priceCtx = document.getElementById('priceChart').getContext('2d');
        new Chart(priceCtx, {
            type: 'line',
            data: {
                labels: {{ stock_data.dates|tojson }},
                datasets: [{
                    label: 'Stock Price ($)',
                    data: {{ stock_data.prices|tojson }},
                    borderColor: 'rgb(74, 144, 226)',
                    backgroundColor: 'rgba(74, 144, 226, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Price History (1 Year)',
                        color: 'var(--text)'
                    },
                    legend: {
                        labels: {
                            color: 'var(--text)'
                        }
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: 'var(--border)'
                        },
                        ticks: {
                            color: 'var(--text)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'var(--border)'
                        },
                        ticks: {
                            color: 'var(--text)',
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });

        // Volume Chart
        const volumeCtx = document.getElementById('volumeChart').getContext('2d');
        new Chart(volumeCtx, {
            type: 'bar',
            data: {
                labels: {{ stock_data.dates|tojson }},
                datasets: [{
                    label: 'Volume',
                    data: {{ stock_data.volumes|tojson }},
                    backgroundColor: 'rgba(75, 192, 192, 0.7)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Volume History (1 Year)',
                        color: 'var(--text)'
                    },
                    legend: {
                        labels: {
                            color: 'var(--text)'
                        }
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: 'var(--border)'
                        },
                        ticks: {
                            color: 'var(--text)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'var(--border)'
                        },
                        ticks: {
                            color: 'var(--text)',
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    </script>
    {% endif %}
    """
    return render_template_string(html, 
                                ticker=ticker,
                                stock_data=stock_data,
                                error=error)
