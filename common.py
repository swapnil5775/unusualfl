import os
from flask import Flask, render_template_string, request, jsonify
import requests
import json
import yfinance as yf
from datetime import datetime, timedelta
import random
import ssl
# API configuration
APIKEY = "bd0cf36c-5072-4b1e-87ee-7e278b8a02e5"  # This is a mock API key
APIKEY = os.environ.get('UNUSUALWHALES_API_KEY', 'bd0cf36c-5072-4b1e-87ee-7e278b8a02e5')
INST_LIST_API_URL = "https://api.unusualwhales.com/api/institutions"
INST_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/institution/{name}/holdings"
SEASONALITY_API_URL = "https://api.unusualwhales.com/api/seasonality/{ticker}/monthly"
SEASONALITY_MARKET_API_URL = "https://api.unusualwhales.com/api/seasonality/market"
ETF_EXPOSURE_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/exposure"
ETF_HOLDINGS_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/holdings"
ETF_INOUTFLOW_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/in-outflow"
ETF_INFO_API_URL = "https://api.unusualwhales.com/api/etfs/{ticker}/info"
MARKET_TIDE_API_URL = "https://api.unusualwhales.com/api/market/market-tide"
INSIDER_TRADES_API_URL = "https://api.unusualwhales.com/api/market/insider-buy-sells"
CONGRESS_TRADES_API_URL = "https://api.unusualwhales.com/api/congress/congress-trader"

# Mock data for testing
MOCK_INSTITUTIONS = [
    "BlackRock", "Vanguard", "State Street", "Fidelity", "JPMorgan",
    "Goldman Sachs", "Morgan Stanley", "PIMCO", "Wellington Management",
    "Capital Group"
]

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')


MOCK_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "WMT"]

def generate_mock_holdings():
    holdings = []
    for ticker in random.sample(MOCK_TICKERS, random.randint(3, 8)):
        holdings.append({
            "ticker": ticker,
            "units": random.randint(10000, 1000000),
            "value": random.randint(1000000, 100000000)
        })
    return holdings

def generate_mock_seasonality(ticker):
    months = ["January", "February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    data = []
    for month in months:
        data.append({
            "month": month,
            "avg_change": random.uniform(-5, 5),
            "max_change": random.uniform(5, 15),
            "median_change": random.uniform(-3, 3),
            "min_change": random.uniform(-15, -5),
            "positive_closes": random.randint(5, 20),
            "positive_months_perc": random.uniform(0.3, 0.7),
            "years": random.randint(5, 15)
        })
    return data

def get_api_data(url, params=None, verify_ssl=False):
    # For testing, return mock data instead of making actual API calls
    if "institutions" in url:
        return {"data": MOCK_INSTITUTIONS}
    elif "holdings" in url:
        return {"data": generate_mock_holdings()}
    elif "seasonality" in url and "{ticker}" in url:
        ticker = url.split("{ticker}")[1].split("/")[0]
        return {"data": generate_mock_seasonality(ticker)}
    elif "info" in url:
        # Extract ticker safely
        try:
            ticker = url.split("{ticker}")[1].split("/")[0]
        except IndexError:
            ticker = "SPY"  # Default ticker if extraction fails
            
        return {
            "data": {
                "name": ticker,
                "description": f"Mock ETF description for {ticker}",
                "asset_class": "Equity",
                "total_assets": random.randint(1000000, 1000000000),
                "volume": random.randint(100000, 1000000),
                "yield": random.uniform(1, 5),
                "expense_ratio": random.uniform(0.03, 0.5)
            }
        }
    elif "exposure" in url or "etfs" in url:
        # Return mock ETF data for any ETF-related endpoint
        return {
            "data": {
                "Technology": random.uniform(20, 40),
                "Healthcare": random.uniform(10, 20),
                "Financials": random.uniform(10, 20),
                "Consumer Discretionary": random.uniform(5, 15),
                "Communication Services": random.uniform(5, 15),
                "Industrials": random.uniform(5, 10),
                "Consumer Staples": random.uniform(2, 8),
                "Energy": random.uniform(2, 8),
                "Materials": random.uniform(2, 5),
                "Utilities": random.uniform(1, 5),
                "Real Estate": random.uniform(1, 5)
            }
        }
    
    try:
        headers = {"Authorization": f"Bearer {APIKEY}"}
        response = requests.get(url, headers=headers, params=params, verify=verify_ssl)
        response.raise_for_status()

        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        return response.json()
    except Exception as e:
        print(f"API Error: {str(e)}")
        return {"error": str(e)}

def get_live_stock_price(ticker):
    try:
        # First try yfinance
        # Create a custom SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Set the SSL context for yfinance
        old_get = requests.get
        def new_get(*args, **kwargs):
            kwargs['verify'] = False
            return old_get(*args, **kwargs)
        requests.get = new_get
        
        stock = yf.Ticker(ticker)
        price = stock.info.get('regularMarketPrice')
        
        # Restore original get function
        requests.get = old_get
        
        if price:
            return price
        
        # If yfinance fails, return mock data
        return round(random.uniform(10, 1000), 2)
    except Exception as e:
        print(f"Stock Price Error: {str(e)}")
        return round(random.uniform(10, 1000), 2)

MENU_BAR = """

<div class="menu-bar">
    <div class="nav-links">
        <a href="/" class="nav-link"><i class="fas fa-home"></i> Home</a>
        <a href="/institution-list" class="nav-link"><i class="fas fa-building"></i> Institutions</a>
        <a href="/research" class="nav-link"><i class="fas fa-search"></i> Stock Research</a>
        <a href="/seasonality" class="nav-link"><i class="fas fa-calendar-alt"></i> Seasonality</a>
        <a href="/etf-research" class="nav-link"><i class="fas fa-chart-pie"></i> ETF Research</a>
        <a href="/market-tide" class="nav-link"><i class="fas fa-water"></i> Market Tide</a>
        <a href="/market-spike" class="nav-link"><i class="fas fa-bolt"></i> Market Spike</a>
        <a href="/flow-per-strike" class="nav-link"><i class="fas fa-exchange-alt"></i> Flow Per Strike</a>
        <a href="/insider-trades" class="nav-link"><i class="fas fa-user-secret"></i> Insider Trades</a>
        <a href="/congress-trades" class="nav-link"><i class="fas fa-landmark"></i> Congress Trades</a>
        <a href="/premium-options" class="nav-link"><i class="fas fa-dollar-sign"></i> Premium Options</a>
        <a href="/most-active-stocks" class="nav-link"><i class="fas fa-fire"></i> Most Active</a>
        <a href="/market-movers" class="nav-link"><i class="fas fa-sort-amount-up"></i> Market Movers</a>
    </div>
    <div class="theme-toggle">
        <button id="theme-toggle-btn" class="btn btn-sm" onclick="toggleTheme()">
            <i class="fas fa-moon dark-icon"></i>
            <i class="fas fa-sun light-icon"></i>
        </button>
    </div>

</div>
<style>
    .menu-bar {
        background: var(--background);
        padding: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid var(--border);
        margin-bottom: 2rem;
    }

    .nav-links {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .nav-link {
        color: var(--text);
        text-decoration: none;
        padding: 0.5rem 0.75rem;
        border-radius: 4px;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
    }

    .nav-link:hover {
        background: var(--hover);
        color: var(--primary-color);
    }

    .theme-toggle {
        margin-left: 1rem;
    }

    .theme-toggle button {
        background: none;
        border: none;
        color: var(--text);
        cursor: pointer;
        padding: 0.5rem;
        font-size: 1rem;
        transition: color 0.2s ease;
    }

    .theme-toggle button:hover {
        color: var(--primary-color);
    }

    @media (max-width: 768px) {
        .menu-bar {
            flex-direction: column;
            gap: 1rem;
            padding: 0.75rem;
        }

        .nav-links {
            width: 100%;
            justify-content: center;
        }
    }
</style>
"""
