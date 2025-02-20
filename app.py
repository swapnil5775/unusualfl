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
INST_LIST_API_URL = "https://api.unusualwhales.com/api/institutions"
INST_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/institution/{name}/holdings"

# Database connection for Neon Postgres
def get_db_connection():
    try:
        conn = psycopg2.connect(os.environ["POSTGRES_URL"], cursor_factory=RealDictCursor)
        return conn
    except KeyError:
        raise Exception("POSTGRES_URL environment variable not set. Please configure it in Vercel with your Neon connection string for 'option_flow_past_15'.")
    except psycopg2.Error as e:
        raise Exception(f"Database connection failed for 'option_flow_past_15': {str(e)}")

# Initialize database table (keeping for consistency, though not used now)
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
        print(f"Failed to initialize database 'option_flow_past_15': {str(e)}")

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
    <a href="/institution/list" style="margin-right: 20px;">Institution List</a>
    <a href="/research" style="margin-right: 20px;">Research</a>
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
