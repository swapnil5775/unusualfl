from flask import Flask, render_template_string, request
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# API configuration (hardcoded for testing)
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"
FLOW_API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"
INST_LIST_API_URL = "https://api.unusualwhales.com/api/institutions"
INST_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/institution/{name}/holdings"
MARKET_TIDE_API_URL = "https://api.unusualwhales.com/api/v1/market-tide"
SEASON_PERF_MONTHLY_API_URL = "https://api.unusualwhales.com/api/seasonality/{month}/performers"
SEASON_STOCK_PERF_API_URL = "https://api.unusualwhales.com/api/seasonality/{ticker}/monthly"
SEASON_MARKET_API_URL = "https://api.unusualwhales.com/api/seasonality/market"

def get_api_data(url, params=None):
    headers = {"Authorization": f"Bearer {APIKEY}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        return {"error": f"{str(e)} - URL: {response.url if 'response' in locals() else url}"}

# Menu bar template
MENU_BAR = """
<div style="background-color: #f8f8f8; padding: 10px;">
    <a href="/" style="margin-right: 20px;">Home</a>
    <a href="/optionflow" style="margin-right: 20px;">Option Flow</a>
    <a href="/institution/list" style="margin-right: 20px;">Institution List</a>
    <a href="/research" style="margin-right: 20px;">Research</a>
    <a href="/market-tide" style="margin-right: 20px;">Market Tide</a>
    <a href="/seasonality" style="margin-right: 20px;">Seasonality</a>
</div>
"""

# Main Page
@app.route('/')
def home():
    html = f"""
    <h1>Unusual Whales Dashboard</h1>
    {MENU_BAR}
    <p>Welcome to the Unusual Whales Dashboard. Select a page from the menu above.</p>
    """
    return render_template_string(html)

# Option Flow Page
@app.route('/optionflow', methods=['GET'])
def option_flow():
    try:
        days = int(request.args.get('days', 1))
        if days not in [1, 2, 3, 7]:
            days = 1
        ticker = request.args.get('ticker', '').strip()
        limit = int(request.args.get('limit', 100))
        if limit not in [100, 500]:
            limit = 100
        offset = int(request.args.get('offset', 0))

        cutoff_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
        params = {"limit": limit, "offset": offset}
        data = get_api_data(FLOW_API_URL, params=params)

        if "error" in data:
            html = f"<h1>Option Flow Alerts</h1>{MENU_BAR}<p>{data['error']}</p>"
        else:
            trades = data.get("data", [])
            total_trades = len(trades)

            if ticker:
                trades = [trade for trade in trades if trade.get("ticker", "").lower() == ticker.lower()]
            filtered_trades = [trade for trade in trades if trade.get("start_time", 0) >= cutoff_time]

            button_html = f"""
            <form method="GET" style="margin-top: 10px; text-align: center;">
                <button type="submit" name="days" value="1">1D</button>
                <button type="submit" name="days" value="2">2D</button>
                <button type="submit" name="days" value="3">3D</button>
                <button type="submit" name="days" value="7">7D</button>
                <input type="hidden" name="limit" value="{limit}">
                <input type="hidden" name="offset" value="{offset}">
                <input type="hidden" name="ticker" value="{ticker}">
            </form>
            <form method="GET" style="margin-top: 10px; text-align: center;">
                <input type="text" name="ticker" value="{ticker}" placeholder="Filter by Ticker">
                <button type="submit">Filter</button>
                <input type="hidden" name="days" value="{days}">
                <input type="hidden" name="limit" value="{limit}">
                <input type="hidden" name="offset" value="0">
            </form>
            """

            next_offset = offset + limit
            pagination_html = f"""
            <div style="text-align: center; margin-top: 10px;">
                <a href="/optionflow?days={days}&ticker={ticker}&limit={limit}&offset={next_offset}">
                    <button>Next Page</button>
                </a>
            </div>
            """

            limit_html = f"""
            <form method="GET" style="margin-top: 10px; text-align: center;">
                <label>Results per page: </label>
                <select name="limit" onchange="this.form.submit()">
                    <option value="100" {'selected' if limit == 100 else ''}>100</option>
                    <option value="500" {'selected' if limit == 500 else ''}>500</option>
                </select>
                <input type="hidden" name="days" value="{days}">
                <input type="hidden" name="ticker" value="{ticker}">
                <input type="hidden" name="offset" value="0">
            </form>
            """

            if filtered_trades:
                table_html = """
                <table border='1'>
                    <tr>
                        <th>Ticker</th><th>Type</th><th>Strike</th><th>Price</th><th>Total Size</th><th>Expiry</th><th>Start Time</th><th>Total Premium</th><th>Alert Rule</th>
                    </tr>
                """
                for trade in filtered_trades:
                    start_time = datetime.fromtimestamp(trade.get("start_time", 0) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                    table_html += f"""
                    <tr>
                        <td>{trade.get('ticker', 'N/A')}</td>
                        <td>{trade.get('type', 'N/A')}</td>
                        <td>{trade.get('strike', 'N/A')}</td>
                        <td>{trade.get('price', 'N/A')}</td>
                        <td>{trade.get('total_size', 'N/A')}</td>
                        <td>{trade.get('expiry', 'N/A')}</td>
                        <td>{start_time}</td>
                        <td>{trade.get('total_premium', 'N/A')}</td>
                        <td>{trade.get('alert_rule', 'N/A')}</td>
                    </tr>
                    """
                table_html += "</table>"
                html = f"""
                <h1>Option Flow Alerts</h1>
                {MENU_BAR}
                {pagination_html}
                {button_html}
                <p>Showing {len(filtered_trades)} trades (filtered from {total_trades} pulled) in the last {days} day(s):</p>
                {table_html}
                {limit_html}
                """
            else:
                html = f"""
                <h1>Option Flow Alerts</h1>
                {MENU_BAR}
                {pagination_html}
                {button_html}
                <p>No trades found in the last {days} day(s) with current filters (from {total_trades} pulled).</p>
                {limit_html}
                """
        return render_template_string(html)
    except Exception as e:
        return render_template_string(f"<h1>Option Flow Alerts</h1>{MENU_BAR}<p>Internal Server Error: {e}</p>")

# Institution List Page
@app.route('/institution/list')
def institution_list():
    data = get_api_data(INST_LIST_API_URL)
    if "error" in data:
        html = f"""
        <h1>Institution List</h1>
        {MENU_BAR}
        <p>{data['error']}</p>
        """
    else:
        institutions = data.get("data", []) if isinstance(data, dict) else data
        if institutions:
            table_html = """
            <table border='1'>
                <tr><th>Name</th></tr>
            """
            for inst in institutions:
                name = inst if isinstance(inst, str) else inst.get('name', 'N/A')
                table_html += f"<tr><td>{name}</td></tr>"
            table_html += "</table>"
            html = f"""
            <h1>Institution List</h1>
            {MENU_BAR}
            {table_html}
            """
        else:
            html = f"""
            <h1>Institution List</h1>
            {MENU_BAR}
            <p>No institutions found.</p>
            """
    return render_template_string(html)

# Research Page
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

    table_html = "<table border='1' id='masterTable'><tr><th>Ticker</th><th>Total Units</th>"
    for name in inst_names:
        table_html += f"<th>{name}</th>"
    table_html += "</tr>"

    ticker_options = ""
    for ticker, inst_holdings in holdings_master.items():
        total_units = sum(inst_holdings.values())
        table_html += f"<tr><td>{ticker}</td><td>{total_units}</td>"
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

# Market Tide Page
@app.route('/market-tide', methods=['GET'])
def market_tide():
    ticker = request.args.get('ticker', 'SPY')
    date = request.args.get('date', '2023-01-01')

    params = {"ticker": ticker, "date": date}
    data = get_api_data(MARKET_TIDE_API_URL, params=params)

    form_html = f"""
    <form method="GET" style="margin-top: 10px;">
        <label>Ticker: </label><input type="text" name="ticker" value="{ticker}" placeholder="Enter ticker symbol">
        <label>Date: </label><input type="date" name="date" value="{date}" min="2022-09-28" max="{datetime.utcnow().strftime('%Y-%m-%d')}">
        <button type="submit">Go</button>
    </form>
    """

    if "error" in data:
        html = f"""
        <h1>Market Tide</h1>
        {MENU_BAR}
        {form_html}
        <p>{data['error']}</p>
        """
    else:
        tide_data = data.get("data", {})
        if not tide_data:
            html = f"""
            <h1>Market Tide</h1>
            {MENU_BAR}
            {form_html}
            <p>No data found for {ticker} on {date}.</p>
            """
        else:
            labels = list(tide_data.keys())
            values = [float(tide_data.get(key, 0) or 0) for key in labels]
            chart_data = json.dumps({"labels": labels, "values": values})

            chart_html = f"""
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <canvas id="tideChart" width="600" height="300"></canvas>
            <script>
                const tideData = {chart_data};
                const ctx = document.getElementById('tideChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: tideData.labels,
                        datasets: [{{
                            label: 'Market Tide Metrics ({ticker} on {date})',
                            data: tideData.values,
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        scales: {{
                            x: {{ title: {{ display: true, text: 'Metric' }} }},
                            y: {{ title: {{ display: true, text: 'Value' }}, beginAtZero: true }}
                        }}
                    }}
                }});
            </script>
            """

            html = f"""
            <h1>Market Tide ({ticker})</h1>
            {MENU_BAR}
            {form_html}
            {chart_html}
            """
    return render_template_string(html)

# Seasonality Main Page
@app.route('/seasonality')
def seasonality_home():
    sub_menu = """
    <div style="margin-top: 10px;">
        <a href="/seasonality/perf-monthly" style="margin-right: 20px;">Perf-Monthly</a>
        <a href="/seasonality/stock-perf-monthly" style="margin-right: 20px;">Stock Perf Monthly</a>
        <a href="/seasonality/seasonality-monthly" style="margin-right: 20px;">Seasonality Monthly</a>
    </div>
    """
    html = f"""
    <h1>Seasonality</h1>
    {MENU_BAR}
    {sub_menu}
    <p>Select a sub-page to view seasonality data.</p>
    """
    return render_template_string(html)

# Perf-Monthly Sub-Page
@app.route('/seasonality/perf-monthly', methods=['GET'])
def perf_monthly():
    month = request.args.get('month', 'january')  # Default to January
    months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']
    data = get_api_data(SEASON_PERF_MONTHLY_API_URL.format(month=month.lower()))

    sub_menu = """
    <div style="margin-top: 10px;">
        <a href="/seasonality" style="margin-right: 20px;">Seasonality Home</a>
        <a href="/seasonality/stock-perf-monthly" style="margin-right: 20px;">Stock Perf Monthly</a>
        <a href="/seasonality/seasonality-monthly" style="margin-right: 20px;">Seasonality Monthly</a>
    </div>
    """

    form_html = f"""
    <form method="GET" style="margin-top: 10px;">
        <label>Month: </label>
        <select name="month" onchange="this.form.submit()">
            {''.join(f'<option value="{m}" {"selected" if m == month.lower() else ""}>{m.capitalize()}</option>' for m in months)}
        </select>
    </form>
    """

    if "error" in data:
        html = f"""
        <h1>Perf-Monthly</h1>
        {MENU_BAR}
        {sub_menu}
        {form_html}
        <p>{data['error']}</p>
        """
    else:
        performers = data.get("data", [])
        if not performers:
            html = f"""
            <h1>Perf-Monthly</h1>
            {MENU_BAR}
            {sub_menu}
            {form_html}
            <p>No performers found for {month.capitalize()}.</p>
            """
        else:
            # Assuming performers return ticker and performance metrics
            table_html = """
            <table border='1'>
                <tr><th>Ticker</th><th>Performance</th></tr>
            """
            for perf in performers:
                table_html += f"""
                <tr>
                    <td>{perf.get('ticker', 'N/A')}</td>
                    <td>{perf.get('performance', 'N/A')}</td>
                </tr>
                """
            table_html += "</table>"
            html = f"""
            <h1>Perf-Monthly ({month.capitalize()})</h1>
            {MENU_BAR}
            {sub_menu}
            {form_html}
            {table_html}
            """
    return render_template_string(html)

# Stock Perf Monthly Sub-Page
@app.route('/seasonality/stock-perf-monthly', methods=['GET'])
def stock_perf_monthly():
    ticker = request.args.get('ticker', 'SPY')
    data = get_api_data(SEASON_STOCK_PERF_API_URL.format(ticker=ticker.upper()))

    sub_menu = """
    <div style="margin-top: 10px;">
        <a href="/seasonality" style="margin-right: 20px;">Seasonality Home</a>
        <a href="/seasonality/perf-monthly" style="margin-right: 20px;">Perf-Monthly</a>
        <a href="/seasonality/seasonality-monthly" style="margin-right: 20px;">Seasonality Monthly</a>
    </div>
    """

    form_html = f"""
    <form method="GET" style="margin-top: 10px;">
        <label>Ticker: </label><input type="text" name="ticker" value="{ticker}" placeholder="Enter ticker symbol">
        <button type="submit">Go</button>
    </form>
    """

    if "error" in data:
        html = f"""
        <h1>Stock Perf Monthly</h1>
        {MENU_BAR}
        {sub_menu}
        {form_html}
        <p>{data['error']}</p>
        """
    else:
        monthly_data = data.get("data", [])
        if not monthly_data:
            html = f"""
            <h1>Stock Perf Monthly</h1>
            {MENU_BAR}
            {sub_menu}
            {form_html}
            <p>No monthly performance data found for {ticker}.</p>
            """
        else:
            # Assuming monthly data returns month and performance
            table_html = """
            <table border='1'>
                <tr><th>Month</th><th>Performance</th></tr>
            """
            for entry in monthly_data:
                table_html += f"""
                <tr>
                    <td>{entry.get('month', 'N/A')}</td>
                    <td>{entry.get('performance', 'N/A')}</td>
                </tr>
                """
            table_html += "</table>"

            # Chart for performance over months
            chart_data = json.dumps({
                "months": [entry.get("month", "N/A") for entry in monthly_data],
                "values": [float(entry.get("performance", 0) or 0) for entry in monthly_data]
            })
            chart_html = f"""
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <canvas id="perfChart" width="600" height="300"></canvas>
            <script>
                const perfData = {chart_data};
                const ctx = document.getElementById('perfChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: perfData.months,
                        datasets: [{{
                            label: 'Performance ({ticker})',
                            data: perfData.values,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            fill: false
                        }}]
                    }},
                    options: {{
                        scales: {{
                            x: {{ title: {{ display: true, text: 'Month' }} }},
                            y: {{ title: {{ display: true, text: 'Performance' }}, beginAtZero: true }}
                        }}
                    }}
                }});
            </script>
            """

            html = f"""
            <h1>Stock Perf Monthly ({ticker})</h1>
            {MENU_BAR}
            {sub_menu}
            {form_html}
            {table_html}
            {chart_html}
            """
    return render_template_string(html)

# Seasonality Monthly Sub-Page
@app.route('/seasonality/seasonality-monthly')
def seasonality_monthly():
    data = get_api_data(SEASON_MARKET_API_URL)

    sub_menu = """
    <div style="margin-top: 10px;">
        <a href="/seasonality" style="margin-right: 20px;">Seasonality Home</a>
        <a href="/seasonality/perf-monthly" style="margin-right: 20px;">Perf-Monthly</a>
        <a href="/seasonality/stock-perf-monthly" style="margin-right: 20px;">Stock Perf Monthly</a>
    </div>
    """

    if "error" in data:
        html = f"""
        <h1>Seasonality Monthly</h1>
        {MENU_BAR}
        {sub_menu}
        <p>{data['error']}</p>
        """
    else:
        monthly_data = data.get("data", [])
        if not monthly_data:
            html = f"""
            <h1>Seasonality Monthly</h1>
            {MENU_BAR}
            {sub_menu}
            <p>No market seasonality data found.</p>
            """
        else:
            # Assuming market seasonality returns month and some metric (e.g., avg return)
            table_html = """
            <table border='1'>
                <tr><th>Month</th><th>Avg Return</th></tr>
            """
            for entry in monthly_data:
                table_html += f"""
                <tr>
                    <td>{entry.get('month', 'N/A')}</td>
                    <td>{entry.get('avg_return', 'N/A')}</td>
                </tr>
                """
            table_html += "</table>"

            chart_data = json.dumps({
                "months": [entry.get("month", "N/A") for entry in monthly_data],
                "values": [float(entry.get("avg_return", 0) or 0) for entry in monthly_data]
            })
            chart_html = f"""
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <canvas id="seasonChart" width="600" height="300"></canvas>
            <script>
                const seasonData = {chart_data};
                const ctx = document.getElementById('seasonChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: seasonData.months,
                        datasets: [{{
                            label: 'Average Market Return',
                            data: seasonData.values,
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        scales: {{
                            x: {{ title: {{ display: true, text: 'Month' }} }},
                            y: {{ title: {{ display: true, text: 'Avg Return' }}, beginAtZero: true }}
                        }}
                    }}
                }});
            </script>
            """

            html = f"""
            <h1>Seasonality Monthly</h1>
            {MENU_BAR}
            {sub_menu}
            {table_html}
            {chart_html}
            """
    return render_template_string(html)

if __name__ == "__main__":
    app.run()
