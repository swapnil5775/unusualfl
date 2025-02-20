from flask import Flask, render_template_string, request
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# API configuration (hardcoded for testing)
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"
FLOW_API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"
INST_LIST_API_URL = "https://api.unusualwhales.com/api/institutions"
INST_ACTIVITY_API_URL = "https://api.unusualwhales.com/api/institution/{name}/activity"
INST_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/institution/{name}/holdings"

def get_api_data(url, params=None):
    headers = {"Authorization": f"Bearer {APIKEY}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        raw_text = response.text
        try:
            parsed_data = response.json()
            return {"text": raw_text, "json": parsed_data}
        except json.JSONDecodeError as e:
            return {"error": f"JSON Parse Error: {str(e)} - Raw Response: {raw_text}"}
    except requests.RequestException as e:
        return {"error": f"API Error: {str(e)} - Status Code: {e.response.status_code if e.response else 'No response'}"}

# Menu bar template
MENU_BAR = """
<div style="background-color: #f8f8f8; padding: 10px;">
    <a href="/" style="margin-right: 20px;">Home</a>
    <a href="/optionflow" style="margin-right: 20px;">Option Flow</a>
    <a href="/institution/list" style="margin-right: 20px;">Institution List</a>
    <a href="/institution/activity" style="margin-right: 20px;">Recent Activity</a>
    <a href="/institution/holdings" style="margin-right: 20px;">Holdings</a>
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
            parsed_data = data["json"]
            trades = parsed_data.get("data", []) if isinstance(parsed_data, dict) else parsed_data
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
        return render_template_string(f"<h1>Option Flow Alerts</h1>{MENU_BAR}<p>Internal Server Error: {{ error }}</p>", error=str(e))

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
        parsed_data = data["json"]
        institutions = parsed_data.get("data", []) if isinstance(parsed_data, dict) else parsed_data
        if institutions:
            table_html = """
            <table border='1'>
                <tr><th>Name</th></tr>
            """
            for inst in institutions:
                name = inst if isinstance(inst, str) else inst.get('name', 'N/A')  # Adjust based on actual API response structure
                table_html += f"""
                <tr>
                    <td><a href="/institution/activity?name={name}">{name}</a></td>
                </tr>
                """
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

# Recent Activity Sub-Page
@app.route('/institution/activity')
def institution_activity():
    institution_name = request.args.get('name', 'BlackRock')  # Default to BlackRock
    data = get_api_data(INST_ACTIVITY_API_URL.format(name=institution_name))

    if "error" in data:
        html = f"""
        <h1>Recent Activity ({institution_name})</h1>
        {MENU_BAR}
        <p>{data['error']}</p>
        """
    else:
        parsed_data = data["json"]
        activities = parsed_data.get("data", []) if isinstance(parsed_data, dict) else parsed_data
        if activities:
            table_html = """
            <table border='1'>
                <tr>
                    <th>Ticker</th><th>Units</th><th>Units Change</th><th>Avg Price</th><th>Total Premium</th><th>Filing Date</th><th>Report Date</th>
                </tr>
            """
            for activity in activities:
                table_html += f"""
                <tr>
                    <td>{activity.get('ticker', 'N/A')}</td>
                    <td>{activity.get('units', 'N/A')}</td>
                    <td>{activity.get('units_change', 'N/A')}</td>
                    <td>{activity.get('avg_price', 'N/A')}</td>
                    <td>{activity.get('total_premium', 'N/A')}</td>
                    <td>{activity.get('filing_date', 'N/A')}</td>
                    <td>{activity.get('report_date', 'N/A')}</td>
                </tr>
                """
            table_html += "</table>"
            html = f"""
            <h1>Recent Activity ({institution_name})</h1>
            {MENU_BAR}
            {table_html}
            """
        else:
            html = f"""
            <h1>Recent Activity ({institution_name})</h1>
            {MENU_BAR}
            <p>No recent activity found for {institution_name}.</p>
            """
    return render_template_string(html)

# Holdings Sub-Page
@app.route('/institution/holdings', methods=['GET'])
def institution_holdings():
    institution_name = request.args.get('name', 'BlackRock')  # Default to BlackRock
    data = get_api_data(INST_HOLDINGS_API_URL.format(name=institution_name))

    search_html = f"""
    <form method="GET" style="margin-top: 10px;">
        <input type="text" name="name" value="{institution_name}" placeholder="Enter institution name">
        <button type="submit">Search</button>
    </form>
    """

    if "error" in data:
        html = f"""
        <h1>Holdings ({institution_name})</h1>
        {MENU_BAR}
        {search_html}
        <p>{data['error']}</p>
        """
    else:
        parsed_data = data["json"]
        holdings = parsed_data.get("data", []) if isinstance(parsed_data, dict) else parsed_data
        if holdings:
            table_html = """
            <table border='1'>
                <tr>
                    <th>Ticker</th><th>Units</th><th>Units Change</th><th>Avg Price</th><th>Filing Date</th><th>Report Date</th>
                </tr>
            """
            for holding in holdings:
                table_html += f"""
                <tr>
                    <td>{holding.get('ticker', 'N/A')}</td>
                    <td>{holding.get('units', 'N/A')}</td>
                    <td>{holding.get('units_change', 'N/A')}</td>
                    <td>{holding.get('avg_price', 'N/A')}</td>
                    <td>{holding.get('filing_date', 'N/A')}</td>
                    <td>{holding.get('report_date', 'N/A')}</td>
                </tr>
                """
            table_html += "</table>"
            html = f"""
            <h1>Holdings ({institution_name})</h1>
            {MENU_BAR}
            {search_html}
            {table_html}
            """
        else:
            html = f"""
            <h1>Holdings ({institution_name})</h1>
            {MENU_BAR}
            {search_html}
            <p>No holdings found for {institution_name}.</p>
            """
    return render_template_string(html)

if __name__ == "__main__":
    app.run()
