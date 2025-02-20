import os
from flask import Flask, render_template_string, request, jsonify
import requests
import json
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# API configuration
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"
FLOW_API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"
INST_LIST_API_URL = "https://api.unusualwhales.com/api/institutions"
INST_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/institution/{name}/holdings"
MARKET_TIDE_API_URL = "https://api.unusualwhales.com/api/v1/market-tide"

# Database connection with error handling
def get_db_connection():
    try:
        conn = psycopg2.connect(os.environ["POSTGRES_URL"], cursor_factory=RealDictCursor)
        return conn
    except KeyError:
        raise Exception("POSTGRES_URL environment variable not set")
    except psycopg2.Error as e:
        raise Exception(f"Database connection failed: {str(e)}")

# Initialize database table
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                ticker TEXT,
                type TEXT,
                strike REAL,
                price REAL,
                total_size INTEGER,
                expiry TEXT,
                start_time BIGINT,
                total_premium REAL,
                alert_rule TEXT,
                trade_date DATE
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to initialize database: {str(e)}")

init_db()  # Run on startup

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
    date = request.args.get('date')
    sort_col = request.args.get('sort_col', 'start_time')
    sort_dir = request.args.get('sort_dir', 'desc')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch trades from DB
        query = "SELECT * FROM trades"
        params = []
        if date:
            query += " WHERE trade_date = %s"
            params.append(date)
        query += f" ORDER BY {sort_col} {sort_dir} LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        cur.execute(query, params)
        trades = cur.fetchall()

        # Total trades
        cur.execute("SELECT COUNT(*) FROM trades" + (" WHERE trade_date = %s" if date else ""), ([date] if date else []))
        total_trades = cur.fetchone()['count']

        # Last 5 days stats
        cur.execute("""
            SELECT trade_date, COUNT(*) as trade_count, SUM(total_premium) as total_premium
            FROM trades
            WHERE trade_date >= %s
            GROUP BY trade_date
            ORDER BY trade_date DESC
            LIMIT 5
        """, [datetime.utcnow().date() - timedelta(days=4)])
        daily_stats = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        return f"Error accessing database: {str(e)}", 500

    html = f"""
    <h1>Option Flow Alerts</h1>
    {MENU_BAR}
    <div style="display: flex;">
        <div style="flex: 3;">
            <input type="date" id="dateFilter" onchange="updateFilters()" value="{date or ''}">
            <button onclick="collectPastData()">Collect Last 15 Days</button>
            <div id="progress" style="display:none">
                <progress id="progressBar" value="0" max="15"></progress>
                <span id="progressMsg"></span>
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
        start_time = datetime.fromtimestamp(trade['start_time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        html += f"""
        <tr>
            <td>{trade['ticker'] or 'N/A'}</td><td>{trade['type'] or 'N/A'}</td>
            <td>{trade['strike'] or 'N/A'}</td><td>{trade['price'] or 'N/A'}</td>
            <td>{trade['total_size'] or 'N/A'}</td><td>{trade['expiry'] or 'N/A'}</td>
            <td>{start_time}</td><td>{trade['total_premium'] or 'N/A'}</td>
            <td>{trade['alert_rule'] or 'N/A'}</td>
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
        html += f"<a href='{prev_url}'>Previous</a> "
    if offset + limit < total_trades:
        next_url = f"/optionflow?sort_col={sort_col}&sort_dir={sort_dir}&limit={limit}&offset={offset+limit}"
        if date:
            next_url += f"&date={date}"
        html += f"<a href='{next_url}'>Next</a>"
    html += """
            </div>
        </div>
        <div style="flex: 1; margin-left: 20px;">
            <h3>Last 5 Days Stats</h3>
            <table border='1'>
                <tr><th>Date</th><th>Trades</th><th>Total Premium</th></tr>
    """
    for stat in daily_stats:
        premium = stat['total_premium'] or 0
        if premium >= 2000000:
            premium_str = f"${round(premium / 1000000)}M"
        elif premium >= 1000000:
            premium_str = f"${round(premium / 1000000, 1)}M"
        elif premium >= 100000:
            premium_str = f"${round(premium / 100000)}00K"
        else:
            premium_str = f"${round(premium / 10000)}0K"
        html += f"<tr><td>{stat['trade_date']}</td><td>{stat['trade_count']}</td><td>{premium_str}</td></tr>"
    html += """
            </table>
        </div>
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
                    setTimeout(() => {
                        document.getElementById('progress').style.display = 'none';
                        window.location.reload();
                    }, 2000);
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
    all_trades = []
    limit = 500
    offset = 0
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=15)
    start_time = int(start_date.timestamp() * 1000)
    end_time = int(end_date.timestamp() * 1000)

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        while True:
            params = {"limit": limit, "offset": offset, "start_time": start_time, "end_time": end_time}
            data = get_api_data(FLOW_API_URL, params=params)
            trades = data.get("data", []) if "error" not in data else []
            if not trades:
                break
            
            for trade in trades:
                trade_date = datetime.fromtimestamp(trade.get('start_time', 0) / 1000).date()
                cur.execute("""
                    INSERT INTO trades (ticker, type, strike, price, total_size, expiry, start_time, total_premium, alert_rule, trade_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    trade.get('ticker'), trade.get('type'), trade.get('strike'), trade.get('price'),
                    trade.get('total_size'), trade.get('expiry'), trade.get('start_time'),
                    trade.get('total_premium'), trade.get('alert_rule'), trade_date
                ))
            all_trades.extend(trades)
            offset += limit
            if len(trades) < limit:
                break

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"Failed to collect data: {str(e)}"}), 500

    return jsonify({"trades": len(all_trades), "message": f"Collected and stored {len(all_trades)} trades"})

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
