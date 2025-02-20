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
            # Extract the 'data' list from the response
            parsed_data = data["json"]
            trades = parsed_data.get("data", []) if isinstance(parsed_data, dict) else parsed_data
            # Filter trades with total_size = 1001
            filtered_trades = [trade for trade in trades if trade.get("total_size") == 1001]
            if filtered_trades:
                # Build a cleaner table with specific fields
                table_html = """
                <table border='1'>
                    <tr>
                        <th>Ticker</th>
                        <th>Type</th>
                        <th>Strike</th>
                        <th>Price</th>
                        <th>Total Size</th>
                        <th>Expiry</th>
                    </tr>
                """
                for trade in filtered_trades:
                    table_html += f"""
                    <tr>
                        <td>{trade.get('ticker', 'N/A')}</td>
                        <td>{trade.get('type', 'N/A')}</td>
                        <td>{trade.get('strike', 'N/A')}</td>
                        <td>{trade.get('price', 'N/A')}</td>
                        <td>{trade.get('total_size', 'N/A')}</td>
                        <td>{trade.get('expiry', 'N/A')}</td>
                    </tr>
                    """
                table_html += "</table>"
                html = f"""
                <h1>Unusual Whales Option Flow Alerts</h1>
                <p>Found {len(filtered_trades)} trades with size = 1001:</p>
                {table_html}
                <p>Raw Response (for debugging): {data['text']}</p>
                """
            else:
                html = f"""
                <h1>Unusual Whales Option Flow Alerts</h1>
                <p>No trades with size = 1001 found in the latest data.</p>
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
