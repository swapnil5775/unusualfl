from flask import Flask, render_template_string
import requests
import json

app = Flask(__name__)

# API configuration (hardcoded for testing)
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"
API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"

def get_option_flow():
    headers = {"Authorization": f"Bearer {APIKEY}"}
    params = {"limit": 100}
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        # Return raw text and attempt to parse JSON
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
        data = get_option_flow()
        if "error" in data:
            html = f"""
            <h1>Unusual Whales Option Flow Alerts</h1>
            <p>{data['error']}</p>
            """
        else:
            # Debug: Show raw response
            raw_response = data["text"]
            parsed_data = data["json"]
            # Check if parsed_data is a list or dict we can filter
            if isinstance(parsed_data, (list, dict)):
                if isinstance(parsed_data, dict):
                    # If it's a dict, see if it contains a list of trades
                    trades = parsed_data.get("trades", parsed_data.get("data", []))
                else:
                    trades = parsed_data
                filtered_trades = [trade for trade in trades if trade.get("size") == 1001]
                if filtered_trades:
                    table_html = "<table border='1'><tr><th>Trade Details</th></tr>"
                    for trade in filtered_trades:
                        table_html += f"<tr><td>{trade}</td></tr>"
                    table_html += "</table>"
                    html = f"""
                    <h1>Unusual Whales Option Flow Alerts</h1>
                    <p>Found {len(filtered_trades)} trades with size = 1001:</p>
                    {table_html}
                    <p>Raw Response (for debugging): {raw_response}</p>
                    """
                else:
                    html = f"""
                    <h1>Unusual Whales Option Flow Alerts</h1>
                    <p>No trades with size = 1001 found in the latest data.</p>
                    <p>Raw Response (for debugging): {raw_response}</p>
                    """
            else:
                html = f"""
                <h1>Unusual Whales Option Flow Alerts</h1>
                <p>Unexpected data format: {type(parsed_data).__name__}</p>
                <p>Raw Response: {raw_response}</p>
                """
        return render_template_string(html)
    except Exception as e:
        return render_template_string("""
        <h1>Unusual Whales Option Flow Alerts</h1>
        <p>Internal Server Error: {{ error }}</p>
        """, error=str(e))

if __name__ == "__main__":
    app.run()
