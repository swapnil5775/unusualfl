from flask import Blueprint, render_template_string, request, jsonify
from common import get_api_data, MENU_BAR, CONGRESS_TRADES_API_URL, MOCK_TICKERS
import logging
from datetime import datetime, timedelta
import random
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

congress_trades_bp = Blueprint('congress_trades', __name__, url_prefix='/')

def generate_mock_congress_trades():
    trades = []
    today = datetime.now()
    member_types = ['house', 'senate']
    txn_types = ['Buy', 'Sell']
    amount_ranges = [
        '$1,000 - $15,000',
        '$15,001 - $50,000',
        '$50,001 - $100,000',
        '$100,001 - $250,000',
        '$250,001 - $500,000'
    ]
    
    for i in range(20):  # Increased to 20 trades for better visualization
        date = today - timedelta(days=random.randint(1, 30))
        ticker = random.choice(MOCK_TICKERS)
        trades.append({
            'amounts': random.choice(amount_ranges),
            'filed_at_date': date.strftime('%Y-%m-%d'),
            'issuer': random.choice(['joint', 'not-disclosed', 'self']),
            'member_type': random.choice(member_types),
            'notes': f'Transaction details for {ticker}',
            'reporter': f'Congress Member {i+1}',
            'ticker': ticker,
            'transaction_date': (date - timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d'),
            'txn_type': random.choice(txn_types)
        })
    
    return trades

def get_congress_trades():
    try:
        response = get_api_data(CONGRESS_TRADES_API_URL)
        
        if not response or isinstance(response, dict) and 'error' in response:
            logger.info("Using mock data for congress trades")
            return generate_mock_congress_trades()
            
        if isinstance(response, dict) and 'data' in response:
            return response['data']
            
        logger.error(f"Invalid response from congress trades API: {response}")
        return generate_mock_congress_trades()
        
    except Exception as e:
        logger.error(f"Error fetching congress trades data: {str(e)}")
        return generate_mock_congress_trades()

def calculate_analytics(trades_data):
    total_buys = sum(1 for trade in trades_data if trade['txn_type'] == 'Buy')
    total_sells = sum(1 for trade in trades_data if trade['txn_type'] == 'Sell')
    
    # Calculate trade distribution by member type
    house_trades = sum(1 for trade in trades_data if trade['member_type'] == 'house')
    senate_trades = sum(1 for trade in trades_data if trade['member_type'] == 'senate')
    
    # Get most traded tickers
    ticker_counts = {}
    for trade in trades_data:
        ticker_counts[trade['ticker']] = ticker_counts.get(trade['ticker'], 0) + 1
    most_traded = sorted(ticker_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'total_trades': len(trades_data),
        'total_buys': total_buys,
        'total_sells': total_sells,
        'house_trades': house_trades,
        'senate_trades': senate_trades,
        'most_traded': most_traded
    }

@congress_trades_bp.route('/congress-trades')
def congress_trades():
    trades_data = get_congress_trades()
    
    if not trades_data:
        trades_data = generate_mock_congress_trades()
    
    analytics = calculate_analytics(trades_data)
    
    # Prepare data for charts in JSON format to avoid Jinja2 syntax issues
    chart_data = {
        'memberTypes': {
            'labels': ['House', 'Senate'],
            'data': [analytics['house_trades'], analytics['senate_trades']]
        },
        'mostTraded': {
            'labels': [item[0] for item in analytics['most_traded']],
            'data': [item[1] for item in analytics['most_traded']]
        }
    }
    
    html = """
    {{ style }}
    <div class="container">
        <h1>Congress Trading Activity</h1>
        """ + MENU_BAR + """
        
        <div class="dashboard">
            <!-- Analytics Cards -->
            <div class="analytics-row">
                <div class="analytics-card">
                    <div class="analytics-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="analytics-content">
                        <h3>Total Trades</h3>
                        <p class="analytics-value">{{ analytics.total_trades }}</p>
                    </div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-icon buy">
                        <i class="fas fa-arrow-up"></i>
                    </div>
                    <div class="analytics-content">
                        <h3>Buy Orders</h3>
                        <p class="analytics-value">{{ analytics.total_buys }}</p>
                    </div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-icon sell">
                        <i class="fas fa-arrow-down"></i>
                    </div>
                    <div class="analytics-content">
                        <h3>Sell Orders</h3>
                        <p class="analytics-value">{{ analytics.total_sells }}</p>
                    </div>
                </div>
            </div>

            <!-- Distribution Charts -->
            <div class="charts-row">
                <div class="chart-card">
                    <h3>Trade Distribution</h3>
                    <canvas id="memberTypeChart"></canvas>
                </div>
                <div class="chart-card">
                    <h3>Most Traded Stocks</h3>
                    <canvas id="topTickersChart"></canvas>
                </div>
            </div>

            <!-- Filters and Search -->
            <div class="controls-section">
                <div class="search-box">
                    <i class="fas fa-search"></i>
                    <input type="text" id="searchInput" placeholder="Search by ticker or member..." onkeyup="filterTrades()">
                </div>
                <div class="filters">
                    <select id="memberType" onchange="filterTrades()">
                        <option value="all">All Members</option>
                        <option value="house">House</option>
                        <option value="senate">Senate</option>
                    </select>
                    <select id="transactionType" onchange="filterTrades()">
                        <option value="all">All Transactions</option>
                        <option value="Buy">Buys</option>
                        <option value="Sell">Sells</option>
                    </select>
                    <select id="dateRange" onchange="filterTrades()">
                        <option value="all">All Time</option>
                        <option value="7">Last 7 Days</option>
                        <option value="30">Last 30 Days</option>
                    </select>
                </div>
            </div>
            
            <!-- Data Table -->
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th onclick="sortTable('filed_at_date')">Date Filed <i class="fas fa-sort"></i></th>
                            <th onclick="sortTable('transaction_date')">Transaction Date <i class="fas fa-sort"></i></th>
                            <th onclick="sortTable('member_type')">Member Type <i class="fas fa-sort"></i></th>
                            <th onclick="sortTable('reporter')">Reporter <i class="fas fa-sort"></i></th>
                            <th onclick="sortTable('ticker')">Ticker <i class="fas fa-sort"></i></th>
                            <th onclick="sortTable('txn_type')">Transaction <i class="fas fa-sort"></i></th>
                            <th onclick="sortTable('amounts')">Amount <i class="fas fa-sort"></i></th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody id="tradesTableBody">
                        {% for item in trades_data %}
                        <tr class="trade-row" 
                            data-member-type="{{ item['member_type'] }}"
                            data-txn-type="{{ item['txn_type'] }}"
                            data-date="{{ item['filed_at_date'] }}">
                            <td>{{ item['filed_at_date'] }}</td>
                            <td>{{ item['transaction_date'] }}</td>
                            <td>{{ item['member_type'].title() }}</td>
                            <td>{{ item['reporter'] }}</td>
                            <td class="ticker-cell">{{ item['ticker'] }}</td>
                            <td class="{{ 'positive' if item['txn_type'] == 'Buy' else 'negative' }}">
                                <i class="fas fa-{{ 'arrow-up' if item['txn_type'] == 'Buy' else 'arrow-down' }}"></i>
                                {{ item['txn_type'] }}
                            </td>
                            <td>{{ item['amounts'] }}</td>
                            <td class="notes">{{ item['notes'] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <style>
        .dashboard {
            padding: 20px;
            background: var(--background);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .analytics-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .analytics-card {
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            display: flex;
            align-items: center;
            transition: transform 0.2s;
        }

        .analytics-card:hover {
            transform: translateY(-5px);
        }

        .analytics-icon {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--primary-color);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
        }

        .analytics-icon i {
            color: white;
            font-size: 1.5rem;
        }

        .analytics-icon.buy {
            background: #28a745;
        }

        .analytics-icon.sell {
            background: #dc3545;
        }

        .analytics-content h3 {
            margin: 0;
            font-size: 0.9rem;
            color: var(--text);
            opacity: 0.8;
        }

        .analytics-value {
            margin: 5px 0 0;
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text);
        }

        .charts-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .chart-card {
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
        }

        .chart-card h3 {
            margin: 0 0 20px;
            color: var(--text);
            font-size: 1.1rem;
        }

        .controls-section {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 30px;
            align-items: center;
        }

        .search-box {
            flex: 1;
            min-width: 300px;
            position: relative;
        }

        .search-box i {
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text);
            opacity: 0.5;
        }

        .search-box input {
            width: 100%;
            padding: 12px 12px 12px 40px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--background);
            color: var(--text);
            font-size: 1rem;
        }

        .filters {
            display: flex;
            gap: 10px;
        }

        .filters select {
            padding: 10px 15px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--background);
            color: var(--text);
            font-size: 0.9rem;
            cursor: pointer;
        }

        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 0;
        }

        th {
            background: var(--primary-color);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.5px;
            padding: 15px;
            position: sticky;
            top: 0;
            cursor: pointer;
            transition: background-color 0.2s;
        }

        th:hover {
            background: var(--secondary-color);
        }

        th i {
            margin-left: 5px;
            font-size: 0.8rem;
        }

        td {
            padding: 15px;
            border-bottom: 1px solid var(--border);
            color: var(--text);
        }

        .ticker-cell {
            font-weight: 600;
            color: var(--primary-color);
        }

        tr:hover {
            background: var(--hover);
        }

        .positive {
            color: #28a745;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .negative {
            color: #dc3545;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .notes {
            max-width: 300px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--text);
            opacity: 0.8;
        }

        @media (max-width: 768px) {
            .analytics-row {
                grid-template-columns: 1fr;
            }

            .charts-row {
                grid-template-columns: 1fr;
            }

            .controls-section {
                flex-direction: column;
            }

            .filters {
                flex-direction: column;
                width: 100%;
            }

            .notes {
                max-width: 200px;
            }
        }
    </style>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Chart data from backend
        const chartData = {{ chart_data|tojson }};
        
        // Initialize charts
        document.addEventListener('DOMContentLoaded', function() {
            // Member Type Distribution Chart
            const memberTypeCtx = document.getElementById('memberTypeChart').getContext('2d');
            new Chart(memberTypeCtx, {
                type: 'doughnut',
                data: {
                    labels: chartData.memberTypes.labels,
                    datasets: [{
                        data: chartData.memberTypes.data,
                        backgroundColor: ['#6c5ce7', '#a55eea']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: getComputedStyle(document.body).getPropertyValue('--text')
                            }
                        }
                    }
                }
            });

            // Top Tickers Chart
            const topTickersCtx = document.getElementById('topTickersChart').getContext('2d');
            new Chart(topTickersCtx, {
                type: 'bar',
                data: {
                    labels: chartData.mostTraded.labels,
                    datasets: [{
                        label: 'Number of Trades',
                        data: chartData.mostTraded.data,
                        backgroundColor: '#6c5ce7'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                color: getComputedStyle(document.body).getPropertyValue('--text')
                            },
                            grid: {
                                color: getComputedStyle(document.body).getPropertyValue('--border')
                            }
                        },
                        x: {
                            ticks: {
                                color: getComputedStyle(document.body).getPropertyValue('--text')
                            },
                            grid: {
                                color: getComputedStyle(document.body).getPropertyValue('--border')
                            }
                        }
                    }
                }
            });
        });

        let currentSort = { column: null, direction: 'asc' };

        function filterTrades() {
            const searchText = document.getElementById('searchInput').value.toLowerCase();
            const memberType = document.getElementById('memberType').value;
            const transactionType = document.getElementById('transactionType').value;
            const dateRange = document.getElementById('dateRange').value;
            const rows = document.querySelectorAll('.trade-row');
            
            const today = new Date();
            const cutoffDate = new Date();
            cutoffDate.setDate(today.getDate() - (dateRange === 'all' ? 365 : parseInt(dateRange)));
            
            rows.forEach(row => {
                const rowMemberType = row.getAttribute('data-member-type');
                const rowTxnType = row.getAttribute('data-txn-type');
                const rowDate = new Date(row.getAttribute('data-date'));
                const rowText = row.textContent.toLowerCase();
                
                const matchesSearch = searchText === '' || rowText.includes(searchText);
                const matchesMemberType = memberType === 'all' || memberType === rowMemberType;
                const matchesTxnType = transactionType === 'all' || transactionType === rowTxnType;
                const matchesDate = dateRange === 'all' || rowDate >= cutoffDate;
                
                row.style.display = (matchesSearch && matchesMemberType && matchesTxnType && matchesDate) ? '' : 'none';
            });
        }

        function sortTable(column) {
            const tbody = document.getElementById('tradesTableBody');
            const rows = Array.from(tbody.getElementsByTagName('tr'));
            
            // Update sort direction
            if (currentSort.column === column) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.column = column;
                currentSort.direction = 'asc';
            }
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.children[getColumnIndex(column)].textContent;
                const bValue = b.children[getColumnIndex(column)].textContent;
                
                if (column === 'filed_at_date' || column === 'transaction_date') {
                    return compareDates(aValue, bValue);
                }
                
                return aValue.localeCompare(bValue);
            });
            
            if (currentSort.direction === 'desc') {
                rows.reverse();
            }
            
            // Reorder rows in the table
            rows.forEach(row => tbody.appendChild(row));
            
            // Update sort icons
            updateSortIcons(column);
        }

        function getColumnIndex(column) {
            const columns = {
                'filed_at_date': 0,
                'transaction_date': 1,
                'member_type': 2,
                'reporter': 3,
                'ticker': 4,
                'txn_type': 5,
                'amounts': 6
            };
            return columns[column];
        }

        function compareDates(a, b) {
            return new Date(a) - new Date(b);
        }

        function updateSortIcons(activeColumn) {
            const headers = document.querySelectorAll('th');
            headers.forEach(header => {
                const icon = header.querySelector('i');
                if (icon) {
                    if (header.textContent.toLowerCase().includes(activeColumn)) {
                        icon.className = `fas fa-sort-${currentSort.direction === 'asc' ? 'up' : 'down'}`;
                    } else {
                        icon.className = 'fas fa-sort';
                    }
                }
            });
        }
    </script>
    """
    
    return render_template_string(html, trades_data=trades_data, analytics=analytics, chart_data=chart_data) 