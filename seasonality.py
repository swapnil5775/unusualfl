from flask import Blueprint, render_template_string, request, jsonify
from common import get_api_data, get_live_stock_price, MENU_BAR, SEASONALITY_API_URL, SEASONALITY_MARKET_API_URL, ETF_INFO_API_URL
import logging
import json
import yfinance as yf
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

seasonality_bp = Blueprint('seasonality', __name__, url_prefix='/')

@seasonality_bp.route('/seasonality')
def seasonality():
    html = """
    {{ style }}
    <div class="container">
        <h1>Seasonality Analysis</h1>
        """ + MENU_BAR + """
        <div class="card">
            <h2><i class="fas fa-chart-line"></i> Stock & ETF Seasonality</h2>
            <p>Analyze seasonal patterns in stock and ETF performance.</p>
            <div class="button-group">
                <a href="/seasonality/per-ticker" class="btn">
                    <i class="fas fa-search"></i> Per Ticker Analysis
                </a>
                <a href="/seasonality/etf-market" class="btn">
                    <i class="fas fa-chart-pie"></i> ETF Market Analysis
                </a>
            </div>
        </div>
    </div>
    <style>
        .button-group {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .card h2 {
            color: var(--primary-color);
            margin-top: 0;
        }
        
        .card p {
            color: var(--text);
            margin-bottom: 1.5rem;
        }
    </style>
    """
    return render_template_string(html)

@seasonality_bp.route('/seasonality/per-ticker')
def seasonality_per_ticker():
    ticker = request.args.get('ticker', '').upper()
    monthly_data = None
    error = None

    if ticker:
        try:
            # Verify ticker exists using yfinance
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info.get('regularMarketPrice'):
                error = f"Invalid ticker symbol: {ticker}"
            else:
                # Get seasonality data
                response = get_api_data(SEASONALITY_API_URL.format(ticker=ticker))
                if "error" not in response:
                    monthly_data = response.get("data", [])
        except Exception as e:
            error = str(e)

    html = """
    {{ style }}
    <div class="container">
        <h1>Ticker Seasonality Analysis</h1>
        """ + MENU_BAR + """
        
        <div class="card">
            <form method="GET" class="search-form">
                <div class="input-group">
                    <i class="fas fa-search"></i>
                    <input type="text" name="ticker" value="{{ ticker or '' }}" 
                           placeholder="Enter ticker symbol (e.g., AAPL, MSFT)" required>
        </div>
                <button type="submit" class="btn">Analyze</button>
            </form>
        </div>

        {% if error %}
        <div class="alert alert-error">
            <i class="fas fa-exclamation-circle"></i>
            {{ error }}
        </div>
        {% endif %}

        {% if ticker and not error %}
        <div class="card">
            <h2>{{ ticker }} - Monthly Seasonality Statistics</h2>
            <div class="charts-container">
                <div class="chart-wrapper">
                    <canvas id="monthlyChangesChart"></canvas>
                </div>
                <div class="chart-wrapper">
                    <canvas id="positiveMonthsChart"></canvas>
                </div>
            </div>
            
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Month</th>
                            <th>Avg Change (%)</th>
                            <th>Max Change (%)</th>
                            <th>Median Change (%)</th>
                            <th>Min Change (%)</th>
                            <th>Positive Months</th>
                            <th>Success Rate (%)</th>
                </tr>
                    </thead>
                    <tbody>
                    {% for item in monthly_data %}
                        <tr>
                            <td>{{ item.month }}</td>
                            <td class="{{ 'positive' if item.avg_change > 0 else 'negative' }}">
                                {{ "%.2f"|format(item.avg_change) }}%
                            </td>
                            <td class="positive">{{ "%.2f"|format(item.max_change) }}%</td>
                            <td class="{{ 'positive' if item.median_change > 0 else 'negative' }}">
                                {{ "%.2f"|format(item.median_change) }}%
                            </td>
                            <td class="negative">{{ "%.2f"|format(item.min_change) }}%</td>
                            <td>{{ item.positive_closes }}/{{ item.years }}</td>
                            <td>{{ "%.1f"|format(item.positive_months_perc * 100) }}%</td>
            </tr>
                    {% endfor %}
                    </tbody>
        </table>
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

        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .alert-error {
            background-color: rgba(220, 53, 69, 0.1);
            color: #dc3545;
            border: 1px solid rgba(220, 53, 69, 0.2);
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

        .table-responsive {
            overflow-x: auto;
        }

        .positive { color: #28a745; }
        .negative { color: #dc3545; }

        @media (max-width: 768px) {
            .search-form {
                flex-direction: column;
            }
            
            .input-group {
                width: 100%;
            }
            
            .charts-container {
                grid-template-columns: 1fr;
            }
        }
    </style>

    {% if ticker and not error and monthly_data %}
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Monthly Changes Chart
        const monthlyCtx = document.getElementById('monthlyChangesChart').getContext('2d');
        
        // Prepare data for charts
        const months = [
            {% for item in monthly_data %}
                "{{ item.month }}",
            {% endfor %}
        ];
        
        const avgChanges = [
            {% for item in monthly_data %}
                {{ item.avg_change }},
            {% endfor %}
        ];
        
        const successRates = [
            {% for item in monthly_data %}
                {{ item.positive_months_perc * 100 }},
            {% endfor %}
        ];
        
        const bgColors = [
            {% for item in monthly_data %}
                "{{ 'rgba(40, 167, 69, 0.7)' if item.avg_change > 0 else 'rgba(220, 53, 69, 0.7)' }}",
            {% endfor %}
        ];
        
        const borderColors = [
            {% for item in monthly_data %}
                "{{ 'rgb(40, 167, 69)' if item.avg_change > 0 else 'rgb(220, 53, 69)' }}",
            {% endfor %}
        ];
        
        new Chart(monthlyCtx, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [{
                    label: 'Average Change (%)',
                    data: avgChanges,
                    backgroundColor: bgColors,
                    borderColor: borderColors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Monthly Average Returns',
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
                        beginAtZero: true,
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
                            color: 'var(--text)'
                        }
                    }
                }
            }
        });

        // Success Rate Chart
        const successCtx = document.getElementById('positiveMonthsChart').getContext('2d');
        new Chart(successCtx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Success Rate (%)',
                    data: successRates,
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
                        text: 'Monthly Success Rate',
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
                        beginAtZero: true,
                        max: 100,
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
                            color: 'var(--text)'
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
                                monthly_data=monthly_data,
                                error=error)

# The main application block has been removed as it is not needed in a blueprint file.
