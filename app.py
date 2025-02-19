from flask import Flask, render_template_string
import requests
import os

app = Flask(__name__)

# API configuration
APIKEY = os.getenv("APIKEY")
API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"

def get_option_flow():
    headers = {"Authorization": f"Bearer {APIKEY}"}
    params = {"limit": 100}
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

@app.route('/')
def display_trades():
    if not APIKEY:
        return "Error: APIKEY not set. Please configure it in Vercel."
    data = get_option_flow()
    if data:
        filtered_trades = [trade for trade in data if trade.get("size") == 1001]
        if filtered_trades:
            # Simple HTML table
            table_html = "<table border='1'><tr><th>Trade Details</th></tr>"
            for trade in filtered_trades:
                table_html += f"<tr><td>{trade}</td></tr>"
            table_html += "</table>"
            html = f"""
            <h1>Unusual Whales Option Flow Alerts</h1>
            <p>Found {len(filtered_trades)} trades with size = 1001:</p>
            {table_html}
            """
        else:
            html = "<h1>Unusual Whales Option Flow Alerts</h1><p>No trades with size = 1001 found.</p>"
    else:
        html = "<h1>Unusual Whales Option Flow Alerts</h1><p>Failed to retrieve data from the API.</p>"
    return render_template_string(html)

if __name__ == "__main__":
    app.run()
