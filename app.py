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

def get_api_data(url, params=None):
    headers = {"Authorization": f"Bearer {APIKEY}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        return {"error": str(e)}

# Menu bar template
MENU_BAR = """
<div style="background-color: #f8f8f8; padding: 10px;">
    <a href="/" style="margin-right: 20px;">Home</a>
    <a href="/optionflow" style="margin-right: 20px;">Option Flow</a>
    <a href="/institution/list" style="margin-right: 20px;">Institution List</a>
    <a href="/research" style="margin-right: 20px;">Research</a>
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
@app.route('/optionflow')
def option_flow():
    try:
        days = int(request.args.get('days', 1))
        if days not in [1, 2, 3]:
            days = 1
        cutoff_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)

        data = get_api_data(FLOW_API_URL, params={"limit": 1000})
        if "error" in data:
            html = f"<h1>Option Flow Alerts</h1>{MENU_BAR}<p>{data['error']}</p>"
        else:
            trades = data.get("data", [])
            total_trades = len(trades)
            filtered_trades = [
                trade for trade in trades
                if trade.get("total_size") == 1001 and trade.get("start_time", 0) >= cutoff_time
            ]

            button_html = """
            <form method="GET" style="margin-top: 10px;">
                <button type="submit" name="days" value="1">1D</button>
                <button type="submit" name="days" value="2">2D</button>
                <button type="submit" name="days" value="3">3D</button>
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
                {button_html}
                <p>Total trades pulled: {total_trades}</p>
                <p>Found {len(filtered_trades)} trades with size = 1001 in the last {days} day(s):</p>
                {table_html}
                """
            else:
                html = f"""
                <h1>Option Flow Alerts</h1>
                {MENU_BAR}
                {button_html}
                <p>Total trades pulled: {total_trades}</p>
                <p>No trades with size = 1001 found in the last {days} day(s).</p>
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
    # Fetch institution list
    inst_data = get_api_data(INST_LIST_API_URL)
    if "error" in inst_data:
        html = f"""
        <h1>Research</h1>
        {MENU_BAR}
        <p>Error fetching institution list: {inst_data['error']}</p>
        """
        return render_template_string(html)

    institutions = inst_data.get("data", [])[:5]  # Limit to 5 for demo; remove slice for full list
    holdings_master = {}

    # Aggregate holdings from all institutions
    for inst in institutions:
        name = inst if isinstance(inst, str) else inst.get('name', 'N/A')
        holdings_data = get_api_data(INST_HOLDINGS_API_URL.format(name=name))
        if "error" not in holdings_data:
            holdings = holdings_data.get("data", [])
            for holding in holdings:
                ticker = holding.get("ticker")
                units = float(holding.get("units", 0) or 0)
                if ticker:
                    if ticker not in holdings_master:
                        holdings_master[ticker] = {}
                    holdings_master[ticker][name] = units

    # Master table
    table_html = """
    <table border='1' id="masterTable">
        <tr><th>Ticker</th><th>Total Units</th></tr>
    """
    ticker_options = ""
    for ticker, inst_holdings in holdings_master.items():
        total_units = sum(inst_holdings.values())
        table_html += f"<tr><td>{ticker}</td><td>{total_units}</td></tr>"
        ticker_options += f"<option value='{ticker}'>{ticker}</option>"
    table_html += "</table>"

    # Chart.js setup
    chart_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <select id="tickerSelect" onchange="updateChart()">
        <option value="">Select a Ticker</option>
        {ticker_options}
    </select>
    <canvas id="holdingsChart" width="400" height="200"></canvas>
    <script>
        const holdingsData = {json.dumps(holdings_master)};
        let chart;

        function updateChart() {{
            const ticker = document.getElementById('tickerSelect').value;
            if (!ticker) return;

            const ctx = document.getElementById('holdingsChart').getContext('2d');
            const data = holdingsData[ticker] || {{}};
            const labels = Object.keys(data);
            const values = Object.values(data);

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
                    scales: {{
                        y: {{ beginAtZero: true }}
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
    <h2>Holdings by Institution</h2>
    {chart_html}
    """
    return render_template_string(html)

if __name__ == "__main__":
    app.run()
