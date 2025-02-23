from flask import Blueprint, render_template_string, request
from common import get_api_data, get_live_stock_price, MENU_BAR, SEASONALITY_API_URL, SEASONALITY_MARKET_API_URL, ETF_INFO_API_URL

seasonality_bp = Blueprint('seasonality', __name__, url_prefix='/')

@seasonality_bp.route('/seasonality')
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

@seasonality_bp.route('/seasonality/per-ticker', methods=['GET'])
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
            etf_info = etf_info_response.get("data", {})  # Get the dictionary under "data"

    # Serialize JSON data for JavaScript
    common_years = []
    performance_values_filtered = []
    price_values_filtered = []
    if ticker and yearly_performance and "error" not in yearly_performance and yearly_prices and "error" not in yearly_prices:
        common_years = list(set(years) & set(price_years))
        common_years.sort()
        performance_values_filtered = [performance_values[years.index(year)] for year in common_years if year in years]
        price_values_filtered = [price_values[price_years.index(year)] for year in common_years if year in price_years]

    # Build HTML with proper conditional rendering
    html = f"""
    <h1>Seasonality - Per Ticker</h1>
    {MENU_BAR}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {ticker or ''}</h2>
            {'<p style="color: red;">Error fetching ETF Info: {etf_info_error}</p>' if etf_info_error else ''}
            <table border='1' {'style="display: none;"' if not etf_info else ''} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info:
        for key, value in etf_info.items():
            if value is not None:  # Skip None values
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
    html += """
            </table>
        </div>
        <div style="flex: 2; min-width: 300px;">
            <form method="GET">
                <label>Enter Ticker (e.g., AAPL, TSLA, PLTR): </label>
                <input type="text" name="ticker" value="{ticker}" placeholder="Enter ticker symbol">
                <button type="submit">GO</button>
            </form>
            {f'<p style="color: red;">Error (Monthly Data): {monthly_error}</p>' if monthly_error else ''}
            {f'<p style="color: red;">Error (Year-Month Data): {yearly_monthly_error}</p>' if yearly_monthly_error else ''}
            {f'<p>No monthly data available for ticker {ticker}</p>' if not monthly_error and not monthly_data else ''}
            {f'<p>No year-month data available for ticker {ticker}</p>' if not yearly_monthly_error and not yearly_monthly_data else ''}

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

    # Add Yearly Charts
    html += f"""
        <h2>Yearly Analysis for {ticker or ''}</h2>
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
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        let sortStates = {{
            monthly: {{ col: 'month', dir: 'asc' }},
            yearly: {{ col: 'year', dir: 'asc' }}
        }};

        function sortTable(col, tableType) {{
            const current = sortStates[tableType];
            const newDir = current.col === col && current.dir === 'asc' ? 'desc' : 'asc';
            sortStates[tableType] = {{ col: col, dir: newDir }};

            let url = `/seasonality/per-ticker?ticker={ticker or ''}`;
            if (tableType === 'monthly') {{
                url += `&sort_col=${{col}}&sort_dir=${{newDir}}&table=monthly`;
            }} else {{
                url += `&sort_col=${{col}}&sort_dir=${{newDir}}&table=yearly`;
            }}
            window.location.href = url;
        }}

        const urlParams = new URLSearchParams(window.location.search);
        const sortCol = urlParams.get('sort_col');
        const sortDir = urlParams.get('sort_dir');
        const tableType = urlParams.get('table');
        if (sortCol && sortDir && tableType) {{
            sortStates[tableType].col = sortCol;
            sortStates[tableType].dir = sortDir;
        }}

        // Chart.js Data
        const commonYears = {json.dumps(common_years)};
        const performanceValuesFiltered = {json.dumps(performance_values_filtered)};
        const priceValuesFiltered = {json.dumps(price_values_filtered)};
        const performanceColors = performanceValuesFiltered.map(val => val >= 0 ? 'rgba(75, 192, 192, 0.7)' : 'rgba(255, 99, 132, 0.7)');
        const performanceBorderColors = performanceValuesFiltered.map(val => val >= 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)');

        // Price Action Line Chart
        const priceCtx = document.getElementById('yearlyPriceChart').getContext('2d');
        new Chart(priceCtx, {{
            type: 'line',
            data: {{
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

        // Performance Bar Chart
        const barCtx = document.getElementById('yearlyBarChart').getContext('2d');
        new Chart(barCtx, {{
            type: 'bar',
            data: {{
                labels: commonYears,
                datasets: [{
                    label: 'Yearly % Change',
                    data: performanceValuesFiltered,
                    backgroundColor: performanceColors,
                    borderColor: performanceBorderColors,
                    borderWidth: 1
                }]
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

        // Combined Chart (Price Line + Performance Bars)
        const combinedCtx = document.getElementById('combinedChart').getContext('2d');
        new Chart(combinedCtx, {{
            type: 'bar',
            data: {{
                labels: commonYears,
                datasets: [
                    {{
                        type: 'line',
                        label: 'Yearly Closing Price',
                        data: priceValuesFiltered,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        fill: true,
                        tension: 0.3,
                        pointRadius: 3,
                        yAxisID: 'y2'
                    }},
                    {{
                        type: 'bar',
                        label: 'Yearly % Change',
                        data: performanceValuesFiltered,
                        backgroundColor: performanceColors,
                        borderColor: performanceBorder
