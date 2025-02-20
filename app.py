from flask import Flask, render_template_string, request
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# API configuration (hardcoded for testing)
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"
API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"

def get_option_flow():
    headers = {"Authorization": f"Bearer {APIKEY}"}
    params = {"limit": 1000}  # Max limit to get more data
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        raw_text = response.text
        try:
            parsed_data = response.json()
            return {"text": raw_text, "json": parsed_data}
        except json.JSONDecodeError as e:
            return {"error": f"JSON Parse Error: {str(e)} - Raw Response: {raw_text}"}
    except requests.RequestException as e:
        return {"error": f"API Error: {str(e)} - Status Code: {e.response.status_code if e.response else 'No response'}"}

@app.route('/')
def display_trades():
    try:
        # Get days from query parameter (default to 1 day)
        days = int(request.args.get('days', 1))
        if days not in [1, 2, 3]:
            days = 1  # Fallback to 1 day if invalid

        # Calculate timestamp for filtering (milliseconds)
        cutoff_time = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)

        data = get_option_flow()
        if "error" in data:
            html = f"""
            <h1>Unusual Whales Option Flow Alerts</h1>
            <p>{data['error']}</p>
            """
        else:
            # Extract trades
            parsed_data = data["json"]
            trades = parsed_data.get("data", []) if isinstance(parsed_data, dict) else parsed_data
            total_trades = len(trades)

            # Filter trades by time (start_time > cutoff) and size = 1001
            filtered_trades = [
                trade for trade in trades
                if trade.get("total_size") == 1001 and trade.get("start_time", 0) >= cutoff_time
            ]

            # GUI buttons
            button_html = """
            <form method="GET">
                <button type="submit" name="days" value="1">1D</button>
                <button type="submit" name="days" value="2">2D</button>
                <button type="submit" name="days" value="3">3D</button>
            </form>
            """

            if filtered_trades:
                # Build table with additional columns: total_premium and alert_rule
                table_html = """
                <table border='1'>
                    <tr>
                        <th>Ticker</th>
                        <th>Type</th>
                        <th>Strike</th>
                        <th>Price</th>
                        <th>Total Size</th>
                        <th>Expiry</th>
                        <th>Start Time</th>
                        <th>Total Premium</th>
                        <th>Alert Rule</th>
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
                <p>Raw Response (for debugging): {data['text']}</p>
                """
            else:
                html = f"""
                <h1>Unusual Whales Option Flow Alerts</h1>
                {button_html}
                <p>Total trades pulled: {total_trades}</p>
                <p>No trades with size = 1001 found in the last {days} day(s).</p>
                <p>Raw Response (for debugging): {data['text']}</p>
                """
        return render_template_string(html)
    except Exception as e:
        return render_template_string("""
        <h1>Unusual Whales Option Flow Alerts</h1>
        <p>Internal Server Error: {{ error }}</p>
        """, error=str(e))

if __name__ == "__main__":
    app.run()
