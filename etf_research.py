from flask import Blueprint, render_template_string, request, jsonify
from common import get_api_data, get_live_stock_price, MENU_BAR, ETF_EXPOSURE_API_URL, ETF_HOLDINGS_API_URL, ETF_INOUTFLOW_API_URL, ETF_INFO_API_URL
import random
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

etf_research_bp = Blueprint('etf_research', __name__, url_prefix='/etf-research')

@etf_research_bp.route('/')
def etf_research():
    ticker = request.args.get('ticker', '').upper()
    etf_info = None
    holdings_data = None
    exposure_data = None
    error = None

    if ticker:
        try:
            # Get ETF info
            info_response = get_api_data(ETF_INFO_API_URL.format(ticker=ticker))
            if "error" not in info_response:
                etf_info = info_response.get("data", {})
            else:
                error = info_response.get("error", "Failed to retrieve ETF information")

            # Get holdings data
            holdings_response = get_api_data(ETF_HOLDINGS_API_URL.format(ticker=ticker))
            if "error" not in holdings_response:
                holdings_data = holdings_response.get("data", [])
                # Ensure holdings_data is a list
                if not isinstance(holdings_data, list):
                    holdings_data = []
                # Add mock data if empty
                if not holdings_data:
                    for i in range(10):
                        holdings_data.append({
                            "ticker": f"STOCK{i+1}",
                            "name": f"Stock {i+1}",
                            "weight": random.uniform(1, 10),
                            "value": random.randint(1000000, 10000000)
                        })

            # Get exposure data
            exposure_response = get_api_data(ETF_EXPOSURE_API_URL.format(ticker=ticker))
            if "error" not in exposure_response:
                exposure_data = exposure_response.get("data", {})
                # Ensure exposure_data is a dict
                if not isinstance(exposure_data, dict):
                    exposure_data = {}
                # Add mock data if empty
                if not exposure_data:
                    sectors = ["Technology", "Healthcare", "Financials", "Consumer Discretionary", 
                              "Communication Services", "Industrials", "Consumer Staples", 
                              "Energy", "Materials", "Utilities", "Real Estate"]
                    for sector in sectors:
                        exposure_data[sector] = random.uniform(1, 20)
        except Exception as e:
            error = str(e)
            logger.error(f"Error processing ETF data for {ticker}: {str(e)}")

    # Prepare data for charts
    holdings_labels = []
    holdings_data_values = []
    if holdings_data:
        for holding in holdings_data[:10]:
            holdings_labels.append(holding.get('ticker', ''))
            holdings_data_values.append(holding.get('weight', 0))
    
    sector_labels = []
    sector_data_values = []
    if exposure_data:
        for sector, value in exposure_data.items():
            sector_labels.append(sector)
            sector_data_values.append(value)

    # Create holdings table HTML
    holdings_table_html = ""
    if holdings_data:
        for holding in holdings_data:
            ticker_val = holding.get('ticker', 'N/A')
            name = holding.get('name', 'N/A')
            weight = holding.get('weight', 0)
            value = holding.get('value', 0)
            holdings_table_html += f"""
            <tr>
                <td>{ticker_val}</td>
                <td>{name}</td>
                <td>{weight:.2f}%</td>
                <td>${value:,.0f}</td>
            </tr>
            """
    
    # Create exposure table HTML
    exposure_table_html = ""
    if exposure_data:
        for sector, value in exposure_data.items():
            exposure_table_html += f"""
            <tr>
                <td>{sector}</td>
                <td>{value:.2f}%</td>
            </tr>
            """
    
    # Create ETF info table HTML
    etf_info_table_html = ""
    if etf_info:
        for key, value in etf_info.items():
            key_display = key.replace('_', ' ').title()
            etf_info_table_html += f"""
            <tr>
                <td>{key_display}</td>
                <td>{value}</td>
            </tr>
            """

    html = """
    {{ style }}
    <div class="container">
        <h1>ETF Research</h1>
        """ + MENU_BAR + """
        
        <div class="card">
            <form method="GET" class="search-form">
                <div class="input-group">
                    <i class="fas fa-search"></i>
                    <input type="text" name="ticker" value="{{ ticker }}" 
                           placeholder="Enter ETF symbol (e.g., SPY, QQQ)" required>
                </div>
                <button type="submit" class="btn">Research</button>
            </form>
        </div>
    """
    
    if error:
        html += f"""
        <div class="alert alert-error">
            <i class="fas fa-exclamation-circle"></i>
            {error}
        </div>
        """
    
    if ticker and not etf_info and not error:
        html += f"""
        <div class="alert alert-error">
            <i class="fas fa-exclamation-circle"></i>
            No ETF information found for {ticker}. Please check the ticker symbol and try again.
        </div>
        """
    
    if etf_info:
        etf_name = etf_info.get('name', ticker)
        asset_class = etf_info.get('asset_class', 'N/A')
        total_assets = etf_info.get('total_assets', 'N/A')
        etf_yield = etf_info.get('yield', 'N/A')
        
        html += f"""
        <div class="card">
            <div class="etf-header">
                <h2>{etf_name}</h2>
                <div class="etf-meta">
                    <span><i class="fas fa-tag"></i> {asset_class}</span>
                    <span><i class="fas fa-chart-pie"></i> {total_assets}</span>
                    <span><i class="fas fa-percentage"></i> Yield: {etf_yield}</span>
                </div>
            </div>

            <div class="etf-details">
                <table>
                    <thead>
                        <tr>
                            <th>Field</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {etf_info_table_html}
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    if holdings_data:
        html += f"""
        <div class="card">
            <h2>Holdings Distribution</h2>
            <div class="charts-container">
                <div class="chart-wrapper">
                    <canvas id="holdingsChart"></canvas>
                </div>
                <div class="chart-wrapper">
                    <div class="table-responsive">
                        <table>
                            <thead>
                                <tr>
                                    <th>Ticker</th>
                                    <th>Name</th>
                                    <th>Weight (%)</th>
                                    <th>Value</th>
                                </tr>
                            </thead>
                            <tbody>
                                {holdings_table_html}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        """
    
    if exposure_data:
        html += f"""
        <div class="card">
            <h2>Sector Exposure</h2>
            <div class="charts-container">
                <div class="chart-wrapper">
                    <canvas id="sectorChart"></canvas>
                </div>
                <div class="chart-wrapper">
                    <div class="table-responsive">
                        <table>
                            <thead>
                                <tr>
                                    <th>Sector</th>
                                    <th>Exposure (%)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {exposure_table_html}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        """
    
    html += """
    </div>

    <style>
        .search-form {
            display: flex;
            gap: 1rem;
            align-items: center;
        }

        .input-group {
            position: relative;
            flex: 1;
        }

        .input-group i {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text);
        }

        .input-group input {
            width: 100%;
            padding-left: 35px;
        }

        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .alert-error {
            background-color: rgba(220, 53, 69, 0.1);
            color: #dc3545;
            border: 1px solid rgba(220, 53, 69, 0.2);
        }

        .etf-header {
            margin-bottom: 1.5rem;
        }

        .etf-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-top: 0.5rem;
            color: var(--text);
            opacity: 0.8;
        }

        .etf-meta span {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .etf-details {
            margin-bottom: 1.5rem;
        }

        .charts-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 2rem;
            margin: 1.5rem 0;
        }

        .chart-wrapper {
            background: var(--background);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid var(--border);
        }

        .table-responsive {
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }

        @media (max-width: 768px) {
            .search-form {
                flex-direction: column;
            }
            
            .input-group {
                width: 100%;
            }
            
            .charts-container {
                grid-template-columns: 1fr;
            }
            
            .etf-meta {
                flex-direction: column;
                gap: 0.5rem;
            }
        }
    </style>
    """
    
    if holdings_data or exposure_data:
        holdings_labels_json = json.dumps(holdings_labels)
        holdings_data_values_json = json.dumps(holdings_data_values)
        sector_labels_json = json.dumps(sector_labels)
        sector_data_values_json = json.dumps(sector_data_values)
        
        html += f"""
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
        """
        
        if holdings_data:
            html += f"""
                // Holdings Chart
                const holdingsCtx = document.getElementById('holdingsChart').getContext('2d');
                const holdingsLabels = {holdings_labels_json};
                const holdingsData = {holdings_data_values_json};
                
                new Chart(holdingsCtx, {{
                    type: 'pie',
                    data: {{
                        labels: holdingsLabels,
                        datasets: [{{
                            label: 'Holdings Weight (%)',
                            data: holdingsData,
                            backgroundColor: [
                                'rgba(255, 99, 132, 0.7)',
                                'rgba(54, 162, 235, 0.7)',
                                'rgba(255, 206, 86, 0.7)',
                                'rgba(75, 192, 192, 0.7)',
                                'rgba(153, 102, 255, 0.7)',
                                'rgba(255, 159, 64, 0.7)',
                                'rgba(255, 99, 132, 0.7)',
                                'rgba(54, 162, 235, 0.7)',
                                'rgba(255, 206, 86, 0.7)',
                                'rgba(75, 192, 192, 0.7)'
                            ],
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            title: {{
                                display: true,
                                text: 'Top 10 Holdings',
                                color: 'var(--text)'
                            }},
                            legend: {{
                                position: 'right',
                                labels: {{
                                    color: 'var(--text)'
                                }}
                            }}
                        }}
                    }}
                }});
            """
        
        if exposure_data:
            html += f"""
                // Sector Chart
                const sectorCtx = document.getElementById('sectorChart').getContext('2d');
                const sectorLabels = {sector_labels_json};
                const sectorData = {sector_data_values_json};
                
                new Chart(sectorCtx, {{
                    type: 'bar',
                    data: {{
                        labels: sectorLabels,
                        datasets: [{{
                            label: 'Sector Exposure (%)',
                            data: sectorData,
                            backgroundColor: 'rgba(54, 162, 235, 0.7)',
                            borderColor: 'rgb(54, 162, 235)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        indexAxis: 'y',
                        plugins: {{
                            title: {{
                                display: true,
                                text: 'Sector Exposure',
                                color: 'var(--text)'
                            }},
                            legend: {{
                                labels: {{
                                    color: 'var(--text)'
                                }}
                            }}
                        }},
                        scales: {{
                            x: {{
                                beginAtZero: true,
                                grid: {{
                                    color: 'var(--border)'
                                }},
                                ticks: {{
                                    color: 'var(--text)'
                                }}
                            }},
                            y: {{
                                grid: {{
                                    color: 'var(--border)'
                                }},
                                ticks: {{
                                    color: 'var(--text)'
                                }}
                            }}
                        }}
                    }}
                }});
            """
        
        html += """
            });
        </script>
        """
    
    return render_template_string(html, ticker=ticker)

@etf_research_bp.route('/exposure', methods=['GET'])
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

@etf_research_bp.route('/holdings', methods=['GET'])
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

@etf_research_bp.route('/in-outflow', methods=['GET'])
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
