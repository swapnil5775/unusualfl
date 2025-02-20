import os
from flask import Flask, render_template_string, request, jsonify
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# API configuration
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"
FLOW_API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"
INST_LIST_API_URL = "https://api.unusualwhales.com/api/institutions"
INST_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/institution/{name}/holdings"
MARKET_TIDE_API_URL = "https://api.unusualwhales.com/api/v1/market-tide"

def get_api_data(url, params=None):
    headers = {"Authorization": f"Bearer {APIKEY}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        return {"error": f"{str(e)} - URL: {response.url if 'response' in locals() else url}", "raw": response.text if 'response' in locals() else ""}

MENU_BAR = """
<div style="background-color: #f8f8f8; padding: 10px;">
    <a href="/" style="margin-right: 20px;">Home</a>
    <a href="/optionflow" style="margin-right: 20px;">Option Flow</a>
    <a href="/institution/list" style="margin-right: 20px;">Institution List</a>
    <a href="/research" style="margin-right: 20px;">Research</a>
    <a href="/market-tide" style="margin-right: 20px;">Market Tide</a>
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
            <tr><th>Name</th></tr>
    """
    if "error" not in data:
        institutions = data.get("data", []) if isinstance(data, dict) else data
        for inst in institutions:
            name = inst if isinstance(inst, str) else inst.get('name', 'N/A')
            html += f"<tr><td><a href='#' onclick='showHoldings(\"{name}\")'>{name}</a></td></tr>"
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

@app.route('/optionflow', methods=['GET'])
def option_flow():
    date = request.args.get('date')  # No default date, only filter if provided
    sort_col = request.args.get('sort_col', 'start_time')
    sort_dir = request.args.get('sort_dir', 'desc')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    params = {"limit": limit, "offset": offset}
    # Only add date parameters if a date is explicitly provided
    if date:
        try:
            start_time = int(datetime.strptime(date, '%Y-%m-%d').timestamp() * 1000)
            end_time = start_time + (24 * 60 * 60 * 1000) - 1  # End of day
            params["start_time"] = start_time
            params["end_time"] = end_time
        except ValueError:
            pass  # Ignore invalid dates, fetch all trades

    data = get_api_data(FLOW_API_URL, params=params)
    trades = data.get("data", []) if "error" not in data else []

    # Sort trades
    sort_key = {'ticker': 'ticker', 'type': 'type', 'strike': 'strike', 'price': 'price',
                'total_size': 'total_size', 'expiry': 'expiry', 'start_time': 'start_time',
                'total_premium': 'total_premium', 'alert_rule': 'alert_rule'}
    def get_sort_value(trade, key):
        val = trade.get(sort_key[key], '')
        return float(val) if isinstance(val, (int, float)) else str(val).lower()
    trades.sort(key=lambda x: get_sort_value(x, sort_col), reverse=(sort_dir == 'desc'))

    # Get total count (assuming API provides this, otherwise estimate)
    total_trades = data.get("total_count", len(trades) + (1 if len(trades) == limit else 0))

    html = f"""
    <h1>Option Flow Alerts</h1>
    {MENU_BAR}
    <div>
        <input type="date" id="dateFilter" onchange="updateFilters()" value="{date or ''}">
        <button onclick="collectPastData()">Collect Last 15 Days</button>
        <div id="progress" style="display:none">
            <progress id="progressBar" value="0" max="15"></progress>
            <span id="progressMsg"></span>
        </div>
    </div>
    <table border='1' id='flowTable'>
        <tr>
            <th><a href="#" onclick="sortTable('ticker')">Ticker</a></th>
            <th><a href="#" onclick="sortTable('type')">Type</a></th>
            <th><a href="#" onclick="sortTable('strike')">Strike</a></th>
            <th><a href="#" onclick="sortTable('price')">Price</a></th>
            <th><a href="#" onclick="sortTable('total_size')">Total Size</a></th>
            <th><a href="#" onclick="sortTable('expiry')">Expiry</a></th>
            <th><a href="#" onclick="sortTable('start_time')">Start Time</a></th>
            <th><a href="#" onclick="sortTable('total_premium')">Total Premium</a></th>
            <th><a href="#" onclick="sortTable('alert_rule')">Alert Rule</a></th>
        </tr>
    """
    for trade in trades:
        start_time = datetime.fromtimestamp(trade.get('start_time', 0)/1000).strftime('%Y-%m-%d %H:%M:%S')
        html += f"""
        <tr>
            <td>{trade.get('ticker', 'N/A')}</td><td>{trade.get('type', 'N/A')}</td>
            <td>{trade.get('strike', 'N/A')}</td><td>{trade.get('price', 'N/A')}</td>
            <td>{trade.get('total_size', 'N/A')}</td><td>{trade.get('expiry', 'N/A')}</td>
            <td>{start_time}</td><td>{trade.get('total_premium', 'N/A')}</td>
            <td>{trade.get('alert_rule', 'N/A')}</td>
        </tr>
        """
    html += f"""
    </table>
    <div>
        <p>Showing {len(trades)} of {total_trades} trades</p>
    """
    if offset > 0:
        prev_url = f"/optionflow?sort_col={sort_col}&sort_dir={sort_dir}&limit={limit}&offset={max(0, offset-limit)}"
        if date:
            prev_url += f"&date={date}"
        html += f"<a href='{prev_url}'>Previous</a>&nbsp;"
    if offset + limit < total_trades:
        next_url = f"/optionflow?sort_col={sort_col}&sort_dir={sort_dir}&limit={limit}&offset={offset+limit}"
        if date:
            next_url += f"&date={date}"
        html += f"<a href='{next_url}'>Next</a>"
    html += """
    </div>
    <script>
        let currentSort = {col: '{sort_col}', dir: '{sort_dir}'};
        function updateFilters() {
            const date = document.getElementById('dateFilter').value;
            let url = `/optionflow?sort_col=${currentSort.col}&sort_dir=${currentSort.dir}`;
            if (date) url += `&date=${date}`;
            window.location.href = url;
        }
        function sortTable(col) {
            const newDir = currentSort.col === col && currentSort.dir === 'desc' ? 'asc' : 'desc';
            currentSort = {col: col, dir: newDir};
            updateFilters();
        }
        function collectPastData() {
            document.getElementById('progress').style.display = 'block';
            fetch('/collect_past_data', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    document.getElementById('progressBar').value = 15;
                    document.getElementById('progressMsg').textContent = 'Processed: ' + data.trades + ' trades';
                    setTimeout(() => document.getElementById('progress').style.display = 'none', 2000);
                })
                .catch(error => {
                    document.getElementById('progressMsg').textContent = 'Error collecting data';
                    console.error('Error:', error);
                });
        }
    </script>
    """
    return render_template_string(html)

@app.route('/collect_past_data', methods=['POST'])
def collect_past_data():
    date = datetime.utcnow().strftime('%Y-%m-%d')
    params = {"limit": 500, "offset": 0}
    data = get_api_data(FLOW_API_URL, params=params)
    trades = data.get("data", []) if "error" not in data else []
    return jsonify({"trades": len(trades)})

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
