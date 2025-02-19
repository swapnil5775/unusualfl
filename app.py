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
        # Return raw text and parsed JSON for debugging
        return {"text": response.text, "json": response.json()}
    except requests.RequestException as e:
        return {"error": f"API Error: {str(e)} - Status Code: {e.response.status_code if e.response else 'No response'}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON Parse Error: {str(e)} - Raw Response: {response.text}"}

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
            if isinstance(parsed_data
