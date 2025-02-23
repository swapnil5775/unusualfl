import os
from flask import Flask, render_template_string, request, jsonify
import requests
import json
import openai as ai
import yfinance as yf  # Ensure yfinance is imported with alias 'yf'

# API configuration
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"
INST_LIST_API_URL = "https://api.unusualwhales.com/api/institutions"
INST_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/institution/{name}/holdings"
SEASONALITY_API_URL = "https://api.unusualwhales.com/api/seasonality/{ticker}/monthly"
SEASONALITY_MARKET_API_URL = "https://api.unusualwhales.com/api/seasonality/market"
ETF_EXPOSURE_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/exposure"
ETF_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/holdings"
ETF_INOUTFLOW_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/in-outflow"
ETF_INFO_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/info"

def get_api_data(url, params=None):
    headers = {"Authorization": f"Bearer {APIKEY}"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")  # Exclude sensitive headers if needed
        return response.json()
    except (requests.RequestException, json.JSONDecodeError) as e:
        print(f"Request Error - URL: {url}, Status Code: {getattr(response, 'status_code', 'N/A')}, Error: {str(e)}")
        return {"error": f"{str(e)}"}

def get_live_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        live_price = stock.info['regularMarketPrice']
        return live_price
    except Exception as e:
        return f"Error: {str(e)}"

MENU_BAR = """
<div style="background-color: #f8f8f8; padding: 10px;">
    <a href="/" style="margin-right: 20px;">Home</a>
    <a href="/institution/list" style="margin-right: 20px;">Institution List</a>
    <a href="/research" style="margin-right: 20px;">Research</a>
    <a href="/seasonality" style="margin-right: 20px;">Seasonality</a>
    <a href="/etf-research" style="margin-right: 20px;">ETF-Research</a>
</div>
"""
