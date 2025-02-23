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
ETF_EXPOSURE_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/exposure"
ETF_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/holdings"
ETF_INOUTFLOW_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/in-outflow"
ETF_INFO_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/info"

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
    <a href="/etf-research" style="margin-right: 20px;">ETF-Research</a>
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
        .pie-chart-container {{ display: none; transition: all 0.5s ease; }}
    </style>
    <div id="instContainer">
        <table border='1' class='inst-table' id='instTable'>
            <tr><th>Name</th><th>Live Price</th><th>Chart</th></tr>
    """
    if "error" not in data:
        institutions = data.get("data", []) if isinstance(data, dict) else data
        for inst in institutions:
            name = inst if isinstance(inst, str) else inst.get('name', 'N/A')
            html += f"<tr><td><a href='#' onclick='showHoldings(\"{name}\")'>{name}</a></td><td>{get_live_stock_price(name) if name.isupper() else 'N/A'}</td><td><a href='#' onclick='showPieChart(\"{name}\")'>View Chart</a></td></tr>"
    else:
        html += f"<tr><td colspan='3'>Error: {data['error']}</td></tr>"
    html += """
        </table>
        <div id="holdingsContainer" class="holdings-table">
            <button onclick="closeHoldings()">Close</button>
            <table border='1' id='holdingsTable'></table>
        </div>
        <div id="pieChartContainer" class="pie-chart-container">
            <button onclick="closePieChart()">Close</button>
            <canvas id="holdingsPieChart" width="400" height="400"></canvas>
        </div>
    </div>
    <script>
        function showHoldings(name) {
            fetch(`/institution/holdings?name=${encodeURIComponent(name)}`)
                .then(response => response.json())
                .then(data => {
                    let table = '<tr><th>Ticker</th><th>Units</th><th>Value</th><th>Live Price</th></tr>';
                    if (data.data) {
                        data.data.forEach(holding => {
                            table += '<tr><td>' + (holding.ticker || 'N/A') + '</td><td>' + 
                                    (holding.units || 'N/A') + '</td><td>' + 
                                    (holding.value || 'N/A') + '</td><td>' + 
                                    (get_live_stock_price(holding.ticker) || 'N/A') + '</td></tr>';
                        });
                    }
                    document.getElementById('holdingsTable').innerHTML = table;
                    document.getElementById('instTable').classList.add('hide');
                    document.getElementById('holdingsContainer').classList.add('show');
                    document.getElementById('pieChartContainer').classList.remove('show');
                })
                .catch(error => console.error('Error:', error));
        }
        function closeHoldings() {
            document.getElementById('instTable').classList.remove('hide');
            document.getElementById('holdingsContainer').classList.remove('show');
        }

        function showPieChart(name) {
            fetch(`/institution/holdings?name=${encodeURIComponent(name)}`)
                .then(response => response.json())
                .then(data => {
                    let holdings = {};
                    if (data.data) {
                        data.data.forEach(holding => {
                            holdings[holding.ticker || 'N/A'] = parseFloat(holding.units || 0);
                        });
                    }
                    const labels = Object.keys(holdings);
                    const dataValues = Object.values(holdings);

                    if (pieChart) pieChart.destroy();
                    const ctx = document.getElementById('holdingsPieChart').getContext('2d');
                    pieChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: labels,
                            datasets: [{
                                data: dataValues,
                                backgroundColor: [
                                    'rgba(255, 99, 132, 0.7)',
                                    'rgba(54, 162, 235, 0.7)',
                                    'rgba(255, 206, 86, 0.7)',
                                    'rgba(75, 192, 192, 0.7)',
                                    'rgba(153, 102, 255, 0.7)',
                                    'rgba(255, 159, 64, 0.7)'
                                ]
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: true,
                            plugins: {
                                legend: { position: 'right' },
                                title: { display: true, text: `Holdings Distribution for ${name}` }
                            }
                        }
                    });
                    document.getElementById('instTable').classList.add('hide');
                    document.getElementById('holdingsContainer').classList.remove('show');
                    document.getElementById('pieChartContainer').classList.add('show');
                })
                .catch(error => console.error('Error:', error));
        }

        function closePieChart() {
            document.getElementById('instTable').classList.remove('hide');
            document.getElementById('pieChartContainer').classList.remove('show');
        }

        let pieChart;
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

    # Pie Chart HTML for Holdings
    pie_chart_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <select id="institutionSelect" onchange="updatePieChart()">
        <option value="">Select an Institution</option>
    """
    for name in inst_names:
        pie_chart_html += f"<option value='{name}'>{name}</option>"
    pie_chart_html += """
    </select>
    <div id="pieChartContainer" style="display: none;">
        <button onclick="closePieChart()">Close</button>
        <canvas id="holdingsPieChart" width="400" height="400"></canvas>
    </div>
    <script>
        const holdingsDataMaster = {json.dumps(holdings_master)};
        let pieChart;

        function updatePieChart() {
            const institution = document.getElementById('institutionSelect').value;
            if (!institution) return;

            const holdings = holdingsDataMaster[institution] || {};
            const labels = Object.keys(holdings);
            const data = Object.values(holdings);

            if (pieChart) pieChart.destroy();
            const ctx = document.getElementById('holdingsPieChart').getContext('2d');
            pieChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(153, 102, 255, 0.7)',
                            'rgba(255, 159, 64, 0.7)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { position: 'right' },
                        title: { display: true, text: `Holdings Distribution for ${institution}` }
                    }
                }
            });
            document.getElementById('pieChartContainer').style.display = 'block';
        }

        function closePieChart() {
            document.getElementById('pieChartContainer').style.display = 'none';
            document.getElementById('institutionSelect').value = '';
            if (pieChart) pieChart.destroy();
        }
    </script>
    """

    html = f"""
    <h1>Research</h1>
    {MENU_BAR}
    <h2>All Institution Holdings</h2>
    {table_html}
    <h2>Top 10 Holdings by Institution</h2>
    {pie_chart_html}
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
    yearly_performance = None
    yearly_prices = None

    if ticker:
        # Fetch monthly seasonality data
        monthly_url = SEASONALITY_API_URL.format(ticker=ticker)
        monthly_response = get_api_data(monthly_url)
        if "error" in monthly_response:
            monthly_error = monthly_response["error"]
        else:
            monthly_data = monthly_response.get("data", [])

        # Fetch year-month seasonality data
        yearly_monthly_url = f"https://api.unusualwhales.com/api/seasonality/{ticker}/year-month"
        yearly_monthly_response = get_api_data(yearly_monthly_url)
        if "error" in yearly_monthly_response:
            yearly_monthly_error = yearly_monthly_response["error"]
        else:
            yearly_monthly_data = yearly_monthly_response.get("data", [])

        # Fetch yearly performance and prices for charts
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="max", interval="1mo")
            yearly_performance = hist['Close'].resample('Y').last().pct_change().dropna() * 100
            yearly_performance = yearly_performance.to_dict()
            years = [dt.strftime('%Y') for dt in yearly_performance.keys()]
            performance_values = list(yearly_performance.values())
            yearly_prices = hist['Close'].resample('Y').last().dropna().to_dict()
            price_years = [dt.strftime('%Y') for dt in yearly_prices.keys()]
            price_values = list(yearly_prices.values())
        except Exception as e:
            yearly_performance = {"error": f"Error fetching performance: {str(e)}"}
            yearly_prices = {"error": f"Error fetching prices: {str(e)}"}

    # Fetch ETF Info for the info bar
    etf_info = None
    etf_info_error = None
    if ticker:
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", [])

    html = f"""
    <h1>Seasonality - Per Ticker</h1>
    {MENU_BAR}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px;">
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
    """

    # Add Yearly Charts between Monthly and 15-Year Monthly Return History
    if ticker and yearly_performance and "error" not in yearly_performance and yearly_prices and "error" not in yearly_prices:
        common_years = list(set(years) & set(price_years))
        common_years.sort()
        performance_values_filtered = [performance_values[years.index(year)] for year in common_years if year in years]
        price_values_filtered = [price_values[price_years.index(year)] for year in common_years if year in price_years]

        html += f"""
        <h2>Yearly Analysis for {ticker}</h2>
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
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // Price Action Line Chart
            const priceCtx = document.getElementById('yearlyPriceChart').getContext('2d');
            const priceChart = new Chart(priceCtx, {
                type: 'line',
                data: {
                    labels: {json.dumps(common_years)},
                    datasets: [{
                        label: 'Yearly Closing Price',
                        data: {json.dumps(price_values_filtered)},
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

            // Performance Bar Chart
            const barCtx = document.getElementById('yearlyBarChart').getContext('2d');
            const barChart = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: {json.dumps(common_years)},
                    datasets: [{
                        label: 'Yearly % Change',
                        data: {json.dumps(performance_values_filtered)},
                        backgroundColor: {json.dumps([val >= 0 and 'rgba(75, 192, 192, 0.7)' or 'rgba(255, 99, 132, 0.7)' for val in performance_values_filtered])},
                        borderColor: {json.dumps([val >= 0 and 'rgba(75, 192, 192, 1)' or 'rgba(255, 99, 132, 1)' for val in performance_values_filtered])},
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

            // Combined Chart (Price Line + Performance Bars)
            const combinedCtx = document.getElementById('combinedChart').getContext('2d');
            const combinedChart = new Chart(combinedCtx, {
                type: 'bar',
                data: {
                    labels: {json.dumps(common_years)},
                    datasets: [
                        {
                            type: 'line',
                            label: 'Yearly Closing Price',
                            data: {json.dumps(price_values_filtered)},
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 3,
                            yAxisID: 'y2'  // Right y-axis for price
                        },
                        {
                            type: 'bar',
                            label: 'Yearly % Change',
                            data: {json.dumps(performance_values_filtered)},
                            backgroundColor: {json.dumps([val >= 0 and 'rgba(75, 192, 192, 0.7)' or 'rgba(255, 99, 132, 0.7)' for val in performance_values_filtered])},
                            borderColor: {json.dumps([val >= 0 and 'rgba(75, 192, 192, 1)' or 'rgba(255, 99, 132, 1)' for val in performance_values_filtered])},
                            borderWidth: 1,
                            yAxisID: 'y1'  // Left y-axis for % change
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
                            grid: { drawOnChartArea: false }  // Hide grid lines for right y-axis to avoid overlap
                        }
                    },
                    plugins: {
                        legend: { display: true, position: 'top' }
                    }
                }
            });
        </script>
        """

    html += """
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
    # Add ETF Info Table at the top
    html = f"""
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {ticker}</h2>
            {'<p style="color: red;">Error fetching ETF Info: ' + etf_info_error + '</p>' if etf_info_error else ''}
            <table border='1' {'style="display: none;"' if not etf_info else ''} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info and len(etf_info) > 0:
        info = etf_info[0]  # Assuming the first item contains the ETF info
        for key, value in info.items():
            if value is not None:  # Skip None values
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
    html += """
            </table>
        </div>
    </div>
    """ + html

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

    # Fetch ETF Info for the info bar
    etf_info = None
    etf_info_error = None
    if ticker != 'ALL':
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", [])

    etf_tickers = ['SPY', 'QQQ', 'IWM', 'XLE', 'XLC', 'XLK', 'XLV', 'XLP', 'XLY', 'XLRE', 'XLF', 'XLI', 'XLB']

    html = f"""
    <h1>Seasonality - ETF Market</h1>
    {MENU_BAR}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {ticker}</h2>
            {'<p style="color: red;">Error fetching ETF Info: ' + etf_info_error + '</p>' if etf_info_error else ''}
            <table border='1' {'style="display: none;"' if not etf_info or ticker == 'ALL' else ''} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info and len(etf_info) > 0 and ticker != 'ALL':
        info = etf_info[0]  # Assuming the first item contains the ETF info
        for key, value in info.items():
            if value is not None:  # Skip None values
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
    html += """
            </table>
        </div>
        <div style="flex: 2; min-width: 300px;">
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
        # Ensure years match for both datasets (using the intersection of years available)
        common_years = list(set(years) & set(price_years))
        common_years.sort()  # Sort to maintain chronological order
        performance_values_filtered = [performance_values[years.index(year)] for year in common_years if year in years]
        price_values_filtered = [price_values[price_years.index(year)] for year in common_years if year in price_years]

        html += f"""
        <h2>Yearly Analysis for {ticker}</h2>
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
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // Price Action Line Chart
            const priceCtx = document.getElementById('yearlyPriceChart').getContext('2d');
            const priceChart = new Chart(priceCtx, {
                type: 'line',
                data: {
                    labels: {json.dumps(common_years)},
                    datasets: [{
                        label: 'Yearly Closing Price',
                        data: {json.dumps(price_values_filtered)},
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

            // Performance Bar Chart
            const barCtx = document.getElementById('yearlyBarChart').getContext('2d');
            const barChart = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: {json.dumps(common_years)},
                    datasets: [{
                        label: 'Yearly % Change',
                        data: {json.dumps(performance_values_filtered)},
                        backgroundColor: {json.dumps([val >= 0 and 'rgba(75, 192, 192, 0.7)' or 'rgba(255, 99, 132, 0.7)' for val in performance_values_filtered])},
                        borderColor: {json.dumps([val >= 0 and 'rgba(75, 192, 192, 1)' or 'rgba(255, 99, 132, 1)' for val in performance_values_filtered])},
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

            // Combined Chart (Price Line + Performance Bars)
            const combinedCtx = document.getElementById('combinedChart').getContext('2d');
            const combinedChart = new Chart(combinedCtx, {
                type: 'bar',
                data: {
                    labels: {json.dumps(common_years)},
                    datasets: [
                        {
                            type: 'line',
                            label: 'Yearly Closing Price',
                            data: {json.dumps(price_values_filtered)},
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            fill: true,
                            tension: 0.3,
                            pointRadius: 3,
                            yAxisID: 'y2'  // Right y-axis for price
                        },
                        {
                            type: 'bar',
                            label: 'Yearly % Change',
                            data: {json.dumps(performance_values_filtered)},
                            backgroundColor: {json.dumps([val >= 0 and 'rgba(75, 192, 192, 0.7)' or 'rgba(255, 99, 132, 0.7)' for val in performance_values_filtered])},
                            borderColor: {json.dumps([val >= 0 and 'rgba(75, 192, 192, 1)' or 'rgba(255, 99, 132, 1)' for val in performance_values_filtered])},
                            borderWidth: 1,
                            yAxisID: 'y1'  // Left y-axis for % change
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
                            grid: { drawOnChartArea: false }  // Hide grid lines for right y-axis to avoid overlap
                        }
                    },
                    plugins: {
                        legend: { display: true, position: 'top' }
                    }
                }
            });
        </script>
        """

        # Add Yearly Table below the charts
        html += f"""
        <h2>Yearly Data for {ticker}</h2>
        <table border='1' id="yearlyDataTable">
            <tr>
                <th>Year</th>
                <th>Yearly % Change</th>
                <th>Yearly Closing Price ($)</th>
            </tr>
        """
        for year in common_years:
            perf_idx = years.index(year) if year in years else -1
            price_idx = price_years.index(year) if year in price_years else -1
            perf_value = performance_values[perf_idx] if perf_idx != -1 else "N/A"
            price_value = price_values[price_idx] if price_idx != -1 else "N/A"
            html += f"""
            <tr>
                <td>{year}</td>
                <td>{perf_value:.2f}%</td>
                <td>${price_value:.2f}</td>
            </tr>
            """
        html += """
        </table>
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

@app.route('/etf-research')
def etf_research():
    html = f"""
    <h1>ETF-Research</h1>
    {MENU_BAR}
    <p>Select a sub-page to view ETF data.</p>
    <ul>
        <li><a href="/etf-research/exposure">Exposure</a></li>
        <li><a href="/etf-research/holdings">Holdings</a></li>
        <li><a href="/etf-research/in-outflow">In-Out Flow</a></li>
    </ul>
    """
    return render_template_string(html)

@app.route('/etf-research/exposure', methods=['GET'])
def etf_exposure():
    ticker = request.args.get('ticker', '').upper()
    data = None
    error = None

    if ticker:
        response = get_api_data(ETF_EXPOSURE_API_URL.format(ticker=ticker))
        if "error" in response:
            error = response["error"]
        else:
            data = response.get("data", [])

    # Fetch ETF Info for the info bar
    etf_info = None
    etf_info_error = None
    if ticker:
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", [])

    html = f"""
    <h1>ETF-Research - Exposure</h1>
    {MENU_BAR}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {ticker}</h2>
            {'<p style="color: red;">Error fetching ETF Info: ' + etf_info_error + '</p>' if etf_info_error else ''}
            <table border='1' {'style="display: none;"' if not etf_info else ''} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info and len(etf_info) > 0:
        info = etf_info[0]  # Assuming the first item contains the ETF info
        for key, value in info.items():
            if value is not None:  # Skip None values
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
    html += """
            </table>
        </div>
        <div style="flex: 2; min-width: 300px;">
            <form method="GET">
                <label>Enter ETF Ticker (e.g., SPY, QQQ): </label>
                <input type="text" name="ticker" value="{ticker}" placeholder="Enter ETF ticker symbol">
                <button type="submit">Search</button>
            </form>
            <h3>Or Click a Predefined ETF:</h3>
            <div>
                <button onclick="window.location.href='/etf-research/exposure?ticker=SPY'">SPY</button>
                <button onclick="window.location.href='/etf-research/exposure?ticker=QQQ'">QQQ</button>
                <button onclick="window.location.href='/etf-research/exposure?ticker=IWM'">IWM</button>
                <button onclick="window.location.href='/etf-research/exposure?ticker=XLF'">XLF</button>
            </div>
            {'<p style="color: red;">Error: ' + error + '</p>' if error else ''}
            {'<p>No data available for ticker ' + ticker + '</p>' if not error and not data else ''}
            <table border='1' {'style="display: none;"' if not data else ''} id="exposureTable">
                <tr>
                    <th>ETF</th>
                    <th>Full Name</th>
                    <th>Last Price</th>
                    <th>Previous Price</th>
                    <th>Shares</th>
                    <th>Weight (%)</th>
                </tr>
    """
    if data:
        for item in data:
            html += f"""
            <tr>
                <td>{item['etf']}</td>
                <td>{item['full_name']}</td>
                <td>{item['last_price']}</td>
                <td>{item['prev_price']}</td>
                <td>{item['shares']}</td>
                <td>{float(item['weight']):.2f}%</td>
            </tr>
            """
    html += """
            </table>
        </div>
    </div>
    """
    return render_template_string(html)

@app.route('/etf-research/holdings', methods=['GET'])
def etf_holdings():
    ticker = request.args.get('ticker', '').upper()
    data = None
    error = None

    if ticker:
        response = get_api_data(ETF_HOLDINGS_API_URL.format(ticker=ticker))
        if "error" in response:
            error = response["error"]
        else:
            data = response.get("data", [])

    # Fetch ETF Info for the info bar
    etf_info = None
    etf_info_error = None
    if ticker:
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", [])

    html = f"""
    <h1>ETF-Research - Holdings</h1>
    {MENU_BAR}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {ticker}</h2>
            {'<p style="color: red;">Error fetching ETF Info: ' + etf_info_error + '</p>' if etf_info_error else ''}
            <table border='1' {'style="display: none;"' if not etf_info else ''} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info and len(etf_info) > 0:
        info = etf_info[0]  # Assuming the first item contains the ETF info
        for key, value in info.items():
            if value is not None:  # Skip None values
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
    html += """
            </table>
        </div>
        <div style="flex: 2; min-width: 300px;">
            <form method="GET">
                <label>Enter ETF Ticker (e.g., SPY, QQQ): </label>
                <input type="text" name="ticker" value="{ticker}" placeholder="Enter ETF ticker symbol">
                <button type="submit">Search</button>
            </form>
            <h3>Or Click a Predefined ETF:</h3>
            <div>
                <button onclick="window.location.href='/etf-research/holdings?ticker=SPY'">SPY</button>
                <button onclick="window.location.href='/etf-research/holdings?ticker=QQQ'">QQQ</button>
                <button onclick="window.location.href='/etf-research/holdings?ticker=IWM'">IWM</button>
                <button onclick="window.location.href='/etf-research/holdings?ticker=XLF'">XLF</button>
            </div>
            {'<p style="color: red;">Error: ' + error + '</p>' if error else ''}
            {'<p>No data available for ticker ' + ticker + '</p>' if not error and not data else ''}
            <table border='1' {'style="display: none;"' if not data else ''} id="holdingsTable">
                <tr>
                    <th>Ticker</th>
                    <th>Name</th>
                    <th>Shares</th>
                    <th>Weight (%)</th>
                    <th>Market Value</th>
                </tr>
    """
    if data:
        for item in data:
            html += f"""
            <tr>
                <td>{item['ticker']}</td>
                <td>{item['name']}</td>
                <td>{item['shares']}</td>
                <td>{float(item['weight']):.2f}%</td>
                <td>{item['market_value']}</td>
            </tr>
            """
    html += """
            </table>
        </div>
    </div>
    """
    return render_template_string(html)

@app.route('/etf-research/in-outflow', methods=['GET'])
def etf_in_outflow():
    ticker = request.args.get('ticker', '').upper()
    data = None
    error = None

    if ticker:
        response = get_api_data(ETF_INOUTFLOW_API_URL.format(ticker=ticker))
        if "error" in response:
            error = response["error"]
        else:
            data = response.get("data", [])

    # Fetch ETF Info for the info bar
    etf_info = None
    etf_info_error = None
    if ticker:
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", [])

    html = f"""
    <h1>ETF-Research - In-Out Flow</h1>
    {MENU_BAR}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {ticker}</h2>
            {'<p style="color: red;">Error fetching ETF Info: ' + etf_info_error + '</p>' if etf_info_error else ''}
            <table border='1' {'style="display: none;"' if not etf_info else ''} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info and len(etf_info) > 0:
        info = etf_info[0]  # Assuming the first item contains the ETF info
        for key, value in info.items():
            if value is not None:  # Skip None values
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
    html += """
            </table>
        </div>
        <div style="flex: 2; min-width: 300px;">
            <form method="GET">
                <label>Enter ETF Ticker (e.g., SPY, QQQ): </label>
                <input type="text" name="ticker" value="{ticker}" placeholder="Enter ETF ticker symbol">
                <button type="submit">Search</button>
            </form>
            <h3>Or Click a Predefined ETF:</h3>
            <div>
                <button onclick="window.location.href='/etf-research/in-outflow?ticker=SPY'">SPY</button>
                <button onclick="window.location.href='/etf-research/in-outflow?ticker=QQQ'">QQQ</button>
                <button onclick="window.location.href='/etf-research/in-outflow?ticker=IWM'">IWM</button>
                <button onclick="window.location.href='/etf-research/in-outflow?ticker=XLF'">XLF</button>
            </div>
            {'<p style="color: red;">Error: ' + error + '</p>' if error else ''}
            {'<p>No data available for ticker ' + ticker + '</p>' if not error and not data else ''}
            <table border='1' {'style="display: none;"' if not data else ''} id="inOutflowTable">
                <tr>
                    <th>Date</th>
                    <th>Inflow</th>
                    <th>Outflow</th>
                    <th>Net Flow</th>
                </tr>
    """
    if data:
        for item in data:
            html += f"""
            <tr>
                <td>{item['date']}</td>
                <td>{item['inflow']}</td>
                <td>{item['outflow']}</td>
                <td>{item['net_flow']}</td>
            </tr>
            """
    html += """
            </table>
        </div>
    </div>
    """
    return render_template_string(html)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
