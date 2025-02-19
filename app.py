import streamlit as st
import requests
import pandas as pd
import os

API_KEY = os.getenv("API_KEY")
API_URL = "https://api.unusualwhales.com/api/option-trades/flow-alerts"

def get_option_flow():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {"limit": 100}
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

st.title("Unusual Whales Option Flow Alerts")
st.write("Displaying trades with size = 1001")

if not API_KEY:
    st.error("API_KEY not set. Please configure it in Vercel.")
else:
    data = get_option_flow()
    if data:
        filtered_trades = [trade for trade in data if trade.get("size") == 1001]
        if filtered_trades:
            df = pd.DataFrame(filtered_trades)
            st.write(f"Found {len(filtered_trades)} trades with size = 1001:")
            st.dataframe(df)
        else:
            st.write("No trades with size = 1001 found in the latest data.")
    else:
        st.write("Failed to retrieve data from the API.")
