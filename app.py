import streamlit as st
import requests
import os

# API configuration
API_KEY = os.getenv("APIKEY")
API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"

# Function to fetch data
def get_option_flow():
    headers = {"Authorization": f"Bearer {APIKEY}"}
    params = {"limit": 100}
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

# Streamlit GUI
st.title("Unusual Whales Option Flow Alerts")
st.write("Displaying trades with size = 1001")

if not API_KEY:
    st.error("API_KEY not set. Please configure it in Vercel.")
else:
    data = get_option_flow()
    if data:
        filtered_trades = [trade for trade in data if trade.get("size") == 1001]
        if filtered_trades:
            st.write(f"Found {len(filtered_trades)} trades with size = 1001:")
            # Display as a simple table without pandas
            st.table(filtered_trades)
        else:
            st.write("No trades with size = 1001 found in the latest data.")
    else:
        st.write("Failed to retrieve data from the API.")
