from flask import Blueprint, render_template_string, request
from common import get_api_data, get_live_stock_price, MENU_BAR, ETF_EXPOSURE_API_URL, ETF_HOLDINGS_API_URL, ETF_INOUTFLOW_API_URL, ETF_INFO_API_URL

etf_research_bp = Blueprint('etf_research', __name__, url_prefix='/')

@etf_research_bp.route('/etf-research')
def etf_research():
    html = f"""
    <h1>ETF-Research</h1>
    {MENU_BAR}
    <p>Select a sub-page to view ETF data.</p>
    <ul>
        <li><a href="/etf-research/exposure">Exposure</a></li>
        <li><a href="/etf-research/holdings">Holdings</a></li>
        <li><a href="/etf-research/in-outflow">In-Out Flow</a></li>
    </ul>
    """
    return render_template_string(html)

@etf_research_bp.route('/etf-research/exposure', methods=['GET'])
def etf_exposure():
    ticker = request.args.get('ticker', '').upper()
    data = None
    error = None

    if ticker:
        response = get_api_data(ETF_EXPOSURE_API_URL.format(ticker=ticker))
        print(f"ETF Exposure API Response for {ticker}: {response}")  # Log the full response for debugging
        if "error" in response:
            error = response["error"]
        else:
            data = response.get("data", [])
            if not isinstance(data, list):  # Ensure data is a list
                error = f"Unexpected API response format: data is not a list, got {type(data)}"
                data = None

    # Fetch ETF Info for the info bar
    etf_info = None
    etf_info_error = None
    if ticker:
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        print(f"ETF Info API Response for {ticker}: {etf_info_response}")  # Log the full response
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", {})  # Get the dictionary under "data"

    html = f"""
    <h1>ETF-Research - Exposure</h1>
    {MENU_BAR}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {ticker}</h2>
            {'<p style="color: red;">Error fetching ETF Info: ' + etf_info_error + '</p>' if etf_info_error else ''}
            <table border='1' {'style="display: none;"' if not etf_info else ''} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info:  # Check if etf_info is not None or empty
        for key, value in etf_info.items():
            if value is not None:  # Skip None values
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>"
    html += """
            </table>
        </div>
        <div style="flex: 2; min-width: 300px;">
            <form method="GET">
                <label>Enter ETF Ticker (e.g., SPY, QQQ): </label>
                <input type="text" name="ticker" value="{ticker}" placeholder="Enter ETF ticker symbol">
                <button type="submit">Search</button>
            </form>
            <h3>Or Click a Predefined ETF:</h3>
            <div>
                <button onclick="window.location.href='/etf-research/exposure?ticker=SPY'">SPY</button>
                <button onclick="window.location.href='/etf-research/exposure?ticker=QQQ'">QQQ</button>
                <button onclick="window.location.href='/etf-research/exposure?ticker=IWM'">IWM</button>
                <button onclick="window.location.href='/etf-research/exposure?ticker=XLF'">XLF</button>
            </div>
            {'<p style="color: red;">Error: ' + error + '</p>' if error else ''}
            {'<p>No data available for ticker ' + ticker + '</p>' if not error and not data else ''}
            <table border='1' {'style="display: none;"' if not data else ''} id="exposureTable">
                <tr>
                    <th>ETF</th>
                    <th>Full Name</th>
                    <th>Last Price</th>
                    <th>Previous Price</th>
                    <th>Shares</th>
                    <th>Weight (%)</th>
                </tr>
    """
    if data:
        for item in data:
            # Add fallback values for missing keys to prevent KeyError
            etf = item.get('etf', 'N/A')
            full_name = item.get('full_name', 'N/A')
            last_price = item.get('last_price', 'N/A')
            prev_price = item.get('prev_price', 'N/A')
            shares = item.get('shares', 'N/A')
            weight = item.get('weight', 'N/A')
            html += f"""
            <tr>
                <td>{etf}</td>
                <td>{full_name}</td>
                <td>{last_price}</td>
                <td>{prev_price}</td>
                <td>{shares}</td>
                <td>{float(weight) if weight and weight != 'N/A' else 'N/A'}%</td>
            </tr>
            """
    html += """
            </table>
        </div>
    </div>
    """
    return render_template_string(html)

@etf_research_bp.route('/etf-research/holdings', methods=['GET'])
def etf_holdings():
    ticker = request.args.get('ticker', '').upper()
    data = None
    error = None

    if ticker:
        response = get_api_data(ETF_HOLDINGS_API_URL.format(ticker=ticker))
        print(f"ETF Holdings API Response for {ticker}: {response}")  # Log the full response for debugging
        if "error" in response:
            error = response["error"]
        else:
            data = response.get("data", [])
            if not isinstance(data, list):  # Ensure data is a list
                error = f"Unexpected API response format: data is not a list, got {type(data)}"
                data = None

    # Fetch ETF Info for the info bar
    etf_info = None
    etf_info_error = None
    if ticker:
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        print(f"ETF Info API Response for {ticker}: {etf_info_response}")  # Log the full response
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", {})  # Get the dictionary under "data"

    html = f"""
    <h1>ETF-Research -
