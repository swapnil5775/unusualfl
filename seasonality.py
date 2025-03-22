from flask import Blueprint, render_template_string, request, jsonify
from common import get_api_data, get_live_stock_price, MENU_BAR, SEASONALITY_API_URL, SEASONALITY_MARKET_API_URL, ETF_INFO_API_URL
import logging
import json
import yfinance as yf
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

seasonality_bp = Blueprint('seasonality', __name__, url_prefix='/')

@seasonality_bp.route('/')
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
@seasonality_bp.route('/per-ticker', methods=['GET'])
def seasonality_per_ticker():
    ticker = request.args.get('ticker', '').upper()
    monthly_data = None
    error = None
    monthly_error = None
    yearly_monthly_error = None
    yearly_monthly_data = None
    yearly_performance = None
    yearly_prices = None
    years = []
    price_years = []
    performance_values = []
    price_values = []

    if ticker:
        try:
            # Get monthly seasonality data
            monthly_url = SEASONALITY_API_URL.format(ticker=ticker)
            monthly_response = get_api_data(monthly_url)
            if "error" in monthly_response:
                monthly_error = monthly_response["error"]
            else:
                monthly_data = monthly_response.get("data", [])

            # Get yearly-monthly data
            yearly_monthly_url = f"https://api.unusualwhales.com/api/seasonality/{ticker}/year-month"
            yearly_monthly_response = get_api_data(yearly_monthly_url)
            if "error" in yearly_monthly_response:
                yearly_monthly_error = yearly_monthly_response["error"]
            else:
                yearly_monthly_data = yearly_monthly_response.get("data", [])

            # Verify ticker exists using yfinance
            stock = yf.Ticker(ticker)
            info = stock.info
            if not info.get('regularMarketPrice'):
                error = f"Invalid ticker symbol: {ticker}"
        except Exception as e:
            error = str(e)
            yearly_performance = {"error": f"Error fetching performance: {str(e)}"}
            yearly_prices = {"error": f"Error fetching prices: {str(e)}"}

        # Get ETF info if available
        etf_info = None
        etf_info_error = None
        try:
            etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
            if "error" in etf_info_response:
                etf_info_error = etf_info_response["error"]
            else:
                etf_info = etf_info_response.get("data", {})
        except Exception as e:
            etf_info_error = str(e)

        # Process year data for charts
        common_years = []
        performance_values_filtered = []
        price_values_filtered = []
        if ticker and yearly_performance and "error" not in yearly_performance and yearly_prices and "error" not in yearly_prices:
            common_years = list(set(years) & set(price_years))
            common_years.sort()
            performance_values_filtered = [
                performance_values[years.index(year)] if year in years and years.index(year) < len(performance_values) else "N/A"
                for year in common_years
            ]
            price_values_filtered = [
                price_values[price_years.index(year)] if year in price_years and price_years.index(year) < len(price_values) else "N/A"
                for year in common_years
            ]

    # Prepare context for template
    context = {
        'ticker': ticker,
        'monthly_data': monthly_data,
        'yearly_monthly_data': yearly_monthly_data,
        'monthly_error': monthly_error,
        'yearly_monthly_error': yearly_monthly_error,
        'yearly_performance': yearly_performance,
        'yearly_prices': yearly_prices,
        'common_years': common_years,
        'performance_values_filtered': performance_values_filtered,
        'price_values_filtered': price_values_filtered,
        'etf_info': etf_info,
        'etf_info_error': etf_info_error,
        'MENU_BAR': MENU_BAR
    }

    # Start of HTML template
    html = """
    {{ style }}
    <div class="container">
        <h1>Seasonality - Per Ticker</h1>
        {{ MENU_BAR | safe }}
        
        <div class="card">
            <form method="GET" class="search-form">
                <div class="input-group">
                    <i class="fas fa-search"></i>
                    <input type="text" name="ticker" value="{{ ticker or '' }}" 
                           placeholder="Enter ticker symbol (e.g., AAPL, MSFT)" required>
                </div>
                <button type="submit" class="btn">Analyze</button>
            </form>

            {% if monthly_error %}<p style="color: red;">Error (Monthly Data): {{ monthly_error }}</p>{% endif %}
            {% if yearly_monthly_error %}<p style="color: red;">Error (Year-Month Data): {{ yearly_monthly_error }}</p>{% endif %}
            {% if not monthly_error and not monthly_data %}<p>No monthly data available for ticker {{ ticker or '' }}</p>{% endif %}
            {% if not yearly_monthly_error and not yearly_monthly_data %}<p>No year-month data available for ticker {{ ticker or '' }}</p>{% endif %}
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

        {% if etf_info %}
        <div class="card">
            <h2>ETF Info for {{ ticker }}</h2>
            <table>
                <tr><th>Field</th><th>Value</th></tr>
                {% for key, value in etf_info.items() %}
                    {% if value is not none %}
                    <tr>
                        <td>{{ key|replace('_', ' ')|title }}</td>
                        <td>{{ value }}</td>
                    </tr>
                    {% endif %}
                {% endfor %}
            </table>
        </div>
        {% endif %}

        {% if yearly_monthly_data %}
        <div class="card">
            <h2>15-Year Monthly Return History</h2>
            <table>
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>Month</th>
                        <th>Open</th>
                        <th>Close</th>
                        <th>Change</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in yearly_monthly_data %}
                    <tr>
                        <td>{{ item.year }}</td>
                        <td>{{ item.month }}</td>
                        <td>{{ "%.2f"|format(item.open|float) if item.open else "N/A" }}</td>
                        <td>{{ "%.2f"|format(item.close|float) if item.close else "N/A" }}</td>
                        <td class="{{ 'positive' if item.change|float > 0 else 'negative' }}">
                            {{ "%.2f"|format(item.change|float) }}%
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
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

    return render_template_string(html, **context)

@seasonality_bp.route('/etf-market', methods=['GET'])
def seasonality_etf_market():
    ticker = request.args.get('ticker', 'ALL').upper()
    data = None
    error = None

    response = get_api_data(SEASONALITY_MARKET_API_URL)
    if "error" in response:
        error = response["error"]
        logger.error(f"API Error for {SEASONALITY_MARKET_API_URL}: {error}")
    else:
        all_data = response.get("data", [])
        data = [item for item in all_data if item['ticker'] == ticker] if ticker != 'ALL' else all_data

    etf_tickers = ['SPY', 'QQQ', 'IWM', 'XLE', 'XLC', 'XLK', 'XLV', 'XLP', 'XLY', 'XLRE', 'XLF', 'XLI', 'XLB']

    context = {
        'ticker': ticker,
        'data': data,
        'error': error,
        'etf_tickers': etf_tickers,
        'MENU_BAR': MENU_BAR
    }

    html = """
    <h1>Seasonality - ETF Market</h1>
    {{ MENU_BAR | safe }}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 2; min-width: 300px; margin-right: 20px;">
            <h3>Select ETF or View All:</h3>
            <div>
                <button onclick="window.location.href='/seasonality/etf-market?ticker=ALL'">ALL</button>
    """
    for t in etf_tickers:
        html += f"""
            <button onclick="window.location.href='/seasonality/etf-market?ticker={t}'">{t}</button>
        """
    html += """
            </div>
            {% if error %}<p style="color: red;">Error: {{ error }}</p>{% endif %}
            {% if not error and not data %}<p>No data available for ticker {{ ticker }}</p>{% endif %}
            <table border='1' {% if not data %}style="display: none;"{% endif %} id="etfMarketTable">
                <tr>
                    <th>Ticker</th>
                    <th>Month</th>
                    <th>Avg Change</th>
                    <th>Max Change</th>
                    <th>Median Change</th>
                    <th>Min Change</th>
                    <th>Positive Closes</th>
                    <th>Positive Months %</th>
                    <th>Years</th>
                    <th>Live Price</th>
                </tr>
    """
    if data:
        for item in data:
            avg_change = float(item.get('avg_change', 0.0)) if item.get('avg_change') else 0.0
            max_change = float(item.get('max_change', 0.0)) if item.get('max_change') else 0.0
            median_change = float(item.get('median_change', 0.0)) if item.get('median_change') else 0.0
            min_change = float(item.get('min_change', 0.0)) if item.get('min_change') else 0.0
            positive_months_perc = float(item.get('positive_months_perc', 0.0)) * 100
            positive_closes = item.get('positive_closes', 0)
            years = item.get('years', 'N/A')
            month = item.get('month', 'N/A')
            ticker_val = item.get('ticker', 'N/A')
            live_price = get_live_stock_price(ticker_val) if ticker_val != 'N/A' else 'N/A'

            def format_with_color(value, decimals=2):
                color = 'red' if value < 0 else 'black'
                return f'<span style="color: {color}">{value:.{decimals}f}</span>'

            html += f"""
            <tr>
                <td>{ticker_val}</td>
                <td>{month}</td>
                <td>{format_with_color(avg_change)}</td>
                <td>{format_with_color(max_change)}</td>
                <td>{format_with_color(median_change)}</td>
                <td>{format_with_color(min_change)}</td>
                <td>{positive_closes}</td>
                <td>{positive_months_perc:.2f}%</td>
                <td>{years}</td>
                <td>{live_price if isinstance(live_price, (int, float)) else live_price}</td>
            </tr>
            """
    html += """
            </table>
        </div>
        <div style="flex: 1; min-width: 300px; padding: 20px; border: 1px solid #ccc; border-radius: 5px; background-color: #f9f9f9;">
            <h3>AI Summary</h3>
            <textarea id="aiQuestion" rows="4" cols="50" placeholder="Enter your question about the ETF seasonality data..."></textarea>
            <br>
            <button onclick="getAiSummary()">Run AI Summary</button>
            <div id="aiResponse" style="margin-top: 10px;"></div>
        </div>
    </div>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        async function getAiSummary() {
            const question = document.getElementById('aiQuestion').value;
            if (!question) {
                alert('Please enter a question.');
                return;
            }

            const data = {{ data | tojson | safe }};
            if (!data || data.length === 0) {
                document.getElementById('aiResponse').innerHTML = '<p>No data available for analysis.</p>';
                return;
            }

            const csvData = data.map(item => `
                Month: ${item.month}, ETF: ${item.ticker}, Avg Change: ${item.avg_change}, 
                Positive Months %: ${item.positive_months_perc * 100}`).join('\n');

            try {
                const response = await fetch('/seasonality/ai-summary', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question, data: csvData })
                });
                const result = await response.json();
                document.getElementById('aiResponse').innerHTML = '<ul>' + result.summary.map(point => `<li>${point}</li>`).join('') + '</ul>';
            } catch (error) {
                document.getElementById('aiResponse').innerHTML = `<p>Error: ${error.message}</p>`;
            }
        }
    </script>
    """
    return render_template_string(html, **context)

@seasonality_bp.route('/ai-summary', methods=['POST'])
def ai_summary():
    data = request.json
    question = data.get('question', '')
    csv_data = data.get('data', '')

    prompt = f"""
    Analyze the given ETF seasonality data and generate a structured response with 4 bullet points of unique insights based on the following prompt:

    - Analyze the given ETF seasonality data and generate a structured table with the following columns:
      1. Month (Display as full month name instead of a number)
      2. ETF (The ETF ticker symbol)
      3. Upside/Downside Change (The average price change for that ETF in that month)
      4. Insight (A brief explanation of why the ETF should be watched in that month)
      5. Win Probability (%) (Percentage of months in the last 15 years where the ETF closed positively)

    Ensure the response provides actionable insights, helping users understand which ETFs to monitor for potential upside or downside movements based on historical trends.

    Data:
    {csv_data}

    Question: {question}
    """

    try:
        import openai
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a financial data analyst specializing in ETF seasonality trends."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        summary = response.choices[0].message['content'].strip().split('\n')
        summary = [line.strip('- ').strip() for line in summary if line.strip()]
        return jsonify({"summary": summary[:4]})
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return jsonify({"summary": ["Unable to generate AI summary. OpenAI service may be unavailable."]})