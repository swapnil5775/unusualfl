from flask import Flask, render_template_string, request
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# API configuration (hardcoded for testing)
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"
FLOW_API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"
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

# Home page (Option Flow Alerts)
@app.route('/')
def display_trades():
    try:
        days = int(request.args.get('days', 1))
        if days not in [1, 2, 3]:
            days = 1
        cutoff_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)

        data = get_api_data(FLOW_API_URL, params={"limit": 1000})
        if "error" in data:
            html = f"<h1>Unusual Whales Option Flow Alerts</h1><p>{data['error']}</p>"
        else:
            parsed_data = data["json"]
            trades = parsed_data.get("data", []) if isinstance(parsed_data, dict) else parsed_data
            total_trades = len(trades)
            filtered_trades = [
                trade for trade in trades
                if trade.get("total_size") == 1001 and trade.get("start_time", 0) >= cutoff_time
            ]

            button_html = """
            <form method="GET" style="display: inline;">
                <button type="submit" name="days" value="1">1D</button>
                <button type="submit" name="days" value="2">2D</button>
                <button type="submit" name="days" value="3">3D</button>
            </form>
            <a href="/institution"><button>Institution</button></a>
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
                <h1>Unusual Whales Option Flow Alerts</h1>
                {button_html}
                <p>Total trades pulled: {total_trades}</p>
                <p>Found {len(filtered_trades)} trades with size = 1001 in the last {days} day(s):</p>
                {table_html}
                """
            else:
                html = f"""
                <h1>Unusual Whales Option Flow Alerts</h1>
                {button_html}
                <p>Total trades pulled: {total_trades}</p>
                <p>No trades with size = 1001 found in the last {days} day(s).</p>
                """
        return render_template_string(html)
    except Exception as e:
        return render_template_string("<h1>Unusual Whales Option Flow Alerts</h1><p>Internal Server Error: {{ error }}</p>", error=str(e))

# Institution main page
@app.route('/institution')
def institution_home():
    button_html = """
    <a href="/"><button>Option Flow</button></a>
    <a href="/institution/activity"><button>Recent Activity</button></a>
    <a href="/institution/holdings"><button>Holdings</button></a>
    """
    html = f"""
    <h1>Unusual Whales Institution Data</h1>
    {button_html}
    <p>Select a sub-page to view institution data.</p>
    """
    return render_template_string(html)

# Recent Activity sub-page
@app.route('/institution/activity')
def institution_activity():
    default_institution = "BlackRock"  # Default institution name
    data = get_api_data(INST_ACTIVITY_API_URL.format(name=default_institution))

    button_html = """
    <a href="/"><button>Option Flow</button></a>
    <a href="/institution"><button>Institution Home</button></a>
    <a href="/institution/holdings"><button>Holdings</button></a>
    """

    if "error" in data:
        html = f"""
        <h1>Institution Recent Activity</h1>
        {button_html}
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
            <h1>Institution Recent Activity ({default_institution})</h1>
            {button_html}
            {table_html}
            """
        else:
            html = f"""
            <h1>Institution Recent Activity ({default_institution})</h1>
            {button_html}
            <p>No recent activity found for {default_institution}.</p>
            """
    return render_template_string(html)

# Holdings sub-page with search
@app.route('/institution/holdings', methods=['GET'])
def institution_holdings():
    institution_name = request.args.get('name', 'BlackRock')  # Default to BlackRock
    data = get_api_data(INST_HOLDINGS_API_URL.format(name=institution_name))

    button_html = """
    <a href="/"><button>Option Flow</button></a>
    <a href="/institution"><button>Institution Home</button></a>
    <a href="/institution/activity"><button>Recent Activity</button></a>
    """
    search_html = f"""
    <form method="GET">
        <input type="text" name="name" value="{institution_name}" placeholder="Enter institution name">
        <button type="submit">Search</button>
    </form>
    """

    if "error" in data:
        html = f"""
        <h1>Institution Holdings ({institution_name})</h1>
        {button_html}
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
            <h1>Institution Holdings ({institution_name})</h1>
            {button_html}
            {search_html}
            {table_html}
            """
        else:
            html = f"""
            <h1>Institution Holdings ({institution_name})</h1>
            {button_html}
            {search_html}
            <p>No holdings found for {institution_name}.</p>
            """
    return render_template_string(html)

if __name__ == "__main__":
    app.run()
