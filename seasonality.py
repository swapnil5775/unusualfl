from flask import Blueprint, render_template_string, request, jsonify
from common import get_api_data, get_live_stock_price, MENU_BAR, SEASONALITY_API_URL, SEASONALITY_MARKET_API_URL, ETF_INFO_API_URL, OPENAI_API_KEY
import logging
import json
import openai
import yfinance as yf
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

openai.api_key = OPENAI_API_KEY

seasonality_bp = Blueprint('seasonality', __name__, url_prefix='/seasonality')

@seasonality_bp.route('/')
def seasonality():
    html = f"""
    <h1>Seasonality</h1>
    {MENU_BAR}
    <p>Select a sub-page or ticker to view seasonality data.</p>
    <ul>
        <li><a href="/seasonality/per-ticker">Per Ticker</a></li>
        <li><a href="/seasonality/etf-market">ETF Market</a></li>
    </ul>
    """
    return render_template_string(html)

@seasonality_bp.route('/per-ticker', methods=['GET'])
def seasonality_per_ticker():
    ticker = request.args.get('ticker', '').upper()
    monthly_data = None
    yearly_monthly_data = None
    monthly_error = None
    yearly_monthly_error = None
    yearly_performance = None
    yearly_prices = None

    if ticker:
        monthly_url = SEASONALITY_API_URL.format(ticker=ticker)
        monthly_response = get_api_data(monthly_url)
        if "error" in monthly_response:
            monthly_error = monthly_response["error"]
        else:
            monthly_data = monthly_response.get("data", [])

        yearly_monthly_url = f"https://api.unusualwhales.com/api/seasonality/{ticker}/year-month"
        yearly_monthly_response = get_api_data(yearly_monthly_url)
        if "error" in yearly_monthly_response:
            yearly_monthly_error = yearly_monthly_response["error"]
        else:
            yearly_monthly_data = yearly_monthly_response.get("data", [])

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="max", interval="1mo")
            yearly_performance = hist['Close'].resample('YE').last().pct_change().dropna() * 100
            yearly_performance = yearly_performance.to_dict()
            years = [dt.strftime('%Y') for dt in yearly_performance.keys()] if yearly_performance else []
            performance_values = list(yearly_performance.values()) if yearly_performance else []
            yearly_prices = hist['Close'].resample('YE').last().dropna().to_dict()
            price_years = [dt.strftime('%Y') for dt in yearly_prices.keys()] if yearly_prices else []
            price_values = list(yearly_prices.values()) if yearly_prices else []
        except Exception as e:
            yearly_performance = {"error": f"Error fetching performance: {str(e)}"}
            yearly_prices = {"error": f"Error fetching prices: {str(e)}"}

    etf_info = None
    etf_info_error = None
    if ticker:
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", {})

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

    html = """
    <h1>Seasonality - Per Ticker</h1>
    {{ MENU_BAR | safe }}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {{ ticker or '' }}</h2>
            {% if etf_info_error %}<p style="color: red;">Error fetching ETF Info: {{ etf_info_error }}</p>{% endif %}
            <table border='1' {% if not etf_info %}style="display: none;"{% endif %} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info:
        for key, value in etf_info.items():
            if value is not None:
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{{ etf_info['{key}'] }}</td></tr>"
    html += """
            </table>
        </div>
        <div style="flex: 2; min-width: 300px;">
            <form method="GET">
                <label>Enter Ticker (e.g., AAPL, TSLA, PLTR): </label>
                <input type="text" name="ticker" value="{{ ticker }}" placeholder="Enter ticker symbol">
                <button type="submit">GO</button>
            </form>
            {% if monthly_error %}<p style="color: red;">Error (Monthly Data): {{ monthly_error }}</p>{% endif %}
            {% if yearly_monthly_error %}<p style="color: red;">Error (Year-Month Data): {{ yearly_monthly_error }}</p>{% endif %}
            {% if not monthly_error and not monthly_data %}<p>No monthly data available for ticker {{ ticker or '' }}</p>{% endif %}
            {% if not yearly_monthly_error and not yearly_monthly_data %}<p>No year-month data available for ticker {{ ticker or '' }}</p>{% endif %}

            <h2>Monthly Seasonality Statistics</h2>
            <table border='1' {% if not monthly_data %}style="display: none;"{% endif %} id="monthlySeasonalityTable">
                <tr>
                    <th>Month</th>
                    <th>Avg Change</th>
                    <th>Max Change</th>
                    <th>Median Change</th>
                    <th>Min Change</th>
                    <th>Positive Closes</th>
                    <th>Positive Months %</th>
                    <th>Years</th>
                </tr>
    """
    if monthly_data:
        for item in monthly_data:
            avg_change = item.get('avg_change', 0.0)
            max_change = item.get('max_change', 0.0)
            median_change = item.get('median_change', 0.0)
            min_change = item.get('min_change', 0.0)
            positive_months_perc = item.get('positive_months_perc', 0.0) * 100
            positive_closes = item.get('positive_closes', 0)
            years = item.get('years', 'N/A')
            month = item.get('month', 'N/A')

            def format_with_color(value, decimals=2):
                color = 'red' if value < 0 else 'black'
                return f'<span style="color: {color}">{value:.{decimals}f}</span>'

            html += f"""
            <tr>
                <td>{month}</td>
                <td>{format_with_color(avg_change)}</td>
                <td>{format_with_color(max_change)}</td>
                <td>{format_with_color(median_change)}</td>
                <td>{format_with_color(min_change)}</td>
                <td>{positive_closes}</td>
                <td>{positive_months_perc:.2f}%</td>
                <td>{years}</td>
            </tr>
            """
    html += """
        </table>
        <h2>Yearly Analysis for {{ ticker or '' }}</h2>
        <div style="display: flex; flex-wrap: wrap; justify-content: space-around; margin-top: 20px; gap: 20px;">
            <div style="flex: 1; min-width: 300px; max-width: 400px;">
                <h3>Price Action (Line)</h3>
                <canvas id="yearlyPriceChart"></canvas>
            </div>
            <div style="flex: 1; min-width: 300px; max-width: 400px;">
                <h3>Performance (Bar)</h3>
                <canvas id="yearlyBarChart"></canvas>
            </div>
            <div style="flex: 1; min-width: 300px; max-width: 400px;">
                <h3>Combined Performance & Price</h3>
                <canvas id="combinedChart"></canvas>
            </div>
        </div>
        <h2>15-Year Monthly Return History</h2>
        <table border='1' {% if not yearly_monthly_data %}style="display: none;"{% endif %} id="yearlyMonthlySeasonalityTable">
            <tr>
                <th>Year</th>
                <th>Month</th>
                <th>Open</th>
                <th>Close</th>
                <th>Change</th>
            </tr>
    """
    if yearly_monthly_data:
        for item in yearly_monthly_data:
            change = float(item.get('change', 0.0)) if item.get('change') else 0.0
            open_price = float(item.get('open', 0.0)) if item.get('open') else 0.0
            close_price = float(item.get('close', 0.0)) if item.get('close') else 0.0
            year = item.get('year', 'N/A')
            month = item.get('month', 'N/A')

            def format_change_with_color(value, decimals=4):
                color = 'red' if value < 0 else 'black'
                return f'<span style="color: {color}">{value:.{decimals}f}</span>'

            html += f"""
            <tr>
                <td>{year}</td>
                <td>{month}</td>
                <td>{open_price:.2f}</td>
                <td>{close_price:.2f}</td>
                <td>{format_change_with_color(change)}</td>
            </tr>
            """
    html += """
        </table>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const commonYears = {{ common_years | tojson }};
        const performanceValuesFiltered = {{ performance_values_filtered | tojson }};
        const priceValuesFiltered = {{ price_values_filtered | tojson }};
        const performanceColors = performanceValuesFiltered.map(val => val >= 0 ? 'rgba(75, 192, 192, 0.7)' : 'rgba(255, 99, 132, 0.7)');
        const performanceBorderColors = performanceValuesFiltered.map(val => val >= 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)');

        const priceCtx = document.getElementById('yearlyPriceChart').getContext('2d');
        new Chart(priceCtx, {
            type: 'line',
            data: {
                labels: commonYears,
                datasets: [{
                    label: 'Yearly Closing Price',
                    data: priceValuesFiltered,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: { title: { display: true, text: 'Year' }, ticks: { maxRotation: 45, minRotation: 45 } },
                    y: { title: { display: true, text: 'Price ($)' }, beginAtZero: true }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        const barCtx = document.getElementById('yearlyBarChart').getContext('2d');
        new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: commonYears,
                datasets: [{
                    label: 'Yearly % Change',
                    data: performanceValuesFiltered,
                    backgroundColor: performanceColors,
                    borderColor: performanceBorderColors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: { title: { display: true, text: 'Year' }, ticks: { maxRotation: 45, minRotation: 45 } },
                    y: { title: { display: true, text: '%' }, beginAtZero: true }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        const combinedCtx = document.getElementById('combinedChart').getContext('2d');
        new Chart(combinedCtx, {
            type: 'bar',
            data: {
                labels: commonYears,
                datasets: [
                    {
                        type: 'line',
                        label: 'Yearly Closing Price',
                        data: priceValuesFiltered,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3,
                        yAxisID: 'y2'
                    },
                    {
                        type: 'bar',
                        label: 'Yearly % Change',
                        data: performanceValuesFiltered,
                        backgroundColor: performanceColors,
                        borderColor: performanceBorderColors,
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: { title: { display: true, text: 'Year' }, ticks: { maxRotation: 45, minRotation: 45 } },
                    y1: { 
                        type: 'linear', 
                        position: 'left', 
                        title: { display: true, text: '%' },
                        beginAtZero: true
                    },
                    y2: { 
                        type: 'linear', 
                        position: 'right', 
                        title: { display: true, text: 'Price ($)' },
                        beginAtZero: true,
                        grid: { drawOnChartArea: false }
                    }
                },
                plugins: {
                    legend: { display: true, position: 'top' }
                }
            }
        });
    </script>
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
        return jsonify({"error": str(e)}), 500
