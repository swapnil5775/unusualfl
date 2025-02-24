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
        print(f"ETF Exposure API Response for {ticker}: {response}")
        if "error" in response:
            error = response["error"]
        else:
            data = response.get("data", [])
            print(f"Data type for {ticker}: {type(data)}, Content: {data}")
            if not isinstance(data, list):
                error = f"API returned unexpected format: expected list, got {type(data)}"
                data = None

    etf_info = None
    etf_info_error = None
    if ticker:
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        print(f"ETF Info API Response for {ticker}: {etf_info_response}")
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", {})

    context = {
        'ticker': ticker,
        'error': error,
        'data': data,
        'etf_info': etf_info,
        'etf_info_error': etf_info_error,
        'MENU_BAR': MENU_BAR
    }

    html = """
    <h1>ETF-Research - Exposure</h1>
    {{ MENU_BAR | safe }}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {{ ticker }}</h2>
            {% if etf_info_error %}<p style="color: red;">Error fetching ETF Info: {{ etf_info_error }}</p>{% endif %}
            <table border='1' {% if not etf_info %}style="display: none;"{% endif %} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info:
        for key, value in etf_info.items():
            if value is not None:
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{{{{ etf_info['{key}'] }}}}</td></tr>"
    html += """
            </table>
        </div>
        <div style="flex: 2; min-width: 300px;">
            <form method="GET">
                <label>Enter ETF Ticker (e.g., SPY, QQQ): </label>
                <input type="text" name="ticker" value="{{ ticker }}" placeholder="Enter ETF ticker symbol">
                <button type="submit">Search</button>
            </form>
            <h3>Or Click a Predefined ETF:</h3>
            <div>
                <button onclick="window.location.href='/etf-research/exposure?ticker=SPY'">SPY</button>
                <button onclick="window.location.href='/etf-research/exposure?ticker=QQQ'">QQQ</button>
                <button onclick="window.location.href='/etf-research/exposure?ticker=IWM'">IWM</button>
                <button onclick="window.location.href='/etf-research/exposure?ticker=XLF'">XLF</button>
            </div>
            {% if error %}<p style="color: red;">Error: {{ error }}</p>{% endif %}
            {% if not error and not data %}<p>No data available for ticker {{ ticker }}</p>{% endif %}
            <table border='1' {% if not data %}style="display: none;"{% endif %} id="exposureTable">
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
    return render_template_string(html, **context)

@etf_research_bp.route('/etf-research/holdings', methods=['GET'])
def etf_holdings():
    ticker = request.args.get('ticker', '').upper()
    data = None
    error = None

    if ticker:
        response = get_api_data(ETF_HOLDINGS_API_URL.format(ticker=ticker))
        print(f"ETF Holdings API Response for {ticker}: {response}")
        if "error" in response:
            error = response["error"]
        else:
            data = response.get("data", [])
            if not isinstance(data, list):
                error = f"Unexpected API response format: data is not a list, got {type(data)}"
                data = None

    etf_info = None
    etf_info_error = None
    if ticker:
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        print(f"ETF Info API Response for {ticker}: {etf_info_response}")
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", {})

    context = {
        'ticker': ticker,
        'error': error,
        'data': data,
        'etf_info': etf_info,
        'etf_info_error': etf_info_error,
        'MENU_BAR': MENU_BAR
    }

    html = """
    <h1>ETF-Research - Holdings</h1>
    {{ MENU_BAR | safe }}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {{ ticker }}</h2>
            {% if etf_info_error %}<p style="color: red;">Error fetching ETF Info: {{ etf_info_error }}</p>{% endif %}
            <table border='1' {% if not etf_info %}style="display: none;"{% endif %} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info:
        for key, value in etf_info.items():
            if value is not None:
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{{{{ etf_info['{key}'] }}}}</td></tr>"
    html += """
            </table>
        </div>
        <div style="flex: 2; min-width: 300px;">
            <form method="GET">
                <label>Enter ETF Ticker (e.g., SPY, QQQ): </label>
                <input type="text" name="ticker" value="{{ ticker }}" placeholder="Enter ETF ticker symbol">
                <button type="submit">Search</button>
            </form>
            <h3>Or Click a Predefined ETF:</h3>
            <div>
                <button onclick="window.location.href='/etf-research/holdings?ticker=SPY'">SPY</button>
                <button onclick="window.location.href='/etf-research/holdings?ticker=QQQ'">QQQ</button>
                <button onclick="window.location.href='/etf-research/holdings?ticker=IWM'">IWM</button>
                <button onclick="window.location.href='/etf-research/holdings?ticker=XLF'">XLF</button>
            </div>
            {% if error %}<p style="color: red;">Error: {{ error }}</p>{% endif %}
            {% if not error and not data %}<p>No data available for ticker {{ ticker }}</p>{% endif %}
            <table border='1' {% if not data %}style="display: none;"{% endif %} id="holdingsTable">
                <tr>
                    <th>Ticker</th>
                    <th>Name</th>
                    <th>Shares</th>
                    <th>Weight (%)</th>
                    <th>Market Value</th>
                </tr>
    """
    if data:
        for item in data:
            ticker_val = item.get('ticker', 'N/A')
            name = item.get('name', 'N/A')
            shares = item.get('shares', 'N/A')
            weight = item.get('weight', 'N/A')
            market_value = item.get('market_value', 'N/A')
            # Preprocess weight to ensure it's either a formatted string or 'N/A'
            weight_display = 'N/A'
            if weight != 'N/A':
                try:
                    weight_display = f"{float(weight):.2f}%"
                except (ValueError, TypeError):
                    weight_display = 'N/A'
            try:
                shares = str(shares) if shares and shares != 'N/A' else 'N/A'
            except (ValueError, TypeError):
                shares = 'N/A'
            html += f"""
            <tr>
                <td>{ticker_val}</td>
                <td>{name}</td>
                <td>{shares}</td>
                <td>{weight_display}</td>
                <td>{market_value}</td>
            </tr>
            """
    html += """
            </table>
        </div>
    </div>
    """
    return render_template_string(html, **context)

@etf_research_bp.route('/etf-research/in-outflow', methods=['GET'])
def etf_in_outflow():
    ticker = request.args.get('ticker', '').upper()
    data = None
    error = None

    if ticker:
        response = get_api_data(ETF_INOUTFLOW_API_URL.format(ticker=ticker))
        print(f"ETF In-Out Flow API Response for {ticker}: {response}")
        if "error" in response:
            error = response["error"]
        else:
            data = response.get("data", [])
            if not isinstance(data, list):
                error = f"Unexpected API response format: data is not a list, got {type(data)}"
                data = None
            else:
                if data:
                    print(f"First data item structure for {ticker}: {data[0]}")

    etf_info = None
    etf_info_error = None
    if ticker:
        etf_info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
        print(f"ETF Info API Response for {ticker}: {etf_info_response}")
        if "error" in etf_info_response:
            etf_info_error = etf_info_response["error"]
        else:
            etf_info = etf_info_response.get("data", {})

    context = {
        'ticker': ticker,
        'error': error,
        'data': data,
        'etf_info': etf_info,
        'etf_info_error': etf_info_error,
        'MENU_BAR': MENU_BAR
    }

    html = """
    <h1>ETF-Research - In-Out Flow</h1>
    {{ MENU_BAR | safe }}
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-bottom: 20px;">
            <h2>ETF Info for {{ ticker }}</h2>
            {% if etf_info_error %}<p style="color: red;">Error fetching ETF Info: {{ etf_info_error }}</p>{% endif %}
            <table border='1' {% if not etf_info %}style="display: none;"{% endif %} id="etfInfoTable">
                <tr><th>Field</th><th>Value</th></tr>
    """
    if etf_info:
        for key, value in etf_info.items():
            if value is not None:
                html += f"<tr><td>{key.replace('_', ' ').title()}</td><td>{{{{ etf_info['{key}'] }}}}</td></tr>"
    html += """
            </table>
        </div>
        <div style="flex: 2; min-width: 300px;">
            <form method="GET">
                <label>Enter ETF Ticker (e.g., SPY, QQQ): </label>
                <input type="text" name="ticker" value="{{ ticker }}" placeholder="Enter ETF ticker symbol">
                <button type="submit">Search</button>
            </form>
            <h3>Or Click a Predefined ETF:</h3>
            <div>
                <button onclick="window.location.href='/etf-research/in-outflow?ticker=SPY'">SPY</button>
                <button onclick="window.location.href='/etf-research/in-outflow?ticker=QQQ'">QQQ</button>
                <button onclick="window.location.href='/etf-research/in-outflow?ticker=IWM'">IWM</button>
                <button onclick="window.location.href='/etf-research/in-outflow?ticker=XLF'">XLF</button>
            </div>
            {% if error %}<p style="color: red;">Error: {{ error }}</p>{% endif %}
            {% if not error and not data %}<p>No data available for ticker {{ ticker }}</p>{% endif %}
            <table border='1' {% if not data %}style="display: none;"{% endif %} id="inOutflowTable">
                <tr>
                    <th>Date</th>
                    <th>Inflow</th>
                    <th>Outflow</th>
                    <th>Net Flow</th>
                </tr>
    """
    if data:
        for item in data:
            date = item.get('date', 'N/A')
            inflow = item.get('inflow', 'N/A')
            outflow = item.get('outflow', 'N/A')
            net_flow = item.get('net_flow', 'N/A')
            try:
                if inflow != 'N/A':
                    inflow = f"{float(inflow):,.2f}"
                if outflow != 'N/A':
                    outflow = f"{float(outflow):,.2f}"
                if net_flow != 'N/A':
                    net_flow = f"{float(net_flow):,.2f}"
            except (ValueError, TypeError):
                pass
            html += f"""
            <tr>
                <td>{date}</td>
                <td>{inflow}</td>
                <td>{outflow}</td>
                <td>{net_flow}</td>
            </tr>
            """
    html += """
            </table>
        </div>
    </div>
    """
    return render_template_string(html, **context)
