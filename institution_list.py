from flask import Blueprint, render_template_string, request
from common import get_api_data, get_live_stock_price, MENU_BAR, INST_LIST_API_URL, INST_HOLDINGS_API_URL

institution_bp = Blueprint('institution', __name__, url_prefix='/')

@institution_bp.route('/')
def home():
    html = """
    {{ style }}
    <div class="container">
        <h1>Welcome to FinanceHub</h1>
        """ + MENU_BAR + """
        
        <div class="welcome-message">
            <p>Explore financial data, market trends, and investment insights with our comprehensive tools.</p>
        </div>
        
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-building"></i></div>
                <h3>Institutions</h3>
                <p>Track institutional investors and their holdings</p>
                <a href="/institution-list" class="feature-link">View Institutions</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-search"></i></div>
                <h3>Stock Research</h3>
                <p>Analyze individual stocks and their performance</p>
                <a href="/research" class="feature-link">Research Stocks</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-calendar-alt"></i></div>
                <h3>Seasonality</h3>
                <p>Discover seasonal patterns in market performance</p>
                <a href="/seasonality" class="feature-link">View Seasonality</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-chart-pie"></i></div>
                <h3>ETF Research</h3>
                <p>Explore ETFs and their composition</p>
                <a href="/etf-research" class="feature-link">Research ETFs</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-water"></i></div>
                <h3>Market Tide</h3>
                <p>Visualize money flow across market sectors</p>
                <a href="/market-tide" class="feature-link">View Market Tide</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-bolt"></i></div>
                <h3>Market Spike</h3>
                <p>Track market volatility and spike events</p>
                <a href="/market-spike" class="feature-link">View Market Spike</a>
            </div>
            
            <div class="feature-card">
                <div class="feature-icon"><i class="fas fa-exchange-alt"></i></div>
                <h3>Flow Per Strike</h3>
                <p>Analyze options flow data by strike price</p>
                <a href="/flow-per-strike" class="feature-link">View Flow Data</a>
            </div>
        </div>
    </div>
    
    <style>
        .welcome-message {
            text-align: center;
            margin-bottom: 2rem;
            font-size: 1.1rem;
            color: var(--text);
        }
        
        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-top: 2rem;
        }
        
        .feature-card {
            background-color: var(--background);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .feature-icon {
            font-size: 2rem;
            color: var(--primary-color);
            margin-bottom: 1rem;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: rgba(var(--primary-rgb), 0.1);
            border-radius: 50%;
        }
        
        .feature-card h3 {
            margin: 0 0 0.5rem 0;
            color: var(--text);
        }
        
        .feature-card p {
            margin: 0 0 1.5rem 0;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .feature-link {
            color: var(--primary-color);
            text-decoration: none;
            font-weight: bold;
            padding: 0.5rem 1rem;
            border: 1px solid var(--primary-color);
            border-radius: 20px;
            transition: all 0.2s;
            margin-top: auto;
        }
        
        .feature-link:hover {
            background-color: var(--primary-color);
            color: white;
        }
        
        @media (max-width: 768px) {
            .features-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """
    
    return render_template_string(html)

@institution_bp.route('/institution-list')
def institution_list():
    data = get_api_data(INST_LIST_API_URL)
    
    # Process data to ensure it's in the correct format
    processed_data = {"data": []}
    if "data" in data and isinstance(data["data"], list):
        processed_data["data"] = []
        for inst in data["data"]:
            if isinstance(inst, str):
                processed_data["data"].append({"name": inst, "is_string": True})
            elif isinstance(inst, dict) and "name" in inst:
                inst["is_string"] = False
                processed_data["data"].append(inst)
            else:
                processed_data["data"].append({"name": "Unknown", "is_string": True})
    
    html = """
    {{ style }}
    <div class="container">
        <h1>Institution List</h1>
        """ + MENU_BAR + """
        
        <div class="card">
            <h2><i class="fas fa-building"></i> Financial Institutions</h2>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="institutionsTable">
                        {% if "error" not in data %}
                            {% for inst in data.get("data", []) %}
                                <tr>
                                    <td>{{ inst.name }}</td>
                                    <td>
                                        <button class="btn-sm" onclick="showHoldings('{{ inst.name }}')">
                                            <i class="fas fa-list"></i> Holdings
                                        </button>
                                        <button class="btn-sm" onclick="showPieChart('{{ inst.name }}')">
                                            <i class="fas fa-chart-pie"></i> Chart
                                        </button>
                                    </td>
                                </tr>
                            {% endfor %}
                        {% else %}
                            <tr>
                                <td colspan="2">Error: {{ data.get('error', 'Unknown error') }}</td>
                            </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div id="holdingsContainer" class="card" style="display: none;">
            <div class="card-header">
                <h2 id="holdingsTitle">Holdings</h2>
                <button class="btn-close" onclick="closeHoldings()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="table-responsive">
                <table id="holdingsTable">
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Units</th>
                            <th>Value</th>
                            <th>Live Price</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
        
        <div id="pieChartContainer" class="card" style="display: none;">
            <div class="card-header">
                <h2 id="pieChartTitle">Holdings Distribution</h2>
                <button class="btn-close" onclick="closePieChart()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="chart-wrapper">
                <canvas id="holdingsPieChart"></canvas>
            </div>
        </div>
    </div>
    
    <style>
        .table-responsive {
            overflow-x: auto;
        }
        
        .btn-sm {
            padding: 0.25rem 0.5rem;
            font-size: 0.875rem;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 0.5rem;
            transition: background-color 0.2s ease;
        }
        
        .btn-sm:hover {
            background-color: var(--secondary-color);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .btn-close {
            background: none;
            border: none;
            color: var(--text);
            font-size: 1.25rem;
            cursor: pointer;
            padding: 0.25rem;
            transition: color 0.2s ease;
        }
        
        .btn-close:hover {
            color: var(--primary-color);
        }
        
        .chart-wrapper {
            padding: 1rem;
            border-radius: 8px;
            background: var(--background);
            border: 1px solid var(--border);
        }
    </style>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        let pieChart;
        
        function showHoldings(name) {
            fetch(`/institution/holdings?name=${encodeURIComponent(name)}`)
                .then(response => response.json())
                .then(data => {
                    let tableBody = '';
                    if (data.data) {
                        data.data.forEach(holding => {
                            const ticker = holding.ticker || 'N/A';
                            const units = holding.units || 'N/A';
                            const value = holding.value || 'N/A';
                            
                            tableBody += `
                                <tr>
                                    <td>${ticker}</td>
                                    <td>${units}</td>
                                    <td>${value}</td>
                                    <td>${ticker !== 'N/A' ? '${ticker}' : 'N/A'}</td>
                                </tr>
                            `.replace('${ticker}', ticker !== 'N/A' ? ticker : 'N/A');
                        });
                    }
                    
                    document.getElementById('holdingsTitle').textContent = `Holdings for ${name}`;
                    document.getElementById('holdingsTable').querySelector('tbody').innerHTML = tableBody;
                    document.getElementById('holdingsContainer').style.display = 'block';
                    document.getElementById('pieChartContainer').style.display = 'none';
                })
                .catch(error => console.error('Error:', error));
        }
        
        function closeHoldings() {
            document.getElementById('holdingsContainer').style.display = 'none';
        }
        
        function showPieChart(name) {
            fetch(`/institution/holdings?name=${encodeURIComponent(name)}`)
                .then(response => response.json())
                .then(data => {
                    const labels = [];
                    const values = [];
                    
                    if (data.data) {
                        data.data.forEach(holding => {
                            if (holding.ticker) {
                                labels.push(holding.ticker);
                                values.push(parseFloat(holding.units || 0));
                            }
                        });
                    }
                    
                    if (pieChart) pieChart.destroy();
                    
                    const ctx = document.getElementById('holdingsPieChart').getContext('2d');
                    pieChart = new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: labels,
                            datasets: [{
                                data: values,
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
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: {
                                title: {
                                    display: true,
                                    text: `Holdings Distribution for ${name}`,
                                    color: 'var(--text)'
                                },
                                legend: {
                                    position: 'right',
                                    labels: {
                                        color: 'var(--text)'
                                    }
                                }
                            }
                        }
                    });
                    
                    document.getElementById('pieChartTitle').textContent = `Holdings Distribution for ${name}`;
                    document.getElementById('pieChartContainer').style.display = 'block';
                    document.getElementById('holdingsContainer').style.display = 'none';
                })
                .catch(error => console.error('Error:', error));
        }
        
        function closePieChart() {
            document.getElementById('pieChartContainer').style.display = 'none';
            if (pieChart) pieChart.destroy();
        }
    </script>
    """
    return render_template_string(html, data=processed_data)

@institution_bp.route('/institution/list')
def institution_list_alt():
    return institution_list()

@institution_bp.route('/institution/holdings')
def get_institution_holdings():
    from flask import jsonify
    name = request.args.get('name')
    data = get_api_data(INST_HOLDINGS_API_URL.format(name=name))
    return jsonify(data)
