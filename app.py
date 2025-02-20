from flask import Flask, render_template_string, request, jsonify
import requests
import json
from datetime import datetime, timedelta
import sqlite3
from threading import Thread

app = Flask(__name__)

# API configuration
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"
FLOW_API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"
INST_LIST_API_URL = "https://api.unusualwhales.com/api/institutions"
INST_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/institution/{name}/holdings"
MARKET_TIDE_API_URL = "https://api.unusualwhales.com/api/v1/market-tide"

# Database setup
def init_db():
    conn = sqlite3.connect('option_flow.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS option_flow
                 (id INTEGER PRIMARY KEY, ticker TEXT, type TEXT, strike REAL, price REAL,
                  total_size INTEGER, expiry TEXT, start_time INTEGER, total_premium REAL,
                  alert_rule TEXT, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

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
        function showHoldings(name) {{
            fetch(`/institution/holdings?name=${{name}}`)
                .then(response => response.json())
                .then(data => {{
                    let table = '<tr><th>Ticker</th><th>Units</th><th>Value</th></tr>';
                    data.data.forEach(holding => {{
                        table += `<tr><td>${{holding.ticker}}</td><td>${{holding.units}}</td><td>${{holding.value}}</td></tr>`;
                    }});
                    document.getElementById('holdingsTable').innerHTML = table;
                    document.getElementById('instTable').classList.add('hide');
                    document.getElementById('holdingsContainer').classList.add('show');
                }});
        }}
        function closeHoldings() {{
            document.getElementById('instTable').classList.remove('hide');
            document.getElementById('holdingsContainer').classList.remove('show');
        }}
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
    date = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    sort_col = request.args.get('sort_col', 'start_time')
    sort_dir = request.args.get('sort_dir', 'desc')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    # Check database first
    conn = sqlite3.connect('option_flow.db')
    c = conn.cursor()
    c.execute(f"SELECT * FROM option_flow WHERE date = ? ORDER BY {sort_col} {sort_dir} LIMIT ? OFFSET ?", 
              (date, limit, offset))
    trades = c.fetchall()
    conn.close()

    if not trades:
        params = {"limit": limit, "offset": offset}
        data = get_api_data(FLOW_API_URL, params=params)
        if "error" not in data:
            trades = data.get("data", [])
            # Store in database
            conn = sqlite3.connect('option_flow.db')
            c = conn.cursor()
            for trade in trades:
                c.execute("""INSERT OR REPLACE INTO option_flow 
                            (ticker, type, strike, price, total_size, expiry, start_time, total_premium, alert_rule, date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (trade.get('ticker'), trade.get('type'), trade.get('strike'), trade.get('price'),
                           trade.get('total_size'), trade.get('expiry'), trade.get('start_time'),
                           trade.get('total_premium'), trade.get('alert_rule'), date))
            conn.commit()
            conn.close()

    html = f"""
    <h1>Option Flow Alerts</h1>
    {MENU_BAR}
    <div>
        <input type="date" id="dateFilter" value="{date}" onchange="updateFilters()">
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
        start_time = datetime.fromtimestamp(trade[7]/1000).strftime('%Y-%m-%d %H:%M:%S')
        html += f"""
        <tr>
            <td>{trade[1]}</td><td>{trade[2]}</td><td>{trade[3]}</td><td>{trade[4]}</td>
            <td>{trade[5]}</td><td>{trade[6]}</td><td>{start_time}</td><td>{trade[8]}</td><td>{trade[9]}</td>
        </tr>
        """

    html += f"""
    </table>
    <script>
        let currentSort = {{col: '{sort_col}', dir: '{sort_dir}'}};
        function updateFilters() {{
            const date = document.getElementById('dateFilter').value;
            window.location.href = `/optionflow?date=${{date}}&sort_col=${{currentSort.col}}&sort_dir=${{currentSort.dir}}`;
        }}
        function sortTable(col) {{
            const newDir = currentSort.col === col && currentSort.dir === 'desc' ? 'asc' : 'desc';
            currentSort = {{col: col, dir: newDir}};
            updateFilters();
        }}
        function collectPastData() {{
            document.getElementById('progress').style.display = 'block';
            fetch('/collect_past_data', {{method: 'POST'}})
                .then(response => response.json())
                .then(data => {{
                    let progress = 0;
                    const bar = document.getElementById('progressBar');
                    const msg = document.getElementById('progressMsg');
                    const interval = setInterval(() => {{
                        if (progress >= 15) {{
                            clearInterval(interval);
                            msg.textContent = 'Collection Complete: ' + data.trades + ' trades saved';
                            setTimeout(() => document.getElementById('progress').style.display = 'none', 2000);
                        }} else {{
                            progress++;
                            bar.value = progress;
                            msg.textContent = `Processing day ${progress} of 15...`;
                        }}
                    }}, 500);
                }});
        }}
    </script>
    """
    return render_template_string(html)

@app.route('/collect_past_data', methods=['POST'])
def collect_past_data():
    def collect_data():
        total_trades = 0
        conn = sqlite3.connect('option_flow.db')
        c = conn.cursor()
        for i in range(15):
            date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            params = {"limit": 500, "offset": 0}
            data = get_api_data(FLOW_API_URL, params=params)
            if "error" not in data:
                trades = data.get("data", [])
                for trade in trades:
                    c.execute("""INSERT OR IGNORE INTO option_flow 
                                (ticker, type, strike, price, total_size, expiry, start_time, total_premium, alert_rule, date)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                              (trade.get('ticker'), trade.get('type'), trade.get('strike'), trade.get('price'),
                               trade.get('total_size'), trade.get('expiry'), trade.get('start_time'),
                               trade.get('total_premium'), trade.get('alert_rule'), date))
                total_trades += len(trades)
        conn.commit()
        conn.close()
        return total_trades

    thread = Thread(target=collect_data)
    thread.start()
    return jsonify({"status": "started"})

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

if __name__ == "__main__":
    app.run(debug=True)
