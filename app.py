import os
from flask import Flask, render_template_string, request, jsonify
import requests
import json
import yfinance as yf

app = Flask(__name__)

# API configuration
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"
INST_LIST_API_URL = "https://api.unusualwhales.com/api/institutions"
INST_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/institution/{name}/holdings"
SEASONALITY_API_URL = "https://api.unusualwhales.com/api/seasonality/{ticker}/monthly"
SEASONALITY_MARKET_API_URL = "https://api.unusualwhales.com/api/seasonality/market"

def get_api_data(url, params=None):
    headers = {"Authorization": f"Bearer {APIKEY}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")  # Exclude sensitive headers if needed
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Request Error - URL: {url}, Status Code: {getattr(response, 'status_code', 'N/A')}, Error: {str(e)}")
        return {"error": f"{str(e)}"}

def get_live_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        live_price = stock.info['regularMarketPrice']
        return live_price
    except Exception as e:
        return f"Error: {str(e)}"

MENU_BAR = """
<div style="background-color: #f8f8f8; padding: 10px;">
    <a href="/" style="margin-right: 20px;">Home</a>
    <a href="/institution/list" style="margin-right: 20px;">Institution List</a>
    <a href="/research" style="margin-right: 20px;">Research</a>
    <a href="/seasonality" style="margin-right: 20px;">Seasonality</a>
</div>
"""

@app.route('/')
def home():
    html = f"""
    <h1>Unusual Whales Dashboard</h1>
    {MENU_BAR}
    <p>Welcome to the Unusual Whales Dashboard. Select a page from the menu above.</p>
    """
    return render_template_string(html)

@app.route('/institution/list')
def institution_list():
    data = get_api_data(INST_LIST_API_URL)
    html = f"""
    <h1>Institution List</h1>
    {MENU_BAR}
    <style>
        .inst-table {{ transition: all 0.5s ease; }}
        .holdings-table {{ display: none; transition: all 0.5s ease; }}
        .show {{ display: block; }}
        .hide {{ display: none; }}
    </style>
    <div id="instContainer">
        <table border='1' class='inst-table' id='instTable'>
            <tr><th>Name</th><th>Live Price</th></tr>
    """
    if "error" not in data:
        institutions = data.get("data", []) if isinstance(data, dict) else data
        for inst in institutions:
            name = inst if isinstance(inst, str) else inst.get('name', 'N/A')
            html += f"<tr><td><a href='#' onclick='showHoldings(\"{name}\")'>{name}</a></td><td>{get_live_stock_price(name)}</td></tr>"
    html += """
        </table>
        <div id="holdingsContainer" class="holdings-table">
            <button onclick="closeHoldings()">Close</button>
            <table border='1' id='holdingsTable'></table>
        </div>
    </div>
    <script>
        function showHoldings(name) {
            fetch(`/institution/holdings?name=${encodeURIComponent(name)}`)
                .then(response => response.json())
                .then(data => {
                    let table = '<tr><th>Ticker</th><th>Units</th><th>Value</th></tr>';
                    if (data.data) {
                        data.data.forEach(holding => {
                            table += '<tr><td>' + (holding.ticker || 'N/A') + '</td><td>' + 
                                    (holding.units || 'N/A') + '</td><td>' + 
                                    (holding.value || 'N/A') + '</td></tr>';
                        });
                    }
                    document.getElementById('holdingsTable').innerHTML = table;
                    document.getElementById('instTable').classList.add('hide');
                    document.getElementById('holdingsContainer').classList.add('show');
                })
                .catch(error => console.error('Error:', error));
        }
        function closeHoldings() {
            document.getElementById('instTable').classList.remove('hide');
            document.getElementById('holdingsContainer').classList.remove('show');
        }
    </script>
    """
    return render_template_string(html)

@app.route('/institution/holdings')
def get_institution_holdings():
    name = request.args.get('name')
    data = get_api_data(INST_HOLDINGS_API_URL.format(name=name))
    return jsonify(data)

@app.route('/research')
def research():
    inst_data = get_api_data(INST_LIST_API_URL)
    if "error" in inst_data:
        html = f"""
        <h1>Research</h1>
        {MENU_BAR}
        <p>Error fetching institution list: {inst_data['error']}</p>
        """
        return render_template_string(html)

    institutions = inst_data.get("data", [])
    holdings_master = {}
    inst_totals = {}

    for inst in institutions:
        name = inst if isinstance(inst, str) else inst.get('name', 'N/A')
        holdings_data = get_api_data(INST_HOLDINGS_API_URL.format(name=name))
        if "error" not in holdings_data:
            holdings = holdings_data.get("data", [])
            total_units = 0
            for holding in holdings:
                ticker = holding.get("ticker")
                units = float(holding.get("units", 0) or 0)
                total_units += units
                if ticker:
                    if ticker not in holdings_master:
                        holdings_master[ticker] = {}
                    holdings_master[ticker][name] = units
            inst_totals[name] = total_units

    inst_names = sorted(inst_totals.keys(), key=lambda x: inst_totals[x], reverse=True)[:10]

    table_html = "<table border='1' id='masterTable'><tr><th>Ticker</th><th>Total Units</th><th>Live Stock Price</th>"
    for name in inst_names:
        table_html += f"<th>{name}</th>"
    table_html += "</tr>"

    ticker_options = ""
    for ticker, inst_holdings in holdings_master.items():
        total_units = sum(inst_holdings.values())
        live_price = get_live_stock_price(ticker)
        table_html += f"<tr><td>{ticker}</td><td>{total_units}</td><td>{live_price if isinstance(live_price, (int, float)) else live_price}</td>"
        for name in inst_names:
            units = inst_holdings.get(name, 0)
            percentage = (units / total_units * 100) if total_units > 0 else 0
            table_html += f"<td>{percentage:.1f}%</td>"
        table_html += "</tr>"
        ticker_options += f"<option value='{ticker}'>{ticker}</option>"
    table_html += "</table>"

    chart_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <select id="tickerSelect" onchange="updateChart()">
        <option value="">Select a Ticker</option>
        {ticker_options}
    </select>
    <canvas id="holdingsChart" width="600" height="300"></canvas>
    <script>
        const holdingsData = {json.dumps(holdings_master)};
        let chart;

        function updateChart() {{
            const ticker = document.getElementById('tickerSelect').value;
            if (!ticker) return;

            const ctx = document.getElementById('holdingsChart').getContext('2d');
            const data = holdingsData[ticker] || {{}};
            const allLabels = Object.keys(data);
            const allValues = Object.values(data);
            const sortedData = allLabels.map((label, idx) => ({{ label: label, value: allValues[idx] }}))
                .sort((a, b) => b.value - a.value)
                .slice(0, 10);
            const labels = sortedData.map(d => d.label);
            const values = sortedData.map(d => d.value);

            if (chart) chart.destroy();
            chart = new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Units Held',
                        data: values,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    scales: {{
                        x: {{ beginAtZero: true, title: {{ display: true, text: 'Units Held' }} }},
                        y: {{ title: {{ display: true, text: 'Institution' }} }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});
        }}
    </script>
    """

    html = f"""
    <h1>Research</h1>
    {MENU_BAR}
    <h2>All Institution Holdings</h2>
    {table_html}
    <h2>Top 10 Holdings by Institution</h2>
    {chart_html}
    """
    return render_template_string(html)

@app.route('/seasonality')
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

@app.route('/seasonality/per-ticker', methods=['GET'])
def seasonality_per_ticker():
    ticker = request.args.get('ticker', '').upper()
    monthly_data = None
    yearly_monthly_data = None
    monthly_error = None
    yearly_monthly_error = None

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

    html = f"""
    <h1>Seasonality - Per Ticker</h1>
    {MENU_BAR}
    <div>
        <form method="GET">
            <label>Enter Ticker (e.g., AAPL, TSLA, PLTR): </label>
            <input type="text" name="ticker" value="{ticker}" placeholder="Enter ticker symbol">
            <button type="submit">GO</button>
        </form>
        {'<p style="color: red;">Error (Monthly Data): ' + monthly_error + '</p>' if monthly_error else ''}
        {'<p style="color: red;">Error (Year-Month Data): ' + yearly_monthly_error + '</p>' if yearly_monthly_error else ''}
        {'<p>No monthly data available for ticker ' + ticker + '</p>' if not monthly_error and not monthly_data else ''}
        {'<p>No year-month data available for ticker ' + ticker + '</p>' if not yearly_monthly_error and not yearly_monthly_data else ''}

        <h2>Monthly Seasonality Statistics</h2>
        <table border='1' {'style="display: none;"' if not monthly_data else ''} id="monthlySeasonalityTable">
            <tr>
                <th><a href="#" onclick="sortTable('month', 'monthly')">Month</a></th>
                <th><a href="#" onclick="sortTable('avg_change', 'monthly')">Avg Change</a></th>
                <th><a href="#" onclick="sortTable('max_change', 'monthly')">Max Change</a></th>
                <th><a href="#" onclick="sortTable('median_change', 'monthly')">Median Change</a></th>
                <th><a href="#" onclick="sortTable('min_change', 'monthly')">Min Change</a></th>
                <th><a href="#" onclick="sortTable('positive_closes', 'monthly')">Positive Closes</a></th>
                <th><a href="#" onclick="sortTable('positive_months_perc', 'monthly')">Positive Months %</a></th>
                <th><a href="#" onclick="sortTable('years', 'monthly')">Years</a></th>
            </tr>
    """
    if monthly_data:
        for item in monthly_data:
            avg_change = item['avg_change']
            max_change = item['max_change']
            median_change = item['median_change']
            min_change = item['min_change']
            positive_months_perc = item['positive_months_perc'] * 100

            def format_with_color(value, decimals=2):
                color = 'red' if value < 0 else 'black'
                return f'<span style="color: {color}">{value:.{decimals}f}</span>'

            html += f"""
            <tr>
                <td>{item['month']}</td>
                <td>{format_with_color(avg_change)}</td>
                <td>{format_with_color(max_change)}</td>
                <td>{format_with_color(median_change)}</td>
                <td>{format_with_color(min_change)}</td>
                <td>{item['positive_closes']}</td>
                <td>{positive_months_perc:.2f}%</td>
                <td>{item['years']}</td>
            </tr>
            """
    html += """
        </table>

        <h2>15-Year Monthly Return History</h2>
        <table border='1' {'style="display: none;"' if not yearly_monthly_data else ''} id="yearlyMonthlySeasonalityTable">
            <tr>
                <th><a href="#" onclick="sortTable('year', 'yearly')">Year</a></th>
                <th><a href="#" onclick="sortTable('month', 'yearly')">Month</a></th>
                <th><a href="#" onclick="sortTable('open', 'yearly')">Open</a></th>
                <th><a href="#" onclick="sortTable('close', 'yearly')">Close</a></th>
                <th><a href="#" onclick="sortTable('change', 'yearly')">Change</a></th>
            </tr>
    """
    if yearly_monthly_data:
        for item in yearly_monthly_data:
            change = float(item['change']) if item['change'] else 0.0
            open_price = float(item['open']) if item['open'] else 0.0
            close_price = float(item['close']) if item['close'] else 0.0

            def format_change_with_color(value, decimals=4):
                color = 'red' if value < 0 else 'black'
                return f'<span style="color: {color}">{value:.{decimals}f}</span>'

            html += f"""
            <tr>
                <td>{item['year']}</td>
                <td>{item['month']}</td>
                <td>{open_price:.2f}</td>
                <td>{close_price:.2f}</td>
                <td>{format_change_with_color(change)}</td>
            </tr>
            """
    html += """
        </table>
    </div>
    <script>
        let sortStates = {
            monthly: { col: 'month', dir: 'asc' },
            yearly: { col: 'year', dir: 'asc' }
        };

        function sortTable(col, tableType) {
            const current = sortStates[tableType];
            const newDir = current.col === col && current.dir === 'asc' ? 'desc' : 'asc';
            sortStates[tableType] = { col: col, dir: newDir };

            let url = `/seasonality/per-ticker?ticker={ticker}`;
            if (tableType === 'monthly') {
                url += `&sort_col=${col}&sort_dir=${newDir}&table=monthly`;
            } else {
                url += `&sort_col=${col}&sort_dir=${newDir}&table=yearly`;
            }
            window.location.href = url;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const sortCol = urlParams.get('sort_col');
        const sortDir = urlParams.get('sort_dir');
        const tableType = urlParams.get('table');
        if (sortCol && sortDir && tableType) {
            sortStates[tableType].col = sortCol;
            sortStates[tableType].dir = sortDir;
        }
    </script>
    """
    return render_template_string(html)

@app.route('/seasonality/etf-market', methods=['GET'])
def seasonality_etf_market():
    ticker = request.args.get('ticker', 'ALL').upper()
    data = None
    error = None
    yearly_performance = None
    yearly_prices = None

    response = get_api_data(SEASONALITY_MARKET_API_URL)
    if "error" in response:
        error = response["error"]
        print(f"API Error for {SEASONALITY_MARKET_API_URL}: {error}")
    else:
        all_data = response.get("data", [])
        data = [item for item in all_data if item['ticker'] == ticker] if ticker != 'ALL' else all_data

    if ticker != 'ALL':
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="max", interval="1mo")
            # Yearly performance (% change)
            yearly_performance = hist['Close'].resample('Y').last().pct_change().dropna() * 100
            yearly_performance = yearly_performance.to_dict()
            years = [dt.strftime('%Y') for dt in yearly_performance.keys()]
            performance_values = list(yearly_performance.values())
            # Yearly closing prices
            yearly_prices = hist['Close'].resample('Y').last().dropna().to_dict()
            price_years = [dt.strftime('%Y') for dt in yearly_prices.keys()]
            price_values = list(yearly_prices.values())
        except Exception as e:
            yearly_performance = {"error": f"Error fetching performance: {str(e)}"}
            yearly_prices = {"error": f"Error fetching prices: {str(e)}"}

    etf_tickers = ['SPY', 'QQQ', 'IWM', 'XLE', 'XLC', 'XLK', 'XLV', 'XLP', 'XLY', 'XLRE', 'XLF', 'XLI', 'XLB']

    html = f"""
    <h1>Seasonality - ETF Market</h1>
    {MENU_BAR}
    <div>
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
        {'<p style="color: red;">Error: ' + error + '</p>' if error else ''}
        {'<p>No data available for ticker ' + ticker + '</p>' if not error and not data else ''}
        <table border='1' {'style="display: none;"' if not data else ''} id="etfMarketTable">
            <tr>
                <th><a href="#" onclick="sortTable('ticker')">Ticker</a></th>
                <th><a href="#" onclick="sortTable('month')">Month</a></th>
                <th><a href="#" onclick="sortTable('avg_change')">Avg Change</a></th>
                <th><a href="#" onclick="sortTable('max_change')">Max Change</a></th>
                <th><a href="#" onclick="sortTable('median_change')">Median Change</a></th>
                <th><a href="#" onclick="sortTable('min_change')">Min Change</a></th>
                <th><a href="#" onclick="sortTable('positive_closes')">Positive Closes</a></th>
                <th><a href="#" onclick="sortTable('positive_months_perc')">Positive Months %</a></th>
                <th><a href="#" onclick="sortTable('years')">Years</a></th>
                <th>Live Price</th>
            </tr>
    """
    if data:
        for item in data:
            avg_change = float(item['avg_change']) if item['avg_change'] else 0.0
            max_change = float(item['max_change']) if item['max_change'] else 0.0
            median_change = float(item['median_change']) if item['median_change'] else 0.0
            min_change = float(item['min_change']) if item['min_change'] else 0.0
            positive_months_perc = float(item['positive_months_perc']) * 100
            live_price = get_live_stock_price(item['ticker'])

            def format_with_color(value, decimals=2):
                color = 'red' if value < 0 else 'black'
                return f'<span style="color: {color}">{value:.{decimals}f}</span>'

            html += f"""
            <tr>
                <td>{item['ticker']}</td>
                <td>{item['month']}</td>
                <td>{format_with_color(avg_change)}</td>
                <td>{format_with_color(max_change)}</td>
                <td>{format_with_color(median_change)}</td>
                <td>{format_with_color(min_change)}</td>
                <td>{item['positive_closes']}</td>
                <td>{positive_months_perc:.2f}%</td>
                <td>{item['years']}</td>
                <td>{live_price if isinstance(live_price, (int, float)) else live_price}</td>
            </tr>
            """

    html += """
        </table>
    """

    if ticker != 'ALL' and yearly_performance and "error" not in yearly_performance and yearly_prices and "error" not in yearly_prices:
        html += f"""
        <h2>Yearly Analysis for {ticker}</h2>
        <div style="display: flex; flex-wrap: wrap; justify-content: space-around; margin-top: 20px;">
            <div style="flex: 1; min-width: 300px; margin: 10px;">
                <h3>Performance (Line)</h3>
                <canvas id="yearlyLineChart"></canvas>
            </div>
            <div style="flex: 1; min-width: 300px; margin: 10px;">
                <h3>Performance (Bar)</h3>
                <canvas id="yearlyBarChart"></canvas>
            </div>
            <div style="flex: 1; min-width: 300px; margin: 10px;">
                <h3>Closing Price</h3>
                <canvas id="yearlyPriceChart"></canvas>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // Line Chart (Performance)
            const lineCtx = document.getElementById('yearlyLineChart').getContext('2d');
            const lineChart = new Chart(lineCtx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(years)},
                    datasets: [{{
                        label: 'Yearly % Change',
                        data: {json.dumps(performance_values)},
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {{
                        x: {{ title: {{ display: true, text: 'Year' }}, ticks: {{ maxRotation: 45, minRotation: 45 }} }},
                        y: {{ title: {{ display: true, text: '%' }}, beginAtZero: true }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});

            // Bar Chart (Performance)
            const barCtx = document.getElementById('yearlyBarChart').getContext('2d');
            const barChart = new Chart(barCtx, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(years)},
                    datasets: [{{
                        label: 'Yearly % Change',
                        data: {json.dumps(performance_values)},
                        backgroundColor: {json.dumps([val >= 0 and 'rgba(75, 192, 192, 0.7)' or 'rgba(255, 99, 132, 0.7)' for val in performance_values])},
                        borderColor: {json.dumps([val >= 0 and 'rgba(75, 192, 192, 1)' or 'rgba(255, 99, 132, 1)' for val in performance_values])},
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {{
                        x: {{ title: {{ display: true, text: 'Year' }}, ticks: {{ maxRotation: 45, minRotation: 45 }} }},
                        y: {{ title: {{ display: true, text: '%' }}, beginAtZero: true }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});

            // Line Chart (Closing Price)
            const priceCtx = document.getElementById('yearlyPriceChart').getContext('2d');
            const priceChart = new Chart(priceCtx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(price_years)},
                    datasets: [{{
                        label: 'Yearly Closing Price',
                        data: {json.dumps(price_values)},
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {{
                        x: {{ title: {{ display: true, text: 'Year' }}, ticks: {{ maxRotation: 45, minRotation: 45 }} }},
                        y: {{ title: {{ display: true, text: 'Price ($)' }}, beginAtZero: true }}
                    }},
                    plugins: {{
                        legend: {{ display: false }}
                    }}
                }}
            }});
        </script>
        """
    elif ticker != 'ALL' and (yearly_performance and "error" in yearly_performance or yearly_prices and "error" in yearly_prices):
        html += f"<p style='color: red;'>{(yearly_performance.get('error', '') if yearly_performance else '') + ' ' + (yearly_prices.get('error', '') if yearly_prices else '')}</p>"

    html += """
    </div>
    <script>
        let sortState = { col: 'ticker', dir: 'asc' };

        function sortTable(col) {
            const newDir = sortState.col === col && sortState.dir === 'asc' ? 'desc' : 'asc';
            sortState = { col: col, dir: newDir };
            window.location.href = `/seasonality/etf-market?ticker={ticker}&sort_col=${col}&sort_dir=${newDir}`;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const sortCol = urlParams.get('sort_col');
        const sortDir = urlParams.get('sort_dir');
        if (sortCol && sortDir) {
            sortState.col = sortCol;
            sortState.dir = sortDir;
        }
    </script>
    """
    return render_template_string(html)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
